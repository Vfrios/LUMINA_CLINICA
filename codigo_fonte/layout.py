import math
import numpy as np
from matplotlib.path import Path
from models import REG

PI=math.pi
def dims(model):
    lo,hi=REG[model]['mesh'].bbox(); return tuple(round(float(v),1) for v in (hi-lo))  # W,H,D

# ---------------- ambientes (retângulos líquidos, cm) ----------------
ROOMS=[
 ('recepcao','Recepção',(15,1635,415,1985),'areia'),
 ('espera','Sala de espera',(425,1635,985,1985),'areia'),
 ('circulacao','Circulação principal',(425,15,555,1635),'areia'),
 ('ramal','Circulação (ramal técnico)',(565,1245,985,1365),'claro'),
 ('consultorio','Consultório / Avaliação',(15,1345,415,1625),'areia'),
 ('botox','Sala de Botox e procedimentos faciais',(15,985,415,1335),'claro'),
 ('peeling','Sala de Peeling e Limpeza de Pele',(15,625,415,975),'claro'),
 ('drenagem','Sala de Drenagem',(15,265,415,615),'claro'),
 ('deposito','Depósito / Armazenamento',(15,15,415,255),'claro'),
 ('banheiro_clientes','Banheiro de clientes',(565,1375,755,1625),'marmore'),
 ('banheiro_acessivel','Banheiro acessível',(765,1375,985,1625),'marmore'),
 ('dml','DML / Área de limpeza',(565,935,725,1235),'claro'),
 ('copa','Copa / Área de funcionários',(735,935,985,1235),'claro'),
 ('tecnologia','Sala de Tecnologia Estética (Ultraformer / Lavieen)',(565,445,985,925),'claro'),
 ('descanso','Área de funcionários (descanso / vestiário)',(565,185,985,435),'areia'),
 ('area_tecnica','Área técnica (TI / elétrica)',(565,15,985,175),'claro'),
]
RECT={k:r for k,_,r,_ in ROOMS}
NAME={k:n for k,n,_,_ in ROOMS}

# ---------------- paredes (eixos, cm) ----------------
E=15; I=10
BASE_WALLS=[  # (xs,ys,xe,ye,thickness,kind)
 (7.5,7.5,992.5,7.5,E,'ext'),(992.5,7.5,992.5,1992.5,E,'ext'),(992.5,1992.5,7.5,1992.5,E,'ext'),(7.5,1992.5,7.5,7.5,E,'ext'),
 (420,7.5,420,1630,I,'int'),          # corredor | coluna esquerda
 (420,1630,420,1800,I,'div'),         # divisória ripada recepção/espera
 (560,7.5,560,1240,I,'int'),(560,1370,560,1630,I,'int'),
 (730,930,730,1240,I,'int'),(760,1370,760,1630,I,'int'),
 (7.5,1630,420,1630,I,'int'),(560,1630,992.5,1630,I,'int'),
 (7.5,1340,420,1340,I,'int'),(7.5,980,420,980,I,'int'),(7.5,620,420,620,I,'int'),(7.5,260,420,260,I,'int'),
 (555,1370,992.5,1370,I,'int'),(555,1240,992.5,1240,I,'int'),
 (560,930,992.5,930,I,'int'),(560,440,992.5,440,I,'int'),(560,180,992.5,180,I,'int'),
]
# ---------------- portas / janelas ----------------
# porta: id, modelo, (cx,cy), largura, eixo do vão ('V'/'H'), swing (N/S/E/W), dobradiça ('min'/'max'), ambiente
DOORS=[
 ('P-Consultório','porta_80',(420,1575),80,'V','W','max','consultorio'),
 ('P-Botox','porta_80',(420,1285),80,'V','W','max','botox'),
 ('P-Peeling','porta_80',(420,925),80,'V','W','max','peeling'),
 ('P-Drenagem','porta_80',(420,565),80,'V','W','max','drenagem'),
 ('P-Depósito','porta_80',(420,205),80,'V','W','max','deposito'),
 ('P-Tecnologia','porta_90',(560,875),90,'V','E','max','tecnologia'),
 ('P-Descanso','porta_80',(560,385),80,'V','E','max','descanso'),
 ('P-Área técnica','porta_80',(560,100),80,'V','E','max','area_tecnica'),
 ('P-WC clientes','porta_80',(610,1370),80,'H','N','min','ramal'),
 ('P-WC acessível','porta_90',(830,1370),90,'H','N','min','ramal'),
 ('P-DML','porta_80',(645,1240),80,'H','N','max','dml'),
 ('P-Copa','porta_80',(785,1240),80,'H','N','max','copa'),
 ('P-Principal','porta_principal_120',(490,1992.5),120,'H','N','both','espera'),
 ('P-Serviço','porta_servico_90',(490,7.5),90,'H','N','min','circulacao'),
]
# janela: id, modelo, (cx,cy), largura, altura, elevação, eixo
WINDOWS=[
 ('J-Recepção frente','janela_250x170',(215,1992.5),250,170,70,'H'),
 ('J-Espera frente','janela_300x150',(790,1992.5),300,150,90,'H'),
 ('J-Recepção lateral','janela_160x150',(7.5,1810),160,150,90,'V'),
 ('J-Consultório','janela_110x120',(7.5,1495),110,120,100,'V'),
 ('J-Botox','janela_140x120',(7.5,1160),140,120,100,'V'),
 ('J-Peeling','janela_140x120',(7.5,800),140,120,100,'V'),
 ('J-Drenagem','janela_140x120',(7.5,440),140,120,100,'V'),
 ('J-Depósito','janela_80x60',(7.5,135),80,60,150,'V'),
 ('J-Espera lateral','janela_140x140',(992.5,1800),140,140,100,'V'),
 ('J-WC acessível','janela_60x50',(992.5,1520),60,50,160,'V'),
 ('J-Ramal','janela_100x140',(992.5,1305),100,140,90,'V'),
 ('J-Copa','janela_100x100',(992.5,1085),100,100,115,'V'),
 ('J-Tecnologia','janela_160x130',(992.5,690),160,130,100,'V'),
 ('J-Descanso','janela_140x130',(992.5,310),140,130,100,'V'),
 ('J-Área técnica','janela_60x50',(992.5,95),60,50,160,'V'),
]

