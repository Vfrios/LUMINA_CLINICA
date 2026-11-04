#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LÚMINA · export_web.py
======================
Camada de exibição web: lê os .obj (em metros, com normais e Tr) gerados por
build_a.py / build_b.py e produz, SEM remodelar nada:

  dist/web/modelos/<peca>.glb          1 GLB por peça de models.REG (89 peças)
  dist/web/modelos/predio_completo.glb prédio inteiro (scene.full_scene(ceilings=True))
  dist/web/texturas/*.png              texturas originais (referência)
  dist/web/data/*.json                 câmeras (= renders 01..08), ambientes, colisão, catálogo
  dist/web/{index.html, three/, ...}   cópia de web/ + manifest/service worker/ícones PWA
  dist/verificacao_web.txt             relatório de validação dos GLB
  dist/LUMINA_WEB.zip                  projeto inteiro (zip final)

Via de conversão escolhida (a mais simples, documentada no README):
  GLB escrito em Python puro (numpy + Pillow), sem dependências novas:
  nada de trimesh / pygltflib / Blender / obj2gltf. Só usa o que o projeto já exige.

Uso:   python3 export_web.py [--vendor] [--sem-textura-piso] [--otimizar draco|meshopt] [--sem-zip]
"""
import os, sys, re, json, math, glob, shutil, struct, zipfile, hashlib, argparse, subprocess, io, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('LUMINA_OUT', RAIZ)                      # build_a.OUT = raiz do projeto
sys.path.insert(0, os.path.join(RAIZ, 'codigo_fonte'))

import lib_geom as G
import layout as L
import build_a as A
import build_b                                                  # RENDER_CAMS (câmeras dos renders)
import scene
from models import REG

OUT = A.OUT
DIST = os.path.join(OUT, 'dist')
WEB_DIST = os.path.join(DIST, 'web')
UNIT = 0.01                                                     # cm -> m

# ---------------------------------------------------------------- utilidades de cor / PBR
def srgb2lin(c):
    """Cores do MATS/MTL são hex sRGB; o glTF espera baseColorFactor LINEAR."""
    return [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c]

# (metallic, roughness) — o que não estiver aqui é fosco (0, 0.8). Cores/alpha continuam vindo de MATS/ALPHA.
PBR = {'inox': (0.70, 0.40), 'dourado': (0.55, 0.45), 'champagne': (0.45, 0.50), 'espelho': (0.80, 0.12),
       'vidro': (0.0, 0.05), 'ceramica': (0.0, 0.35), 'marmore': (0.0, 0.30), 'led': (0.0, 0.5), 'led_neutro': (0.0, 0.5),
       'preto': (0.0, 0.50), 'esquadria': (0.1, 0.50), 'teto': (0.0, 0.95)}
EMISSIVOS = {'led', 'led_neutro'}                               # materiais "luminosos"

# ---------------------------------------------------------------- escritor GLB (glTF 2.0 binário)
class GLB:
    """Montador mínimo de glTF 2.0 .glb: materiais PBR, texturas embutidas, malhas por material."""
    def __init__(s):
        s.buf = bytearray(); s.views = []; s.accs = []; s.mats = []; s._mat = {}
        s.meshes = []; s.nodes = []; s.images = []; s.texs = []; s._tex = {}
        s.samplers = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]  # repete + mipmap

    def _view(s, data, target=None):
        off = len(s.buf); s.buf += data; s.buf += b'\0' * ((4 - len(s.buf) % 4) % 4)
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target: v["target"] = target
        s.views.append(v); return len(s.views) - 1

    def _acc(s, arr, comp, typ, target, minmax=False):
        arr = np.ascontiguousarray(arr)
        a = {"bufferView": s._view(arr.tobytes(), target), "componentType": comp, "count": int(arr.shape[0]), "type": typ}
        if minmax: a["min"] = [float(x) for x in arr.min(0)]; a["max"] = [float(x) for x in arr.max(0)]
        s.accs.append(a); return len(s.accs) - 1

    def textura(s, caminho_png, qualidade=90):
        """Embute a imagem (como JPEG, bem menor que PNG para mármore/porcelanato) e devolve o índice da textura."""
        if caminho_png in s._tex: return s._tex[caminho_png]
        bio = io.BytesIO(); Image.open(caminho_png).convert('RGB').save(bio, 'JPEG', quality=qualidade, optimize=True)
        bv = s._view(bio.getvalue())
        s.images.append({"name": os.path.splitext(os.path.basename(caminho_png))[0], "bufferView": bv, "mimeType": "image/jpeg"})
        s.texs.append({"sampler": 0, "source": len(s.images) - 1})
        s._tex[caminho_png] = len(s.texs) - 1; return s._tex[caminho_png]

    def material(s, nome, kd, alpha=1.0, emis=None, metal=0.0, rough=0.8, tex=None, dupla_face=True):
        if nome in s._mat: return s._mat[nome]
        pbr = {"baseColorFactor": (srgb2lin(kd[:3]) + [alpha]) if tex is None else [1, 1, 1, alpha],
               "metallicFactor": metal, "roughnessFactor": rough}
        if tex is not None: pbr["baseColorTexture"] = {"index": tex}
        m = {"name": nome, "pbrMetallicRoughness": pbr, "doubleSided": dupla_face}
        if alpha < 1.0: m["alphaMode"] = "BLEND"                # ALPHA do MATS -> alphaMode BLEND
        if emis is not None: m["emissiveFactor"] = srgb2lin(emis[:3])
        s.mats.append(m); s._mat[nome] = len(s.mats) - 1; return s._mat[nome]

    def malha(s, nome, prims):
        """prims: lista de (idx_material, pos Nx3, nrm Nx3, uv Nx2|None, indices)."""
        P = []
        for mi, pos, nrm, uv, idx in prims:
            pos = np.asarray(pos, np.float32); nrm = np.asarray(nrm, np.float32)
            at = {"POSITION": s._acc(pos, 5126, "VEC3", 34962, True), "NORMAL": s._acc(nrm, 5126, "VEC3", 34962)}
            if uv is not None: at["TEXCOORD_0"] = s._acc(np.asarray(uv, np.float32), 5126, "VEC2", 34962)
            idx = np.asarray(idx, np.uint32 if len(pos) > 65535 else np.uint16)
            P.append({"attributes": at, "indices": s._acc(idx, 5125 if idx.dtype == np.uint32 else 5123, "SCALAR", 34963),
                      "material": mi, "mode": 4})
        s.meshes.append({"name": nome, "primitives": P}); return len(s.meshes) - 1

    def no(s, nome, malha=None, filhos=None, extras=None):
        n = {"name": nome}
        if malha is not None: n["mesh"] = malha
        if filhos: n["children"] = filhos
        if extras: n["extras"] = extras
        s.nodes.append(n); return len(s.nodes) - 1

    def salvar(s, caminho, raizes, extras=None):
        j = {"asset": {"version": "2.0", "generator": "LUMINA export_web.py (unidade: metro, y para cima)", "extras": extras or {}},
             "scene": 0, "scenes": [{"nodes": raizes}], "nodes": s.nodes, "meshes": s.meshes, "materials": s.mats,
             "accessors": s.accs, "bufferViews": s.views, "buffers": [{"byteLength": len(s.buf)}]}
        if s.images: j["images"] = s.images; j["textures"] = s.texs; j["samplers"] = s.samplers
        js = json.dumps(j, separators=(',', ':'), ensure_ascii=False).encode('utf-8'); js += b' ' * ((4 - len(js) % 4) % 4)
        bn = bytes(s.buf) + b'\0' * ((4 - len(s.buf) % 4) % 4)
        total = 12 + 8 + len(js) + 8 + len(bn)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'wb') as f:
            f.write(struct.pack('<4sII', b'glTF', 2, total))
            f.write(struct.pack('<I4s', len(js), b'JSON')); f.write(js)
            f.write(struct.pack('<I4s', len(bn), b'BIN\0')); f.write(bn)
        return total

# ---------------------------------------------------------------- leitura de OBJ / MTL (já em metros)
def ler_mtl(caminho):
    mats = {}; cur = None
    for ln in open(caminho, encoding='utf-8'):
        p = ln.split()
        if not p: continue
        if p[0] == 'newmtl': cur = mats.setdefault(p[1], {'kd': (0.7, 0.7, 0.7), 'tr': 0.0, 'ke': None})
        elif cur is not None and p[0] == 'Kd': cur['kd'] = tuple(map(float, p[1:4]))
        elif cur is not None and p[0] == 'Tr': cur['tr'] = float(p[1])
        elif cur is not None and p[0] == 'd': cur['tr'] = 1 - float(p[1])   # tolera MTL antigo
        elif cur is not None and p[0] == 'Ke': cur['ke'] = tuple(map(float, p[1:4]))
    return mats

def ler_obj(caminho):
    """Retorna {material: (pos, nrm, idx)} e o dict do MTL. Vértices únicos por par (v, vn)."""
    v = []; vn = []; faces = {}; cur = '_'; mtl = {}
    base = os.path.dirname(caminho)
    for ln in open(caminho, encoding='utf-8'):
        p = ln.split()
        if not p or p[0].startswith('#'): continue
        if p[0] == 'mtllib': mtl = ler_mtl(os.path.join(base, p[1]))
        elif p[0] == 'v': v.append(tuple(map(float, p[1:4])))
        elif p[0] == 'vn': vn.append(tuple(map(float, p[1:4])))
        elif p[0] == 'usemtl': cur = p[1]
        elif p[0] == 'f':
            ids = []
            for t in p[1:]:
                a = t.split('/'); ids.append((int(a[0]) - 1, int(a[2]) - 1 if len(a) > 2 and a[2] else -1))
            for i in range(1, len(ids) - 1): faces.setdefault(cur, []).append((ids[0], ids[i], ids[i + 1]))
    out = {}
    for m, fs in faces.items():
        mp = {}; pos = []; nrm = []; idx = []
        for tri in fs:
            for key in tri:
                if key not in mp:
                    mp[key] = len(pos); pos.append(v[key[0]]); nrm.append(vn[key[1]] if key[1] >= 0 else (0, 1, 0))
                idx.append(mp[key])
        out[m] = (np.array(pos, np.float32), np.array(nrm, np.float32), np.array(idx))
    return out, mtl

def mat_do_mtl(glb, nome, mtl):
    d = mtl.get(nome, {'kd': G.MATS.get(nome, (0.7, 0.7, 0.7)), 'tr': 0.0, 'ke': None})
    me, ru = PBR.get(nome, (0.0, 0.8))
    return glb.material(nome, d['kd'], round(1 - d['tr'], 3), d['ke'] if d['ke'] else None, me, ru)

# ---------------------------------------------------------------- 1) uma peça: OBJ web -> GLB
def peca_glb(nome, info, destino):
    obj = os.path.join(OUT, 'modelos_web', info['catdir'], nome, nome + '.obj')
    if not os.path.exists(obj): raise SystemExit(f'OBJ web ausente: {obj} (rode build_a.py antes)')
    grupos, mtl = ler_obj(obj)
    g = GLB()
    prims = [(mat_do_mtl(g, m, mtl), pos, nrm, None, idx) for m, (pos, nrm, idx) in grupos.items()]
    dims = [round(float(x), 1) for x in info['dims']] if 'dims' in info else None
    n = g.no(nome, g.malha(nome, prims), extras={"descricao": info['desc'], "categoria": info['cat'], "dimensoes_cm_LxAxP": dims})
    return g.salvar(destino, [n], {"peca": nome, "descricao": info['desc']})

# ---------------------------------------------------------------- 2) prédio completo (scene.full_scene)
FLOORTEX = {'areia': 'porcelanato_areia', 'claro': 'porcelanato_claro', 'marmore': 'marmore_bege'}
FLOORBASE = {'areia': 'DCCBAE', 'claro': 'E4DDD0', 'marmore': 'E6DED0'}

def grupos_de_polys(polys, uvfn=None):
    """polys (cm) -> {material: [pos, nrm, uv, idx]} em METROS; normal por polígono (Newell); descarta degenerados."""
    acc = {}; descartados = 0
    for m, vs in polys:
        n, area = G.newell(vs)
        if n is None or area < 1e-4: descartados += 1; continue
        g = acc.setdefault(m, {'pos': [], 'nrm': [], 'uv': [], 'idx': []}); b = len(g['pos'])
        for v in vs:
            g['pos'].append((v[0] * UNIT, v[1] * UNIT, v[2] * UNIT)); g['nrm'].append(tuple(n))
            if uvfn: g['uv'].append(uvfn(v))
        for i in range(1, len(vs) - 1): g['idx'] += [b, b + i, b + i + 1]
    return acc, descartados

def prims_de_polys(glb, polys, matfn=None):
    acc, dr = grupos_de_polys(polys)
    prims = []
    for m, g in acc.items():
        mi = matfn(m) if matfn else None
        if mi is None:
            me, ru = PBR.get(m, (0.0, 0.9 if m.startswith('w_') else 0.8))
            mi = glb.material(m, G.MATS[m], G.ALPHA.get(m, 1.0), G.MATS[m] if m in EMISSIVOS else None, me, ru,
                              dupla_face=(m != 'teto'))        # teto: face única (voltada p/ baixo) => some na vista aérea
        prims.append((mi, g['pos'], g['nrm'], None, g['idx']))
    return prims, dr

def predio_glb(destino, textura_piso=True):
    g = GLB()
    # --- mesmas componentes de scene.full_scene(ceilings=True, ground=False)
    paredes = scene.wall_polys()
    fp = scene.floor_polys(True)
    teto = [p for p in fp if p[0] == 'teto']
    portas_janelas = scene.item_polys(A.DOORS + A.WINDOWS)
    mobiliario = scene.item_polys(A.ITEMS)
    cheio = scene.full_scene(ceilings=True, ground=False)
    assert len(cheio) == len(paredes) + len(fp) + len(portas_janelas) + len(mobiliario), 'composição diverge de full_scene'
    assert all(abs(v[1] - 300) < 1e-6 for _, vs in teto for v in vs) and teto, 'teto inesperado'

    desc = 0
    # --- pisos: 1 quad por ambiente, material próprio "piso_<id>" (textura embutida + permite realce por ambiente)
    piso_prims = []
    laje = [(scene.mat('C7B899'), [(0, 0, 2000), (1000, 0, 2000), (1000, 0, 0), (0, 0, 0)])]   # laje sob os vãos de porta
    p, d = prims_de_polys(g, laje, lambda m: g.material('piso_base', G.MATS[m], 1.0, None, 0.0, 0.9)); piso_prims += p; desc += d
    H = 0.5                                                       # cm acima da laje (evita z-fighting na vista superior)
    for k, nome, (x0, y0, x1, y1), ft in L.ROOMS:
        if textura_piso:
            tex = g.textura(os.path.join(OUT, 'texturas', FLOORTEX[ft] + '.png'))
            mi = g.material('piso_' + k, (1, 1, 1), 1.0, None, 0.0, 0.55, tex=tex, dupla_face=False)
        else:
            c = G.H(FLOORBASE[ft]); mi = g.material('piso_' + k, c, 1.0, None, 0.0, 0.55, dupla_face=False)
        quad = [(m_, vs) for m_, vs in [('x', [(x0, H, y1), (x1, H, y1), (x1, H, y0), (x0, H, y0)])]]
        acc, d = grupos_de_polys(quad, uvfn=lambda v: (v[0] / 120.0, v[2] / 120.0))   # 1 repetição = 120 cm (2x2 placas de 60)
        gg = acc['x']; piso_prims.append((mi, gg['pos'], gg['nrm'], gg['uv'] if textura_piso else None, gg['idx']))
    n_piso = g.no('pisos', g.malha('pisos', piso_prims))

    pr, d = prims_de_polys(g, paredes); desc += d; n_par = g.no('paredes', g.malha('paredes', pr))
    pr, d = prims_de_polys(g, teto); desc += d; n_teto = g.no('teto', g.malha('teto', pr))
    pr, d = prims_de_polys(g, portas_janelas); desc += d; n_esq = g.no('esquadrias', g.malha('esquadrias', pr))
    pr, d = prims_de_polys(g, mobiliario); desc += d; n_mob = g.no('mobiliario', g.malha('mobiliario', pr))
    raiz = g.no('LUMINA_Clinica', filhos=[n_piso, n_par, n_teto, n_esq, n_mob],
                extras={"unidade": "metro", "eixos": "x=leste, y=cima, z=sul (fachada/entrada em z=20 m)", "ambientes": len(L.ROOMS)})
    tam = g.salvar(destino, [raiz], {"projeto": "LÚMINA · Clínica de Estética e Biomedicina",
                                     "aviso": "Projeto conceitual. Não atesta conformidade com RDC 50/ANVISA, NBR 9050, instalações ou legislação local."})
    return tam, desc, len(cheio)

# ---------------------------------------------------------------- 3) dados para o web app
ROTULOS = {  # render -> (id, rótulo, descrição)
    'render_03_recepcao': ('recepcao', 'Recepção', 'Balcão, painel e letreiro LÚMINA'),
    'render_04_sala_espera': ('espera', 'Sala de espera', 'Sofá, poltronas e painel ripado'),
    'render_05_sala_tecnologia': ('tecnologia', 'Tecnologia', 'Ultraformer / Lavieen (ilustrativos)'),
    'render_06_sala_botox': ('botox', 'Sala de Botox', 'Procedimentos faciais'),
    'render_07_corredor': ('corredor', 'Corredor', 'Circulação principal'),
    'render_08_banheiro_acessivel': ('wc_acessivel', 'WC acessível', 'Círculo de manobra Ø1,50 m'),
    'render_01_vista_aerea_fachada': ('aerea', 'Vista aérea', 'Fachada e volumetria'),
    'render_02_vista_superior': ('superior', 'Vista superior', 'Planta em perspectiva'),
}
def orbita(eye, alvo):
    d = np.array(eye, float) - np.array(alvo, float); r = float(np.linalg.norm(d))
    return dict(theta=round(math.degrees(math.atan2(d[0], d[2])), 3), phi=round(math.degrees(math.acos(d[1] / r)), 3), r=round(r, 3))

def dados_views():
    out = []
    for nome, (eye, tg, fov, size, teto) in build_b.RENDER_CAMS.items():
        vid, rot, desc = ROTULOS[nome]; e = [round(c * UNIT, 4) for c in eye]; t = [round(c * UNIT, 4) for c in tg]
        o = orbita(e, t)
        out.append(dict(id=vid, rotulo=rot, descricao=desc, render=nome + '.png', interno=bool(teto), fov=fov,
                        eye=e, target=t, **o))
    ordem = [v[0] for v in ROTULOS.values()]
    return sorted(out, key=lambda v: ordem.index(v['id']))

def dados_rooms():
    out = []
    for k, nome, (x0, y0, x1, y1), ft in L.ROOMS:
        w, d = (x1 - x0) / 100, (y1 - y0) / 100; cx, cz = (x0 + x1) / 200, (y0 + y1) / 200
        longo_z = d >= w; R = max(w, d) * 1.15 + 2.5
        tgt = [round(cx, 3), 0.8, round(cz, 3)]
        phi = 32 if k == 'circulacao' else 28; theta = 0 if longo_z else 90
        if k in ('circulacao',): R = 17.0
        out.append(dict(id=k, nome=nome, rect=[x0 / 100, y0 / 100, x1 / 100, y1 / 100], largura=round(w, 2), profundidade=round(d, 2),
                        area=round(w * d, 1), material='piso_' + k, centro=[round(cx, 3), round(cz, 3)],
                        camera=dict(theta=theta, phi=phi, r=round(R, 2), target=tgt, fov=45)))
    return out

def dados_colisao():
    """Retângulos AABB (m) das paredes SEM os vãos de porta (janelas têm peitoril => continuam bloqueando) + móveis grandes."""
    paredes = []
    for s in A.SEGS:
        horiz = abs(s['y0'] - s['y1']) < 1e-6; t = s['t']
        lo, hi = (min(s['x0'], s['x1']), max(s['x0'], s['x1'])) if horiz else (min(s['y0'], s['y1']), max(s['y0'], s['y1']))
        fixo = s['y0'] if horiz else s['x0']; cortes = []
        for d in A.DOORS:
            if (d['axis'] == 'H') == horiz and abs((d['y'] if horiz else d['x']) - fixo) < 1:
                c = d['x'] if horiz else d['y']
                if lo - 0.1 <= c <= hi + 0.1: cortes.append((c - d['W'] / 2, c + d['W'] / 2))
        cortes.sort(); cur = lo; trechos = []
        for a, b in cortes:
            if a > cur: trechos.append((cur, a))
            cur = max(cur, b)
        if cur < hi: trechos.append((cur, hi))
        for a, b in trechos:
            r = [a, fixo - t / 2, b, fixo + t / 2] if horiz else [fixo - t / 2, a, fixo + t / 2, b]
            paredes.append([round(v * UNIT, 3) for v in r])
    moveis = []
    for it in A.ITEMS:
        if it['kind'] == 'light' or it['elev'] >= 30 or it['H'] < 40: continue
        fp = np.array(L.footprint(it)); moveis.append([round(float(v) * UNIT, 3) for v in (fp[:, 0].min(), fp[:, 1].min(), fp[:, 0].max(), fp[:, 1].max())])
    return dict(unidade='m', eixos='[x0, z0, x1, z1]', limites=[0.15, 0.15, 9.85, 19.85], altura_olhos=1.65, raio=0.22,
                inicio=dict(pos=[4.9, 19.3], yaw_graus=0), paredes=paredes, moveis=moveis)

def dados_catalogo():
    return [dict(id=n, nome=i['desc'], categoria=i['cat'], dimensoes_cm=[round(float(x), 1) for x in i['dims']], glb=f'modelos/{n}.glb')
            for n, i in sorted(REG.items(), key=lambda kv: (kv[1]['cat'], kv[0]))]

# ---------------------------------------------------------------- 4) validação de GLB (estrutural, sem dependências)
def validar_glb(caminho):
    """Confere cabeçalho, JSON, limites de bufferViews/accessors, min/max, índices, normais unitárias, imagens e referências."""
    b = open(caminho, 'rb').read()
    mg, ver, tot = struct.unpack('<4sII', b[:12]); assert mg == b'glTF' and ver == 2 and tot == len(b), 'cabeçalho GLB'
    jl, jt = struct.unpack('<I4s', b[12:20]); assert jt == b'JSON'; j = json.loads(b[20:20 + jl])
    o = 20 + jl; bl, bt = struct.unpack('<I4s', b[o:o + 8]); assert bt == b'BIN\0'; binb = b[o + 8:o + 8 + bl]
    assert j['buffers'][0]['byteLength'] <= len(binb)
    tipos = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}; dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}
    def dados(ai):
        a = j['accessors'][ai]; v = j['bufferViews'][a['bufferView']]; n = tipos[a['type']]
        assert v['byteOffset'] + v['byteLength'] <= len(binb), 'bufferView fora do buffer'
        arr = np.frombuffer(binb, dt[a['componentType']], a['count'] * n, v['byteOffset']).reshape(a['count'], n)
        assert np.isfinite(arr.astype(np.float64)).all(), 'NaN/Inf'; return a, arr
    st = {'tris': 0, 'verts': 0, 'prims': 0, 'bbox': None}; lo = np.full(3, 1e9); hi = np.full(3, -1e9)
    for me in j['meshes']:
        for p in me['primitives']:
            a, pos = dados(p['attributes']['POSITION']); _, nr = dados(p['attributes']['NORMAL']); _, ix = dados(p['indices'])
            assert np.allclose(pos.min(0), a['min'], atol=1e-5) and np.allclose(pos.max(0), a['max'], atol=1e-5), 'min/max POSITION'
            assert len(nr) == len(pos) and ix.max() < len(pos), 'índice fora de alcance'
            assert np.abs(np.linalg.norm(nr, axis=1) - 1).max() < 1e-3, 'normais não unitárias'
            assert len(ix) % 3 == 0 and 0 <= p['material'] < len(j['materials'])
            if 'TEXCOORD_0' in p['attributes']: dados(p['attributes']['TEXCOORD_0'])
            st['tris'] += len(ix) // 3; st['verts'] += len(pos); st['prims'] += 1
            lo = np.minimum(lo, pos.min(0)); hi = np.maximum(hi, pos.max(0))
    for im in j.get('images', []):
        v = j['bufferViews'][im['bufferView']]; Image.open(io.BytesIO(binb[v['byteOffset']:v['byteOffset'] + v['byteLength']])).load()
    for nd in j['nodes']:
        assert all(c < len(j['nodes']) for c in nd.get('children', [])) and nd.get('mesh', 0) < len(j['meshes'])
    st['bbox'] = (lo, hi); st['materiais'] = len(j['materials']); st['bytes'] = len(b); st['json'] = j
    st['blend'] = [m['name'] for m in j['materials'] if m.get('alphaMode') == 'BLEND']
    return st

# ---------------------------------------------------------------- 5) ícones PWA, vendor opcional, cópia de web/, zip
def gerar_icones(pasta):
    os.makedirs(pasta, exist_ok=True)
    import matplotlib.font_manager as fm
    fonte = fm.findfont('DejaVu Serif')
    for tam, nome, mask in ((192, 'icon-192.png', False), (512, 'icon-512.png', False), (512, 'icon-maskable-512.png', True)):
        im = Image.new('RGB', (tam, tam), '#7A2E3A'); d = ImageDraw.Draw(im)
        if not mask: d.rounded_rectangle([0, 0, tam - 1, tam - 1], radius=tam // 5, fill='#7A2E3A')
        m = tam * (0.30 if mask else 0.20); d.ellipse([m, m, tam - m, tam - m], outline='#B8975A', width=max(2, tam // 40))
        f = ImageFont.truetype(fonte, int(tam * (0.30 if mask else 0.34))); d.text((tam / 2, tam / 2), 'L', font=f, fill='#E3D3B5', anchor='mm')
        im.save(os.path.join(pasta, nome))

VENDOR = {  # versões fixadas; baixadas só com --vendor
    'model-viewer.min.js': 'https://cdn.jsdelivr.net/npm/@google/model-viewer@3.5.0/dist/model-viewer.min.js',
    'three/three.module.js': 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js',
    'three/addons/loaders/GLTFLoader.js': 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js',
    'three/addons/utils/BufferGeometryUtils.js': 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/utils/BufferGeometryUtils.js',
    'three/addons/controls/OrbitControls.js': 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js',
    'three/addons/environments/RoomEnvironment.js': 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/environments/RoomEnvironment.js',
}
def baixar_vendor(destino):
    ok = True
    for rel, url in VENDOR.items():
        p = os.path.join(destino, 'vendor', rel); os.makedirs(os.path.dirname(p), exist_ok=True)
        try:
            with urllib.request.urlopen(url, timeout=30) as r: open(p, 'wb').write(r.read())
        except Exception as e:
            ok = False; print(f'  [aviso] vendor: não baixou {rel} ({e.__class__.__name__}); o site usará a CDN.')
    return ok

def copiar_web(vendorizado):
    if os.path.exists(WEB_DIST): shutil.rmtree(WEB_DIST)
    shutil.copytree(os.path.join(RAIZ, 'web'), WEB_DIST, ignore=shutil.ignore_patterns('README.md', '__pycache__'))
    if vendorizado:      # importmap do Three aponta p/ cópia local
        p = os.path.join(WEB_DIST, 'three', 'index.html'); t = open(p, encoding='utf-8').read()
        t = re.sub(r'(<!--IMPORTMAP-->).*?(<!--/IMPORTMAP-->)',
                   r'\1<script type="importmap">{"imports":{"three":"../vendor/three/three.module.js","three/addons/":"../vendor/three/addons/"}}</script>\2', t, flags=re.S)
        open(p, 'w', encoding='utf-8').write(t)

def zip_final():
    alvo = os.path.join(DIST, 'LUMINA_WEB.zip')
    if os.path.exists(alvo): os.remove(alvo)
    base = os.path.basename(OUT.rstrip('/')) or 'LUMINA_WEB'
    with zipfile.ZipFile(alvo, 'w', zipfile.ZIP_DEFLATED) as z:
        for raiz, dirs, fs in os.walk(OUT):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', 'node_modules', '.git')]
            for f in fs:
                p = os.path.join(raiz, f)
                if os.path.abspath(p) == os.path.abspath(alvo) or f.endswith('.pyc'): continue
                z.write(p, os.path.join('LUMINA_WEB', os.path.relpath(p, OUT)))
    return alvo

# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description='LÚMINA: OBJ -> GLB + web app em dist/web')
    ap.add_argument('--vendor', action='store_true', help='baixa model-viewer e three (versões fixas) p/ dist/web/vendor (precisa de internet)')
    ap.add_argument('--sem-textura-piso', action='store_true', help='pisos em cor lisa (sem textura embutida)')
    ap.add_argument('--otimizar', choices=['draco', 'meshopt'], help='comprime os GLB com gltf-transform (npx; precisa de internet)')
    ap.add_argument('--sem-zip', action='store_true', help='não gera dist/LUMINA_WEB.zip')
    a = ap.parse_args()
    rel = ['VERIFICAÇÃO DO PACOTE WEB — LÚMINA (export_web.py)', '']
    erros = []

    # a) peças
    pasta_mod = os.path.join(WEB_DIST, 'modelos'); stage = os.path.join(DIST, '_stage')
    if os.path.exists(stage): shutil.rmtree(stage)
    os.makedirs(stage)
    tot_b = 0; probs = 0
    for nome, info in REG.items():
        dst = os.path.join(stage, 'modelos', nome + '.glb'); peca_glb(nome, info, dst)
        st = validar_glb(dst); tot_b += st['bytes']
        dims_glb = (st['bbox'][1] - st['bbox'][0]) * 100; dims_reg = np.array(info['dims'])      # reg: L,A,P (cm)
        if not np.allclose(dims_glb, dims_reg, atol=0.6): probs += 1; erros.append(f'{nome}: dimensões GLB {dims_glb.round(1)} ≠ REG {dims_reg}')
    rel.append(f'[OK] {len(REG)} peças convertidas OBJ→GLB ({tot_b/1024:.0f} KB no total), todas validadas; dimensões do GLB (m×100) = dimensões de models.REG (±0,6 cm)' if not probs
               else f'[ALERTA] {probs} peça(s) com dimensão divergente')

    # b) prédio
    dst = os.path.join(stage, 'modelos', 'predio_completo.glb')
    tam, desc, npol = predio_glb(dst, textura_piso=not a.sem_textura_piso)
    st = validar_glb(dst); lo, hi = st['bbox']
    rel.append(f'[OK] predio_completo.glb: {tam/1048576:.2f} MB, {st["tris"]} triângulos, {st["materiais"]} materiais, {npol} polígonos de scene.full_scene(ceilings=True); {desc} polígonos degenerados descartados')
    ext = (hi - lo)
    if not (abs(ext[0] - 10) < 0.02 and abs(ext[1] - 3) < 0.02 and abs(ext[2] - 20) < 0.02): erros.append(f'bbox do prédio inesperado: {ext}')
    else: rel.append(f'[OK] Escala em metros: caixa do prédio = {ext[0]:.2f} × {ext[2]:.2f} m, pé-direito {ext[1]:.2f} m (planta 10×20 m, 3 m)')
    if tam > 20 * 1048576: erros.append('predio_completo.glb > 20 MB: use --otimizar meshopt')
    else: rel.append('[OK] predio_completo.glb < 20 MB')
    for m in st['blend']: pass
    rel.append(f'[OK] Materiais com alphaMode BLEND (de ALPHA): {", ".join(sorted(set(st["blend"]))) or "nenhum"}')
    mats_vis = {m['name'] for m in st['json']['materials']}
    faltam = [f'piso_{k}' for k, *_ in L.ROOMS if f'piso_{k}' not in mats_vis]
    (rel.append('[OK] 16 materiais piso_<ambiente> presentes (realce por ambiente no web app)') if not faltam else erros.append(f'faltam materiais de piso: {faltam}'))
    rel.append(f'[OK] Nós do glTF: {", ".join(n["name"] for n in st["json"]["nodes"])}')

    # c) otimização opcional
    if a.otimizar:
        for f in glob.glob(os.path.join(stage, 'modelos', '*.glb')):
            r = subprocess.run(['npx', '--yes', '@gltf-transform/cli', 'optimize', f, f, '--compress', a.otimizar], capture_output=True, text=True)
            if r.returncode: print('  [aviso] gltf-transform falhou:', r.stderr[-200:]); break

    # d) dados do web app
    views = dados_views(); rooms = dados_rooms(); col = dados_colisao(); cat = dados_catalogo()
    for v in views:                                              # confere ida e volta orbit -> câmera
        th, ph = math.radians(v['theta']), math.radians(v['phi'])
        e = np.array(v['target']) + v['r'] * np.array([math.sin(ph) * math.sin(th), math.cos(ph), math.sin(ph) * math.cos(th)])
        if np.abs(e - np.array(v['eye'])).max() > 0.01: erros.append(f'orbit inconsistente em {v["id"]}')
    rel.append(f'[OK] {len(views)} vistas = câmeras de build_b.RENDER_CAMS (render_01..08); órbita (θ, φ, r) conferida por ida e volta com a posição do olho')
    rel.append(f'[OK] {len(rooms)} ambientes (exatamente os de layout.ROOMS); colisão: {len(col["paredes"])} trechos de parede (vãos de porta livres), {len(col["moveis"])} móveis')
    dd = os.path.join(stage, 'data')
    os.makedirs(dd, exist_ok=True)
    for nome, dado in (('views.json', views), ('rooms.json', rooms), ('collision.json', col), ('catalogo.json', cat)):
        json.dump(dado, open(os.path.join(dd, nome), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # e) montar dist/web
    gerar_icones(os.path.join(RAIZ, 'web', 'icons'))
    vend = False
    copiar_web(False)
    if a.vendor:
        vend = baixar_vendor(WEB_DIST)
        if vend: copiar_web(True); baixar_vendor(WEB_DIST)
    shutil.copytree(os.path.join(stage, 'modelos'), pasta_mod); shutil.copytree(dd, os.path.join(WEB_DIST, 'data'))
    shutil.copytree(os.path.join(OUT, 'texturas'), os.path.join(WEB_DIST, 'texturas'))
    shutil.rmtree(stage)
    # service worker: lista de pré-cache + versão (hash dos arquivos pré-cacheados)
    arq = sorted(os.path.relpath(os.path.join(r, f), WEB_DIST).replace(os.sep, '/') for r, _, fs in os.walk(WEB_DIST) for f in fs
                 if not f.endswith('.glb') or f == 'predio_completo.glb')
    arq = [x for x in arq if not x.startswith('texturas/') and not x.startswith('vendor/') and x != 'sw.js']
    h = hashlib.md5()
    for x in arq:
        h.update(x.encode('utf-8'))
        with open(os.path.join(WEB_DIST, *x.split('/')), 'rb') as f: h.update(f.read())
    ver = h.hexdigest()[:8]
    p = os.path.join(WEB_DIST, 'sw.js'); t = open(p, encoding='utf-8').read()
    t = re.sub(r'/\*VERSAO\*/.*?/\*FIM\*/', f'/*VERSAO*/"{ver}"/*FIM*/', t, flags=re.S)
    t = re.sub(r'/\*PRECACHE\*/.*?/\*FIM\*/', '/*PRECACHE*/' + json.dumps(['./'] + arq) + '/*FIM*/', t, flags=re.S)
    open(p, 'w', encoding='utf-8').write(t)
    rel.append(f'[OK] dist/web montado: {len(arq)} arquivos no pré-cache do service worker (versão {ver}); vendor local: {"sim" if vend else "não (usa CDN com versões fixas)"}')
    for obrig in ('index.html', 'modelos/predio_completo.glb', 'three/index.html', 'manifest.webmanifest', 'sw.js', 'data/views.json'):
        if not os.path.exists(os.path.join(WEB_DIST, obrig)): erros.append('ausente em dist/web: ' + obrig)

    rel += ['', 'LIMITAÇÕES: a validação é estrutural (GLB bem formado, limites, normais, min/max, imagens, escala).',
            'Renderização real em <model-viewer>/Three.js depende do navegador: confira visualmente após `npx serve dist/web`.',
            'Ultraformer e Lavieen são volumes ilustrativos. Conformidade normativa (RDC 50, NBR 9050, instalações) NÃO foi verificada.']
    if erros: rel += [''] + ['[ALERTA] ' + e for e in erros]
    open(os.path.join(DIST, 'verificacao_web.txt'), 'w', encoding='utf-8').write('\n'.join(rel) + '\n')
    print('\n'.join(rel))
    if not a.sem_zip:
        z = zip_final(); print(f'zip final: {z} ({os.path.getsize(z)/1048576:.1f} MB)')
    if erros: sys.exit(1)

if __name__ == '__main__':
    main()
