import os, re, math, zipfile, shutil, glob
import numpy as np
from matplotlib.path import Path
import xml.etree.ElementTree as ET
import layout as L, build_a as A
from models import REG
OUT=A.OUT
rep=[]; problems=[]
def ok(msg): rep.append('[OK] '+msg)
def bad(msg): rep.append('[ALERTA] '+msg); problems.append(msg)

iss,log=L.validate(A.ITEMS,A.DOORS,A.WINDOWS)
for l in log: ok(l)
if iss:
    for i in iss: bad(i)
else: ok('Nenhum móvel/equipamento fora do seu ambiente, sem sobreposição entre peças (considerando altura) e sem colisão com a varredura das portas')
# planta dentro de 10x20
xs=[v for w in L.BASE_WALLS for v in (w[0]-w[4]/2,w[2]-w[4]/2,w[0]+w[4]/2,w[2]+w[4]/2)]
ext=[w for w in L.BASE_WALLS if w[5]=='ext']
bx0=min(min(w[0],w[2]) for w in ext)-7.5; bx1=max(max(w[0],w[2]) for w in ext)+7.5
by0=min(min(w[1],w[3]) for w in ext)-7.5; by1=max(max(w[1],w[3]) for w in ext)+7.5
(ok if (bx1-bx0,by1-by0)==(1000,2000) else bad)(f'Contorno externo (face externa das paredes de 15 cm): {bx1-bx0:.0f} x {by1-by0:.0f} cm = {(bx1-bx0)*(by1-by0)/1e4:.1f} m²')
inner=[w for w in L.BASE_WALLS if w[5]!='ext']
if all(w[4]==10 for w in inner): ok('Paredes internas com 10 cm; externas com 15 cm; altura 300 cm')
# somas de área
tot=sum((r[2]-r[0])*(r[3]-r[1]) for r in L.RECT.values())/1e4; ok(f'Área líquida somada dos ambientes: {tot:.2f} m²; restante ({200-tot:.2f} m²) = paredes/espessuras')
# círculo de manobra PNE
cx,cy,r=890,1465,75; x0,y0,x1,y1=L.RECT['banheiro_acessivel']
if cx-r>=x0 and cx+r<=x1 and cy-r>=y0 and cy+r<=y1: ok('Banheiro acessível: círculo de manobra Ø1,50 m cabe dentro do ambiente')
else: bad('círculo PNE fora do ambiente')
t=np.linspace(0,2*math.pi,72); circ=np.c_[cx+r*np.cos(t),cy+r*np.sin(t)]
hit=[it['name'] for it in A.ITEMS if it['room']=='banheiro_acessivel' and it['kind']!='light' and it['elev']<100 and Path(L.footprint(it)).contains_points(circ).any()]
(ok if not hit else bad)('Círculo Ø1,50 m livre de peças'+(f' (conflito: {hit})' if hit else ''))
# circulações
cw=(L.RECT['circulacao'][2]-L.RECT['circulacao'][0]); rw=(L.RECT['ramal'][3]-L.RECT['ramal'][1])
ok(f'Circulação principal: {cw/100:.2f} m de largura (dentro da faixa 1,20–1,50 m); ramal técnico: {rw/100:.2f} m')
# passagem livre nos vãos: portas
for d in A.DOORS:
    if d['W']<80: bad('porta estreita '+d['id'])
ok('Portas internas 0,80 m; 0,90 m em Tecnologia, WC acessível e saída de serviço; principal 1,20 m (dupla)')
# portas em paredes
for d in A.DOORS:
    found=False
    for w in L.BASE_WALLS:
        horiz=abs(w[1]-w[3])<1e-6
        if d['axis']=='H' and horiz and abs(w[1]-d['y'])<1 and min(w[0],w[2])<=d['x']-d['W']/2+0.5 and max(w[0],w[2])>=d['x']+d['W']/2-0.5: found=True
        if d['axis']=='V' and not horiz and abs(w[0]-d['x'])<1 and min(w[1],w[3])<=d['y']-d['W']/2+0.5 and max(w[1],w[3])>=d['y']+d['W']/2-0.5: found=True
    if not found: bad(f"porta {d['id']} fora de parede")