# ---------------- mobiliário ----------------
ITEMS=[]   # dict(id,model,x,y,elev,angle,W,D,H,room,kind,name)
def _dn(model): 
    w,h,d=dims(model); return w,d,h
def put(model,x,y,ang_deg=0,elev=0,room=None,kind='furn',name=None,power=None):
    w,d,h=_dn(model)
    ITEMS.append(dict(model=model,x=x,y=y,elev=elev,angle=math.radians(ang_deg),W=w,D=d,H=h,room=room,kind=kind,name=name or REG[model]['desc'],power=power))
    return ITEMS[-1]
FACE={'S':0,'N':180,'E':270,'W':90}   # direção para onde a frente aponta -> ângulo (graus)
def at_wall(model,side,along,room,gap=0,elev=0,kind='furn',name=None):
    x0,y0,x1,y1=RECT[room]; w,d,h=_dn(model)
    if side=='N': return put(model,along,y0+gap+d/2,0,elev,room,kind,name)
    if side=='S': return put(model,along,y1-gap-d/2,180,elev,room,kind,name)
    if side=='W': return put(model,x0+gap+d/2,along,270,elev,room,kind,name)   # frente para leste
    if side=='E': return put(model,x1-gap-d/2,along,90,elev,room,kind,name)    # frente para oeste

def build_items():
    ITEMS.clear()
    # ===== RECEPÇÃO =====
    r='recepcao'
    at_wall('painel_logo','N',215,r,0,0,name='Painel do logotipo LÚMINA')
    put('letreiro_lumina',215,1635+6+1.5+0.2,0,170,r,name='Logotipo LÚMINA (letras 3D dourado fosco)')
    at_wall('armario_baixo_240','N',215,r,6,0,name='Armário inferior')
    put('balcao_recepcao',215,1830,0,0,r,name='Balcão de recepção')
    put('cadeira_atendimento',215,1745,0,0,r)
    put('monitor',215,1828,180,75,r,name='Monitor'); put('teclado',215,1806,180,75,r,name='Teclado')
    put('monitor',150,1676,0,75,r,name='Monitor secundário') if False else None
    put('impressora',310,1661,0,75,r)
    put('vaso_decor',110,1661,0,75,r); put('planta_pequena',270,1661,0,75,r)
    put('vaso_decor',290,1852,0,105,r)
    put('planta_grande',45,1960,0,0,r)
    for x in (140,215,290): put('pendente_dourado',x,1830,0,200,r,'light',name='Pendente decorativo',power=0.5)
    put('fita_led_v',215-119,1636,0,15,r,'light',name='LED vertical atrás do painel',power=0.3)
    put('fita_led_v',215+119,1636,0,15,r,'light',name='LED vertical atrás do painel',power=0.3)
    put('fita_led_h',215,1636,0,262,r,'light',name='LED superior atrás do painel',power=0.3)
    # ===== ESPERA =====
    r='espera'
    at_wall('painel_ripado_400x260','N',770,r,0,0,name='Painel ripado de madeira')
    put('espelho_redondo_100',770,1635+4+1.6,0,110,r,name='Espelho decorativo redondo')
    put('sofa_4_lugares',985-45,1815,90,0,r,name='Sofá 4 lugares')
    at_wall('mesa_lateral','E',1665,r,0,0)
    put('abajur',962.5,1665,0,53,r)
    put('mesa_centro_redonda',790,1805,0,0,r)
    put('poltrona_marsala',790,1690,0,0,r,name='Poltrona marsala 1'); put('poltrona_marsala',790,1920,180,0,r,name='Poltrona marsala 2')
    put('planta_grande',955,1962,0,0,r)
    put('fita_led_400',770,1640,0,262,r,'light',name='LED indireto sobre painel ripado',power=0.3)
    # ===== CONSULTÓRIO =====
    r='consultorio'
    at_wall('maca_profissional','W',1455,r,0,0,name='Maca profissional')
    at_wall('armario_alto_120','N',350,r,0,0); at_wall('bancada_160','N',180,r,0,0,name='Bancada')
    put('espelho_100x90',180,1345+1.5,0,125,r)
    put('lixeira',275,1372,0,0,r); put('planta_pequena',240,1370,0,90,r); put('vaso_decor',130,1368,0,90,r)
    put('mesa_escritorio_140',240,1500,0,0,r,name='Mesa de consultório')
    put('cadeira_visita',240,1580,180,0,r,name='Cadeira do profissional')
    put('cadeira_visita',205,1425,0,0,r,name='Cadeira do paciente 1'); put('cadeira_visita',275,1425,0,0,r,name='Cadeira do paciente 2')
    put('monitor',240,1480,0,75,r); put('teclado',240,1512,0,75,r)
    put('quadro_abstrato',415-1.75,1440,90,120,r)
    # ===== BOTOX =====
    r='botox'
    put('maca_profissional',215,1160,0,0,r,name='Maca profissional'); put('mocho',88,1160,0,0,r)
    put('carrinho_auxiliar',345,1228,0,0,r)
    at_wall('bancada_pia_200','N',300,r,0,0,name='Bancada com pia'); at_wall('armario_alto_100','N',80,r,0,0)
    put('espelho_120x90',300,985+1.5,0,130,r); put('lixeira',165,1010,0,0,r); put('conjunto_materiais',250,1012,0,90,r)
    put('spot_direcionavel',215,1160,0,283,r,'light',name='Spot técnico sobre a maca',power=0.6)
    put('painel_led_60',150,1090,0,297,r,'light',name='Painel LED técnico',power=0.6); put('painel_led_60',290,1240,0,297,r,'light',name='Painel LED técnico',power=0.6)
    put('fita_led_400',215,990,0,285,r,'light',name='LED indireto',power=0.25)
    # ===== PEELING =====
    r='peeling'
    put('maca_profissional',215,800,0,0,r,name='Maca profissional'); put('mocho',88,800,0,0,r)
    put('carrinho_auxiliar',240,870,0,0,r); put('cart_limpeza_pele',345,720,0,0,r); put('vaporizador_ozonio',70,712,0,0,r)
    put('lupa_luminaria',140,866,0,0,r)
    at_wall('bancada_pia_200','N',300,r,0,0,name='Bancada com pia'); at_wall('armario_alto_100','N',80,r,0,0)
    put('espelho_120x90',300,625+1.5,0,130,r); put('lixeira',165,650,0,0,r); put('conjunto_materiais',250,652,0,90,r)
    put('spot_direcionavel',215,800,0,283,r,'light',name='Spot técnico sobre a maca',power=0.6)
    put('painel_led_60',150,730,0,297,r,'light',name='Painel LED técnico',power=0.6); put('painel_led_60',290,880,0,297,r,'light',name='Painel LED técnico',power=0.6)
    put('fita_led_400',215,630,0,285,r,'light',name='LED indireto',power=0.25)
    # ===== DRENAGEM =====
    r='drenagem'
    put('maca_profissional',215,440,0,0,r,name='Maca profissional'); put('poltrona_drenagem',350,310,90,0,r)
    at_wall('armario_alto_100','S',100,r,0,0); put('carrinho_auxiliar',330,520,0,0,r)
    put('planta_grande',50,300,0,0,r); put('quadro_abstrato',200,265+1.5,0,130,r); put('vaso_decor',150,300,0,0,r,name='Vaso decorativo') if False else None
    put('mesa_lateral',300,315,0,0,r) if False else None
    put('fita_led_400',215,270,0,285,r,'light',name='LED indireto acolhedor',power=0.25)
    put('fita_led_400',215,610,0,285,r,'light',name='LED indireto acolhedor',power=0.25)
    # ===== TECNOLOGIA =====
    r='tecnologia'
    put('maca_profissional',775,690,0,0,r,name='Maca profissional')
    at_wall('ultraformer','E',590,r,0,0,name='Ultraformer'); at_wall('lavieen','E',800,r,0,0,name='Lavieen')
    at_wall('cadeira_visita','W',600,r,0,0); at_wall('cadeira_visita','W',665,r,0,0)
    put('carrinho_auxiliar',740,785,0,0,r)
    at_wall('bancada_pia_220','N',800,r,0,0,name='Bancada com pia'); at_wall('armario_alto_100','N',625,r,0,0); at_wall('armario_alto_60','N',945,r,0,0)
    put('espelho_140x90',800,445+1.5,0,130,r); put('lixeira',700,525,0,0,r); put('conjunto_materiais',770,478,0,90,r)
    put('spot_direcionavel',775,690,0,283,r,'light',name='Spot técnico sobre a maca',power=0.6)
    for x,y in((650,560),(900,560),(650,800),(900,800)): put('painel_led_60',x,y,0,297,r,'light',name='Painel LED técnico',power=0.6)
    # ===== DESCANSO =====
    r='descanso'
    at_wall('armario_vestiario_200','N',680,r,0,0); at_wall('sofa_2_lugares','S',900,r,0,0); put('mesa_lateral',795,412,0,0,r)
    put('planta_grande',955,215,0,0,r)
    # ===== ÁREA TÉCNICA =====
    r='area_tecnica'
    at_wall('rack_ti','N',690,r,0,0); at_wall('quadro_eletrico','E',95,r,0,110); at_wall('prateleiras_dml','N',850,r,0,0,name='Prateleiras técnicas')
    # ===== COPA =====
    r='copa'
    at_wall('bancada_pia_200','E',1050,r,0,0,name='Bancada com pia'); put('microondas',955,1120,90,90,r)
    put('armario_aereo_170',860,935+19,0,140,r); at_wall('frigobar','N',765,r,0,0)
    put('mesa_copa_redonda',840,1080,0,0,r); put('cadeira_copa',783,1080,270,0,r); put('cadeira_copa',897,1080,90,0,r)
    put('lixeira',940,1190,0,0,r)
    # ===== DML =====
    r='dml'
    at_wall('tanque_dml','N',650,r,0,0); at_wall('armario_alto_80','W',1040,r,0,0); at_wall('prateleiras_dml','E',1090,r,0,0)
    put('balde_e_rodo',585,1205,0,0,r)
    # ===== DEPÓSITO =====
    r='deposito'
    at_wall('estante_deposito_360','N',215,r,0,0); at_wall('estante_deposito_160','W',150,r,0,0)
    at_wall('armario_alto_120','S',150,r,0,0); put('caixas_empilhadas',300,130,0,0,r)
    # ===== BANHEIRO CLIENTES =====
    r='banheiro_clientes'
    at_wall('vaso_sanitario','S',690,r,0,0); at_wall('lavatorio_60','E',1500,r,0,0)
    put('espelho_60x80',755-1.5,1500,90,115,r); put('dispenser_sabonete',755-6,1552,90,100,r)
    put('dispenser_papel',565+5.5,1480,270,100,r); put('lixeira',600,1600,0,0,r)
    # ===== BANHEIRO ACESSÍVEL =====
    r='banheiro_acessivel'
    at_wall('vaso_sanitario','S',900,r,0,0); at_wall('lavatorio_pne','W',1520,r,0,0)
    at_wall('barra_apoio_80','E',1585,r,0,80); at_wall('barra_apoio_70','S',900,r,0,80)
    put('espelho_60x80',765+1.5,1520,270,110,r); put('dispenser_sabonete',765+6,1475,270,100,r)
    put('lixeira',965,1400,0,0,r)
    # ===== CIRCULAÇÃO =====
    r='circulacao'
    for y in (1430,1105,745,385): put('painel_ripado_150x260',427,y,270,0,r,name='Painel ripado (circulação)')
    for y in (120,400,700,1000,1300,1560): put('spot_embutido',490,y,0,298,r,'light',name='Spot LED embutido',power=0.4)
    # spots gerais
    def spots(room,xs,ys):
        for x in xs:
            for y in ys: put('spot_embutido',x,y,0,298,room,'light',name='Spot LED embutido',power=0.4)
    spots('recepcao',(100,215,330),(1700,1900)); spots('espera',(500,650,800,930),(1700,1900))
    spots('consultorio',(120,250,360),(1420,1560)); spots('drenagem',(120,215,320),(340,540))
    spots('banheiro_clientes',(660,),(1440,1560)); spots('banheiro_acessivel',(875,),(1440,1560))
    spots('ramal',(650,800,930),(1305,)); spots('dml',(645,),(1000,1150)); spots('copa',(860,),(1000,1150))
    spots('descanso',(650,780,900),(250,360)); spots('area_tecnica',(700,850),(95,)); spots('deposito',(120,215,320),(135,))
    return ITEMS