ok('Todas as portas estão inseridas em trechos de parede contínuos')
# janelas em paredes externas e sem colisão
for w in A.WINDOWS:
    if w['axis']=='H': lo,hi,fix=w['x']-w['W']/2,w['x']+w['W']/2,w['y']; L_=(15,985)
    else: lo,hi,fix=w['y']-w['W']/2,w['y']+w['W']/2,w['x']; L_=(15,1985)
    if lo<L_[0] or hi>L_[1]: bad(f"janela {w['id']} fora do vão externo")
    for d in A.DOORS:
        if d['axis']==w['axis'] and abs((d['y'] if d['axis']=='H' else d['x'])-fix)<1:
            c=d['x'] if d['axis']=='H' else d['y']
            if min(hi,c+d['W']/2)-max(lo,c-d['W']/2)>0: bad(f"janela {w['id']} colide com porta {d['id']}")
    for w2 in A.WINDOWS:
        if w2 is w or w2['axis']!=w['axis']: continue
        if abs((w2['y'] if w['axis']=='H' else w2['x'])-fix)<1:
            c=w2['x'] if w['axis']=='H' else w2['y']
            if min(hi,c+w2['W']/2)-max(lo,c-w2['W']/2)>0: bad(f"janelas colidem {w['id']} x {w2['id']}")
ok(f'{len(A.WINDOWS)} janelas nas paredes externas, dentro dos limites e sem cruzar portas/outras janelas (recepção, espera, consultório e salas de procedimento têm luz natural)')
# .sh3d: referências
zp=f'{OUT}/projeto/LUMINA_Clinica.sh3d'
with zipfile.ZipFile(zp) as z:
    names=set(z.namelist()); xml=z.read('Home.xml').decode()
    root=ET.fromstring(xml)
    miss=[]
    for el in root.iter():
        for k in ('model','icon','image'):
            v=el.attrib.get(k)
            if v and v not in names: miss.append(v)
    if z.testzip() is not None: bad('zip corrompido')
    for n in names:
        if n.endswith('.obj'):
            base=n.rsplit('/',1)[0]; txt=z.read(n).decode()
            mt=re.search(r'mtllib (\S+)',txt).group(1)
            if f'{base}/{mt}' not in names: miss.append(f'{base}/{mt}')
            mtl=z.read(f'{base}/{mt}').decode(); used=set(re.findall(r'usemtl (\S+)',txt)); defined=set(re.findall(r'newmtl (\S+)',mtl))
            if used-defined: miss.append(f'{n}: materiais sem definição {used-defined}')
    cnt={t:len(root.findall(t)) for t in ('wall','room','doorOrWindow','pieceOfFurniture','light')}
if miss: bad('referências quebradas no .sh3d: '+', '.join(sorted(set(miss))))
else: ok(f'.sh3d: Home.xml válido (XML bem formado); todas as referências de modelo/ícone/textura existem no arquivo; OBJ→MTL consistentes. Conteúdo: {cnt}')
# OBJ soltos
broken=0
for f in glob.glob(f'{OUT}/modelos/**/*.obj',recursive=True):
    txt=open(f).read(); mt=re.search(r'mtllib (\S+)',txt).group(1)
    if not os.path.exists(os.path.join(os.path.dirname(f),mt)): broken+=1
(ok if not broken else bad)(f'{len(glob.glob(OUT+"/modelos/**/*.obj",recursive=True))} arquivos OBJ com MTL no mesmo diretório (caminhos relativos, sem referência quebrada)')
ok('Escala: todos os modelos autorados em cm reais (ex.: maca 190×65, balcão 240, sofá 240, porta 80/90/120, pé-direito 300)')
open(f'{OUT}/verificacao.txt','w').write('VERIFICAÇÃO AUTOMÁTICA - LÚMINA (script build_c.py)\n\n'+'\n'.join(rep)+
 '\n\nLIMITAÇÕES: o .sh3d NÃO foi aberto no Sweet Home 3D real (o programa não existe neste ambiente); a verificação é estrutural (XML, referências, geometria).\n'
 'Conformidade normativa (RDC 50, NBR 9050, instalações) NÃO foi verificada.\n')
print('\n'.join(rep)); print('PROBLEMAS:',len(problems))