def build_doors():
    out=[]
    for did,model,(cx,cy),W,ax,sw,hinge,room in DOORS:
        w,d,h=_dn(model)
        ang={'N':0,'S':180,'E':90,'W':270}[sw]
        out.append(dict(id=did,model=model,x=cx,y=cy,W=W,D=d,H=h,axis=ax,swing=sw,hinge=hinge,room=room,angle=math.radians(ang),elev=0))
    return out
def build_windows():
    out=[]
    for wid,model,(cx,cy),W,Hh,el,ax in WINDOWS:
        w,d,h=_dn(model); ang=0 if ax=='H' else 90
        out.append(dict(id=wid,model=model,x=cx,y=cy,W=W,D=d,H=Hh,axis=ax,elev=el,angle=math.radians(ang)))
    return out

def footprint(it):
    a=it['angle']; c,s=math.cos(a),math.sin(a); hw,hd=it['W']/2,it['D']/2
    return [(it['x']+lx*c-lz*s, it['y']+lx*s+lz*c) for lx,lz in ((-hw,-hd),(hw,-hd),(hw,hd),(-hw,hd))]

def door_sector(d,n=10):
    """polígono da varredura da folha (quarto de círculo) em coords de planta"""
    cx,cy,W=d['x'],d['y'],d['W']-8
    if d['hinge']=='both':
        return [door_sector(dict(d,x=cx-W/2 if False else cx,hinge=h,W=d['W']/2+8),n) for h in('min','max')]
    r=W; sw=d['swing']
    if d['axis']=='V':
        hy=cy-d['W']/2+4 if d['hinge']=='min' else cy+d['W']/2-4; hx=cx; cdir=(0,1) if d['hinge']=='min' else (0,-1)
    else:
        hx=cx-d['W']/2+4 if d['hinge']=='min' else cx+d['W']/2-4; hy=cy; cdir=(1,0) if d['hinge']=='min' else (-1,0)
        cy=hy
    if d['axis']=='V': hy_,hx_=hy,hx
    else: hy_,hx_=hy,hx
    odir={'N':(0,-1),'S':(0,1),'E':(1,0),'W':(-1,0)}[sw]
    a0=math.atan2(cdir[1],cdir[0]); a1=math.atan2(odir[1],odir[0])
    da=(a1-a0+PI)%(2*PI)-PI
    pts=[(hx_,hy_)]+[(hx_+r*math.cos(a0+da*i/n),hy_+r*math.sin(a0+da*i/n)) for i in range(n+1)]
    return pts

def _mask(poly,X,Y):
    return Path(poly).contains_points(np.c_[X.ravel(),Y.ravel()]).reshape(X.shape)

COUNTERS={'balcao_recepcao','armario_baixo_240','bancada_160','bancada_pia_200','bancada_pia_220','lavatorio_60','mesa_escritorio_140'}
def validate(items,doors,windows):
    issues=[]; log=[]
    # 1) planta cabe em 10x20 e ambientes sem sobreposição
    for k,(x0,y0,x1,y1) in RECT.items():
        if x0<15 or y0<15 or x1>985 or y1>1985: issues.append(f'ambiente fora do imóvel: {k}')
    keys=list(RECT)
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            A,B=RECT[a],RECT[b]
            if min(A[2],B[2])-max(A[0],B[0])>0.01 and min(A[3],B[3])-max(A[1],B[1])>0.01: issues.append(f'ambientes sobrepostos: {a} x {b}')
    log.append(f'Ambientes: {len(RECT)}; nenhum fora dos limites internos 15..985 x 15..1985 cm; sobreposições entre ambientes: {sum(1 for s in issues if "sobrepostos" in s)}')
    # 2) móveis dentro do ambiente
    fps=[]
    for it in items:
        if it['kind']=='light': continue
        fp=footprint(it); xs=[p[0] for p in fp]; ys=[p[1] for p in fp]
        r=RECT[it['room']]
        if min(xs)<r[0]-0.6 or max(xs)>r[2]+0.6 or min(ys)<r[1]-0.6 or max(ys)>r[3]+0.6:
            issues.append(f"fora do ambiente: {it['name']} ({it['model']}) em {it['room']}: x[{min(xs):.0f},{max(xs):.0f}] y[{min(ys):.0f},{max(ys):.0f}] vs {r}")
        fps.append((it,fp))
    # 3) sobreposição móvel x móvel (com faixa de elevação)
    def rng(it): return it['elev'],it['elev']+it['H']
    for i,(a,fa) in enumerate(fps):
        Pa=Path(fa)
        for b,fb in fps[i+1:]:
            if a['room']!=b['room']: continue
            (a0,a1),(b0,b1)=rng(a),rng(b)
            if min(a1,b1)-max(a0,b0)<=0.5: continue
            if (a['elev']>=70 and b['model'] in COUNTERS) or (b['elev']>=70 and a['model'] in COUNTERS): continue
            xa=[p[0] for p in fa]; ya=[p[1] for p in fa]; xb=[p[0] for p in fb]; yb=[p[1] for p in fb]
            ox=min(max(xa),max(xb))-max(min(xa),min(xb)); oy=min(max(ya),max(yb))-max(min(ya),min(yb))
            if ox>1.0 and oy>1.0: issues.append(f"sobreposição: {a['name']} x {b['name']} em {a['room']} (ox={ox:.1f}, oy={oy:.1f})")
    # 4) portas: varredura livre
    for d in doors:
        secs=door_sector(d); secs=secs if isinstance(secs[0],list) else [secs]
        for sec in secs:
            P=Path(sec)
            for it,fp in fps:
                if it['elev']>150: continue
                xs=[p[0] for p in fp]; ys=[p[1] for p in fp]
                gx,gy=np.meshgrid(np.linspace(min(xs),max(xs),12),np.linspace(min(ys),max(ys),12))
                inside=Path(fp).contains_points(np.c_[gx.ravel(),gy.ravel()])
                pts=np.c_[gx.ravel(),gy.ravel()][inside]
                if len(pts) and P.contains_points(pts).any(): issues.append(f"porta {d['id']} bate em: {it['name']} ({it['room']})")
    # 5) portas x portas
    ds=[(d,door_sector(d)) for d in doors]
    for i,(a,sa) in enumerate(ds):
        for b,sb in ds[i+1:]:
            sa_=sa if isinstance(sa[0],list) else [sa]; sb_=sb if isinstance(sb[0],list) else [sb]
            for A in sa_:
                for B in sb_:
                    gx,gy=np.meshgrid(np.linspace(min(p[0] for p in A),max(p[0] for p in A),40),np.linspace(min(p[1] for p in A),max(p[1] for p in A),40))
                    pts=np.c_[gx.ravel(),gy.ravel()]; pts=pts[Path(A).contains_points(pts)]
                    if len(pts) and Path(B).contains_points(pts).any(): issues.append(f"varreduras se cruzam: {a['id']} x {b['id']}")
    # 6) portas/janelas dentro de paredes (vão na parede, sem sair do ambiente)
    log.append(f'Portas: {len(doors)}; janelas: {len(windows)}')
    return issues,log
