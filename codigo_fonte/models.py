import math
from lib_geom import Mesh
REG={}   # name -> dict(mesh, cat, desc)
def reg(name,cat,desc,mesh): REG[name]=dict(mesh=mesh,cat=cat,desc=desc)

def maca():
    m=Mesh(); m.b(0,0,0,100,6,46,'branco_quente'); m.b(0,6,0,22,48,22,'inox')
    m.b(0,54,0,170,8,55,'branco_quente'); m.b(-17,62,0,155,10,65,'estofado_nude')
    h=Mesh().b(0,0,0,36,10,65,'estofado_nude'); m.add(h,rz=12,px=-18,py=0,pz=0,tx=0,ty=0,tz=0)  # placeholder rotated
    m2=Mesh(); m2.b(78,62,0,35,10,65,'estofado_nude'); m.p=[q for q in m.p]  # keep
    m.b(0,62,0,190,0.5,66,'champagne') if False else None
    m.b(-95+2,58,0,2,5,58,'champagne'); m.b(95-2,58,0,2,5,58,'champagne')
    return m
def maca_v2():
    m=Mesh(); m.b(0,0,0,100,6,46,'branco_quente'); m.b(0,6,0,22,48,22,'inox')
    m.b(0,54,0,170,8,55,'branco_quente'); m.b(-17,62,0,155,10,65,'estofado_nude')
    head=Mesh().b(0,0,0,36,10,65,'estofado_nude'); m.add(head,rz=10,px=0,py=0,pz=0,tx=77,ty=62,tz=0)
    m.b(-30,58,-30,2,4,2,'champagne')
    return m
reg('maca_profissional','maca','Maca estética profissional (190x65)',maca_v2())

def mocho():
    m=Mesh(); m.cy0(0,0,0,26,3,'inox'); m.cy0(0,3,0,3,45,'inox'); m.cy0(0,48,0,19,9,'estofado_nude'); return m
reg('mocho','maca','Mocho giratório',mocho())

def carrinho(W=55,D=40,H=85):
    m=Mesh()
    for sx in(-1,1):
        for sz in(-1,1):
            m.cy0(sx*(W/2-3),0,sz*(D/2-3),1.2,H,'champagne',n=8); m.cyl(sx*(W/2-3),3,sz*(D/2-3),3,3,'preto','x',8)
    for y in(12,45,H-2): m.b(0,y,0,W,2,D,'branco_quente')
    m.b(-10,47,0,14,8,12,'marsala'); m.cy0(12,47,2,3,10,'champagne',n=8); m.b(-8,H,0,20,4,14,'nude')
    return m
reg('carrinho_auxiliar','maca','Carrinho auxiliar 3 prateleiras',carrinho())

def armario_alto(W,Hh=200):
    m=Mesh(); m.b(0,0,0,W,Hh,45,'madeira',escala_textura=100); n=max(1,round(W/50)); dw=W/n
    for i in range(n):
        x=-W/2+dw*(i+.5); m.b(x,4,22.5+0.75,dw-1.5,Hh-8,1.5,'branco_quente'); m.b(x+(dw/2-6)*(1 if i%2==0 else -1),Hh/2-15,24.5,1.6,30,1.2,'champagne')
    return m
for w in(60,80,100,120): reg(f'armario_alto_{w}','armarios',f'Armário alto {w} cm',armario_alto(w))

def armario_baixo(W,Hh=75,D=40):
    m=Mesh(); m.b(0,0,0,W,Hh-3,D,'madeira',escala_textura=100)
    m.b(0,Hh-3,0,W+1,3,D+1,'marmore',escala_textura=100); n=max(2,round(W/60)); dw=W/n
    for i in range(n):
        x=-W/2+dw*(i+.5); m.b(x,4,D/2+0.75,dw-1.5,Hh-10,1.5,'nude'); m.b(x+(dw/2-6),Hh-20,D/2+1.8,1.2,14,1.2,'champagne')
    return m
reg('armario_baixo_240','armarios','Armário inferior de recepção 240',armario_baixo(240))

def bancada(W,D=60,Hh=90,pia=False,name=None):
    m=Mesh(); m.b(0,0,0,W,Hh-4,D-2,'madeira',escala_textura=100); n=max(2,round(W/60)); dw=W/n
    for i in range(n):
        x=-W/2+dw*(i+.5); m.b(x,4,D/2-1+0.75,dw-1.5,Hh-12,1.5,'branco_quente'); m.b(x+(dw/2-6),Hh-22,D/2+0.3,1.2,12,1.2,'champagne')
    m.b(0,Hh-4,0,W+2,4,D,'marmore',escala_textura=100); m.b(0,Hh,-D/2+1,W,8,2,'marmore',escala_textura=100)
    if pia:
        x=W*0.18; m.b(x,Hh-3.5,2,42,0.8,34,'inox'); m.cy0(x,Hh,-D/2+9,1.5,20,'champagne',n=8); m.b(x,Hh+18,-D/2+16,2.2,2.2,14,'champagne')
    return m
reg('bancada_160','armarios','Bancada 160x50',bancada(160,50)); reg('bancada_pia_200','armarios','Bancada com pia 200x60',bancada(200,60,pia=True))
reg('bancada_pia_220','armarios','Bancada com pia 220x60',bancada(220,60,pia=True))
reg('lavatorio_60','banheiros','Lavatório com gabinete 60x45',bancada(60,45,85,pia=True))

def lixeira():
    m=Mesh(); m.cy0(0,0,0,12,30,'inox',n=14); m.cy0(0,30,0,12.5,2,'preto',n=14); return m
reg('lixeira','decoracao','Lixeira com tampa',lixeira())

def espelho_ret(W,Hh):
    m=Mesh(); m.b(0,0,0,W,Hh,3,'champagne'); m.b(0,2.5,1.6,W-5,Hh-5,0.6,'espelho'); return m
for (w,h) in((100,90),(120,90),(140,90),(60,80)): reg(f'espelho_{w}x{h}','decoracao',f'Espelho {w}x{h}',espelho_ret(w,h))
def espelho_red(D=100):
    m=Mesh(); m.cyl(0,D/2,0,D/2,3,'champagne','z',32); m.cyl(0,D/2,1.7,D/2-2.5,0.6,'espelho','z',32); return m
reg('espelho_redondo_100','decoracao','Espelho redondo Ø100 moldura champagne',espelho_red())

def planta(big=True):
    m=Mesh()
    if big:
        m.cy0(0,0,0,18,40,'terracota',n=14,r2=15)
        offs=[(0,95,0,11,38),(9,120,4,10,30),(-9,110,-5,10,34),(5,75,-9,9,26),(-8,72,8,9,26),(0,140,0,8,24),(10,95,-8,8,26),(-11,92,3,8,28)]
        for x,y,z,r,hh in offs: m.sph(x,y,z,r,hh,r,'verde'); 
        m.cy0(0,38,0,1.2,80,'marrom_claro',n=6)
    else:
        m.cy0(0,0,0,9,15,'branco_quente',n=12,r2=8)
        for x,y,z in((0,26,0),(5,22,3),(-5,22,-3)): m.sph(x,y,z,6,10,6,'verde_claro',n=10,k=6)
    return m
reg('planta_grande','decoracao','Planta ornamental em vaso terracota',planta(True)); reg('planta_pequena','decoracao','Planta pequena',planta(False))
def vaso():
    m=Mesh(); m.cy0(0,0,0,6,22,'ceramica',n=12,r2=4)
    for x,z,a in((0,0,0),(3,1,12),(-3,-1,-12)): m.add(Mesh().cy0(0,0,0,0.4,38,'marrom_claro',n=5),rz=a,tx=x,ty=22,tz=z)
    m.sph(0,60,0,4,3,4,'nude',n=8,k=5); m.sph(6,55,1,3,3,3,'terracota',n=8,k=5); m.sph(-6,55,-1,3,3,3,'nude',n=8,k=5); return m
reg('vaso_decor','decoracao','Vaso decorativo com ramos',vaso())
def quadro():
    m=Mesh(); m.b(0,0,0,80,60,3,'champagne'); m.b(0,2,1.6,76,56,0.6,'branco_quente')
    m.b(-14,8,2.0,28,44,0.5,'marsala'); m.b(14,8,2.0,28,26,0.5,'terracota'); m.b(14,36,2.0,28,16,0.5,'nude'); return m
reg('quadro_abstrato','decoracao','Quadro abstrato 80x60',quadro())

def ripado(W,Hh):
    m=Mesh(); m.b(0,0,-1.6,W,Hh,0.8,'madeira_escura'); n=int(W//7); x0=-(n*7-2)/2
    for i in range(n): m.b(x0+i*7+2.5,0,0.4,5,Hh,3.2,'madeira')
    return m
for (w,h) in((400,260),(150,260)): reg(f'painel_ripado_{w}x{h}','decoracao',f'Painel ripado de madeira {w}x{h}',ripado(w,h))
def painel_logo():
    m=Mesh(); m.b(0,0,0,224,250,4,'marsala'); m.b(-131,0,0,38,250,4,'madeira_escura')
    m.b(131,0,0,38,250,4,'madeira_escura')
    for sx in(-1,1):
        for i in range(5): m.b(sx*131+(i-2)*7,0,2.6,5,250,2.4,'madeira')
    m.bb(-115,-3,-2,115,0,0,'led'); m.bb(-115,250,-2,115,253,0,'led'); m.bb(-115,0,-2,-112,250,0,'led'); m.bb(112,0,-2,115,250,0,'led')
    m.b(0,0,4.1,224,1.2,0.6,'champagne'); m.b(0,248.8,4.1,224,1.2,0.6,'champagne'); return m
reg('painel_logo','recepcao','Painel do logotipo (marsala + ripado + LED)',painel_logo())

def letreiro():
    m=Mesh(); t=4.5; z0,z1=0,3; hh=30; gm='dourado'
    def L(x):
        m.stroke(x+t/2,0,x+t/2,hh,t,z0,z1,gm); m.stroke(x,t/2,x+20,t/2,t,z0,z1,gm); return 20
    def U(x,acc=True):
        w=26; r=(w-t)/2; cx=x+w/2; cyc=r+t/2
        m.stroke(x+t/2,hh,x+t/2,cyc,t,z0,z1,gm); m.stroke(x+w-t/2,hh,x+w-t/2,cyc,t,z0,z1,gm)
        pts=[(cx-r*math.cos(math.pi*i/8),cyc-r*math.sin(math.pi*i/8)) for i in range(9)]
        for a,b in zip(pts,pts[1:]): m.stroke(a[0],a[1],b[0],b[1],t,z0,z1,gm)
        if acc: m.stroke(cx-3,hh+5,cx+4,hh+11,3,z0,z1,gm)
        return w
    def M(x):
        w=34; m.stroke(x+t/2,0,x+t/2,hh,t,z0,z1,gm); m.stroke(x+w-t/2,0,x+w-t/2,hh,t,z0,z1,gm)
        m.stroke(x+t/2,hh-2,x+w/2,9,t,z0,z1,gm); m.stroke(x+w-t/2,hh-2,x+w/2,9,t,z0,z1,gm); return w
    def I(x): m.stroke(x+t/2,0,x+t/2,hh,t,z0,z1,gm); return 6
    def N(x):
        w=28; m.stroke(x+t/2,0,x+t/2,hh,t,z0,z1,gm); m.stroke(x+w-t/2,0,x+w-t/2,hh,t,z0,z1,gm); m.stroke(x+t/2,hh-2,x+w-t/2,2,t,z0,z1,gm); return w
    def A(x):
        w=30; m.stroke(x+2,0,x+w/2,hh,t,z0,z1,gm); m.stroke(x+w-2,0,x+w/2,hh,t,z0,z1,gm); m.stroke(x+8,9,x+w-8,9,3.5,z0,z1,gm); return w
    x=0
    for f in (L,U,M,I,N,A): x+=f(x)+9
    return m
reg('letreiro_lumina','recepcao','Letras 3D LÚMINA em dourado fosco',letreiro())

def balcao():
    m=Mesh(); m.b(0,0,22.5,240,102,25,'marsala'); m.b(0,102,22.5,240,3,27,'marmore')
    m.b(0,0,-12.5,240,72,45,'madeira'); m.b(0,72,-12.5,240,3,45,'marmore')
    m.b(0,55,35.2,236,1.5,0.6,'champagne'); m.b(0,3,35.2,236,1.5,0.6,'champagne')
    m.b(0,0,10.2,238,0,0.1,'madeira') if False else None
    return m
reg('balcao_recepcao','recepcao','Balcão de recepção 240 (marsala + mármore)',balcao())
def cadeira_atend():
    m=Mesh(); m.cy0(0,0,0,26,3,'inox',n=10); m.cy0(0,3,0,3,38,'inox',n=8); m.b(0,41,0,48,7,46,'marsala_tecido'); m.b(0,48,-21,46,38,5,'marsala_tecido'); return m
reg('cadeira_atendimento','recepcao','Cadeira giratória de atendimento',cadeira_atend())
def monitor():
    m=Mesh(); m.cy0(0,0,0,12,1.5,'preto',n=12); m.b(0,1.5,0,4,16,3,'preto'); m.b(0,15,0,55,32,2.5,'preto'); m.b(0,16.5,1.3,52,29,0.3,'tela'); return m
reg('monitor','equipamentos','Monitor 24"',monitor())
reg('teclado','equipamentos','Teclado',Mesh().b(0,0,0,42,2,14,'branco'))
def impressora():
    m=Mesh(); m.b(0,0,0,40,16,34,'branco'); m.b(0,16,-4,34,8,22,'cinza'); m.b(0,3,17.1,30,1.5,0.3,'preto'); return m
reg('impressora','equipamentos','Impressora',impressora())
def mesa_esc():
    m=Mesh(); m.b(0,72,0,140,3,70,'madeira'); m.b(-66,0,0,3,72,64,'madeira_escura'); m.b(66,0,0,3,72,64,'madeira_escura'); m.b(0,25,-30,130,45,2,'madeira_escura'); return m
reg('mesa_escritorio_140','consultorio','Mesa de consultório 140x70',mesa_esc())
def cadeira(col='tecido_bege',leg='dourado',H=85):
    m=Mesh()
    for sx in(-1,1):
        for sz in(-1,1): m.cy0(sx*20,0,sz*20,1.2,44,leg,n=6)
    m.b(0,44,0,46,5,46,col); m.b(0,49,-21,44,H-49,4,col); return m
reg('cadeira_visita','consultorio','Cadeira de visita',cadeira()); reg('cadeira_copa','copa','Cadeira da copa',cadeira('madeira','madeira_escura'))

def sofa4():
    m=Mesh()
    for sx in(-1,1):
        for sz in(-1,1): m.cy0(sx*112,0,sz*38,2,10,'dourado',n=8)
    m.b(0,10,0,240,20,90,'tecido_bege')
    for i in range(4): m.b(-90+i*60,30,6,58,12,72,'tecido_bege')
    m.b(0,30,-37,240,45,16,'tecido_bege'); m.b(-114,30,0,12,32,90,'tecido_bege'); m.b(114,30,0,12,32,90,'tecido_bege')
    for x in(-90,90): m.b(x,42,-20,40,32,12,'marsala_tecido')
    return m
reg('sofa_4_lugares','espera','Sofá 4 lugares (240x90)',sofa4())
def sofa2():
    m=Mesh(); m.b(0,8,0,150,18,80,'tecido_bege'); m.b(0,26,-32,150,38,16,'tecido_bege')
    for i in range(2): m.b(-37+i*74,26,6,72,12,62,'tecido_bege')
    m.b(-69,26,0,12,28,80,'tecido_bege'); m.b(69,26,0,12,28,80,'tecido_bege')
    for sx in(-1,1):
        for sz in(-1,1): m.cy0(sx*68,0,sz*34,2,8,'dourado',n=8)
    return m
reg('sofa_2_lugares','funcionarios','Sofá 2 lugares (descanso)',sofa2())
def poltrona(col='marsala_tecido'):
    m=Mesh()
    for sx in(-1,1):
        for sz in(-1,1): m.cy0(sx*34,0,sz*34,2,14,'dourado',n=8)
    m.b(0,14,0,80,18,80,col); m.b(0,32,6,60,12,66,col); m.b(0,32,-34,80,46,12,col); m.b(-34,32,4,12,24,70,col); m.b(34,32,4,12,24,70,col); return m
reg('poltrona_marsala','espera','Poltrona marsala',poltrona())
def poltrona_dren():
    m=poltrona('nude'); return m
reg('poltrona_drenagem','salas','Poltrona nude (drenagem)',poltrona_dren())
def mesa_centro():
    m=Mesh(); m.cy0(0,0,0,26,2,'dourado',n=20); m.cy0(0,2,0,6,33,'dourado',n=10); m.cy0(0,35,0,40,3,'marmore',n=28); return m
reg('mesa_centro_redonda','espera','Mesa de centro redonda Ø80',mesa_centro())
def mesa_lateral():
    m=Mesh(); m.cy0(0,0,0,16,2,'dourado',n=14); m.cy0(0,2,0,2.5,48,'dourado',n=8); m.cy0(0,50,0,22.5,3,'marmore',n=20); return m
reg('mesa_lateral','espera','Mesa lateral',mesa_lateral())
def abajur():
    m=Mesh(); m.cy0(0,0,0,7,2,'dourado',n=10); m.cy0(0,2,0,1.2,20,'dourado',n=6); m.cy0(0,20,0,13,20,'branco_quente',n=14,r2=9); return m
reg('abajur','espera','Abajur',abajur())

def ultraformer():
    m=Mesh()
    for sx in(-1,1):
        for sz in(-1,1): m.cyl(sx*23,4,sz*24,4,4,'preto','x',10)
    m.b(0,6,0,50,4,56,'inox'); m.b(0,10,0,46,78,52,'branco_quente'); m.b(0,34,26.1,44,10,0.6,'marsala'); m.b(0,58,26.1,44,1.5,0.6,'champagne')
    m.b(0,88,-4,46,18,42,'branco_quente'); scr=Mesh().b(0,0,0,36,26,2.5,'preto'); scr2=Mesh().b(0,1.5,1.4,33,23,0.3,'tela')
    m.add(scr,rx=-22,tx=0,ty=108,tz=6); m.add(scr2,rx=-22,tx=0,ty=108,tz=6)
    m.b(28,68,0,8,18,16,'cinza'); m.cyl(31,78,0,3.2,18,'branco','z',10); m.cyl(31,78,10,2.2,3,'champagne','z',10)
    for i in range(6): m.b(30,64-i*8,-2,1.5,8,1.5,'preto')
    return m
reg('ultraformer','ultraformer','Ultraformer (modelo ilustrativo)',ultraformer())
def lavieen():
    m=Mesh()
    for sx in(-1,1):
        for sz in(-1,1): m.cyl(sx*21,4,sz*26,4,4,'preto','x',10)
    m.b(0,6,0,46,4,58,'inox'); m.b(0,10,0,44,66,54,'branco_quente'); m.b(0,30,27.1,42,8,0.6,'marsala')
    m.b(0,76,-4,44,16,44,'branco_quente'); s=Mesh().b(0,0,0,28,18,2.5,'preto'); m.add(s,rx=-20,tx=0,ty=92,tz=10)
    m.cy0(-14,76,-16,3.5,40,'inox',n=10); m.b(-14,114,-6,4,4,24,'inox')
    m.add(Mesh().b(0,0,0,4,4,26,'branco_quente'),rx=35,px=0,py=0,pz=0,tx=-14,ty=112,tz=8)
    m.cyl(-14,104,20,3.5,16,'branco','z',10); m.cyl(-14,104,29,2.5,3,'champagne','z',10)
    return m
reg('lavieen','lavieen','Lavieen laser (modelo ilustrativo)',lavieen())
def vaporizador():
    m=Mesh(); m.cy0(0,0,0,26,4,'branco',n=12); m.cy0(0,4,0,2.5,100,'inox',n=8); m.cy0(0,100,0,9,12,'branco',n=14)
    m.b(0,108,12,3,3,26,'inox'); m.cyl(0,109.5,26,4,5,'champagne','z',10); return m
reg('vaporizador_ozonio','equipamentos','Vaporizador/ozônio para limpeza de pele',vaporizador())
def lupa():
    m=Mesh(); m.cy0(0,0,0,20,3,'branco',n=12); m.cy0(0,3,0,1.5,105,'inox',n=8); m.b(0,105,10,3,3,24,'inox')
    m.cyl(0,108,24,14,4,'branco','z',20); m.cyl(0,108,26.3,11,0.6,'vidro','z',20); return m
reg('lupa_luminaria','equipamentos','Lupa com luz de bancada',lupa())
def cart_limp():
    m=carrinho(60,45,85)
    m.b(-12,87,0,30,14,22,'branco'); m.b(-12,99,0,26,1.5,18,'tela'); m.cy0(12,87,4,3,10,'champagne',n=8); m.b(18,87,-6,14,6,10,'marsala'); return m
reg('cart_limpeza_pele','equipamentos','Carrinho com equipamentos de limpeza de pele',cart_limp())
def materiais():
    m=Mesh(); m.b(0,0,0,32,1.5,22,'branco_quente')
    for x,mt in((-10,'marsala'),(-4,'ceramica'),(2,'champagne'),(8,'nude')): m.cy0(x,1.5,-4,2.6,12,mt,n=8)
    m.b(4,1.5,6,14,4,8,'caixa'); return m
reg('conjunto_materiais','equipamentos','Materiais de apoio (frascos e bandeja)',materiais())

def luz_spot():
    m=Mesh(); m.cy0(0,0,0,6.5,1.2,'branco',n=14); m.cy0(0,0,0,5,0.6,'led',n=14); return m
reg('spot_embutido','iluminacao','Spot LED embutido',luz_spot())
def spot_dir():
    m=Mesh(); m.cy0(0,10,0,6,3,'branco',n=12); m.cyl(0,4,0,5,12,'branco','x',12) ; m.cy0(0,0,0,4.5,1,'led',n=12); return m
reg('spot_direcionavel','iluminacao','Spot direcionável',spot_dir())
reg('painel_led_60','iluminacao','Painel LED técnico 60x60',Mesh().b(0,0,0,60,3,60,'branco').b(0,0,0,56,0.6,56,'led_neutro'))
def pendente():
    m=Mesh(); m.cy0(0,70,0,0.4,30,'preto',n=5); m.cy0(0,40,0,13,30,'dourado',n=16,r2=6); m.cy0(0,39,0,11,1,'led',n=14); m.cy0(0,100,0,4,1,'dourado',n=10); return m
reg('pendente_dourado','iluminacao','Pendente decorativo dourado',pendente())
reg('fita_led_400','iluminacao','Fita LED indireta 400',Mesh().b(0,0,0,400,1.5,1.5,'led'))
reg('fita_led_v','iluminacao','Fita LED vertical 250',Mesh().b(0,0,0,1.5,250,1.5,'led'))
reg('fita_led_h','iluminacao','Fita LED horizontal 240',Mesh().b(0,0,0,240,1.5,1.5,'led'))

def porta(W,D,Hh=210,name=None,kind='wood'):
    m=Mesh(); fr='branco_quente'; t=4
    m.b(-W/2+t/2,0,0,t,Hh,D,fr); m.b(W/2-t/2,0,0,t,Hh,D,fr); m.b(0,Hh-t,0,W,t,D,fr)
    m.b(0,0,0,W-2*t,Hh-t,3.5,'madeira_porta'); m.b(W/2-t-6,95,3,1.4,14,1.2,'champagne')
    m.b(0,90,1.9,W-2*t-6,0.6,0.4,'champagne') if False else None
    return m
reg('porta_80','portas','Porta interna 80x210',porta(80,10)); reg('porta_90','portas','Porta 90x210',porta(90,10))
def porta_servico():
    m=porta(90,15); return m
reg('porta_servico_90','portas','Porta de serviço 90x210',porta_servico())
def porta_principal():
    W,D,Hh=120,15,220; m=Mesh(); fr='marsala'; t=5
    m.b(-W/2+t/2,0,0,t,Hh,D,fr); m.b(W/2-t/2,0,0,t,Hh,D,fr); m.b(0,Hh-t,0,W,t,D,fr)
    for sx in(-1,1):
        m.b(sx*(W/4),0,0,W/2-t-1,Hh-t,2.5,'esquadria'); m.b(sx*(W/4),3,0.3,W/2-t-6,Hh-t-8,0.6,'vidro'); m.b(sx*4,90,3,2,60,2,'champagne')
    return m
reg('porta_principal_120','portas','Porta principal dupla 120x220 vidro',porta_principal())
def janela(W,Hh,D):
    m=Mesh(); t=4; fr='esquadria'
    m.b(0,0,0,W,t,D,fr); m.b(0,Hh-t,0,W,t,D,fr); m.b(-W/2+t/2,0,0,t,Hh,D,fr); m.b(W/2-t/2,0,0,t,Hh,D,fr)
    nm=max(1,round(W/100))
    for i in range(1,nm): m.b(-W/2+W*i/nm,0,0,t,Hh,D,fr)
    m.b(0,t,0,W-2*t,Hh-2*t,0.6,'vidro'); return m
JAN=[(250,170),(300,150),(160,150),(110,120),(140,120),(60,50),(80,60),(100,140),(140,140),(100,100),(160,130),(140,130)]
for (w,h) in JAN:
    reg(f'janela_{w}x{h}','portas',f'Janela {w}x{h}',janela(w,h,15))

def vaso_san():
    m=Mesh(); m.b(0,0,10,20,15,30,'ceramica'); m.sph(0,28,8,19,17,29,'ceramica',n=14,k=8); m.b(0,30,-27,38,42,14,'ceramica')
    m.cy0(0,72,-27,3,1.5,'champagne',n=10); m.sph(0,47,8,18,2,26,'branco',n=14,k=4); return m
reg('vaso_sanitario','banheiros','Vaso sanitário com caixa acoplada',vaso_san())
def lav_pne():
    m=Mesh(); m.b(0,68,0,55,12,45,'ceramica'); m.cy0(0,80,-14,1.5,14,'champagne',n=8); m.b(0,92,-8,2,2,12,'champagne'); m.cy0(0,30,-16,2.5,38,'inox',n=8); return m
reg('lavatorio_pne','banheiros','Lavatório suspenso acessível',lav_pne())
reg('dispenser_sabonete','banheiros','Dispenser de sabonete',Mesh().b(0,0,0,10,20,9,'branco').b(0,16,5,2,3,4,'champagne'))
reg('dispenser_papel','banheiros','Dispenser de papel toalha',Mesh().b(0,0,0,28,30,11,'branco').b(0,3,5.6,20,2,0.4,'champagne'))
def barra(L):
    m=Mesh(); m.cyl(0,2.5,0,1.9,L,'inox','x',10)
    for s in(-1,1): m.cyl(s*(L/2-4),2.5,-1.5,2.6,3,'inox','z',10)
    return m
reg('barra_apoio_80','banheiros','Barra de apoio 80 cm',barra(80)); reg('barra_apoio_70','banheiros','Barra de apoio 70 cm',barra(70))
def tanque():
    m=Mesh(); m.b(0,0,0,58,62,46,'branco_quente'); m.b(0,62,0,60,28,50,'ceramica'); m.b(0,72,0,50,1,40,'inox')
    m.cy0(0,90,-20,1.5,18,'champagne',n=8); m.b(0,106,-14,2.2,2.2,12,'champagne'); return m
reg('tanque_dml','dml','Tanque/pia de serviço',tanque())
def prateleira(W,D,Hh,n,name,cat,boxes=False):
    m=Mesh()
    for s in(-1,1): m.b(s*(W/2-1.5),0,0,3,Hh,D,'inox')
    m.b(0,0,-D/2+0.5,W,Hh,1,'inox') if False else None
    for i in range(n): m.b(0,8+i*(Hh-14)/(n-1),0,W,2.5,D,'madeira')
    if boxes:
        cols=['caixa','bege','areia','nude']; k=0
        for i in range(n-1):
            y=8+2.5+i*(Hh-14)/(n-1); x=-W/2+8
            while x<W/2-30:
                w=22+(k*7)%14; hh=16+(k*5)%12; m.b(x+w/2,y,0,w,hh,D-8,cols[k%4]); x+=w+4+(k*3)%6; k+=1
    reg(name,cat,name.replace('_',' ').capitalize(),m)
prateleira(180,35,200,5,'prateleiras_dml','dml'); prateleira(360,40,200,5,'estante_deposito_360','deposito',True); prateleira(160,40,200,5,'estante_deposito_160','deposito',True)
def balde():
    m=Mesh(); m.cy0(0,0,0,13,25,'terracota',n=12,r2=15); m.add(Mesh().cy0(0,0,0,1,120,'madeira',n=6),rz=8,tx=4,ty=10,tz=0); m.b(6,100,0,18,6,12,'cinza'); return m
reg('balde_e_rodo','dml','Balde e rodo',balde())
def caixas():
    m=Mesh(); m.b(-12,0,0,34,26,38,'caixa'); m.b(20,0,0,26,20,34,'bege'); m.b(-12,26,0,30,22,32,'areia'); return m
reg('caixas_empilhadas','deposito','Caixas de insumos',caixas())
def rack():
    m=Mesh(); m.b(0,0,0,55,180,60,'preto'); m.b(0,4,30.3,46,172,0.5,'tela')
    for i in range(6): m.b(0,20+i*24,30.8,40,2,0.3,'led')
    return m
reg('rack_ti','tecnica','Rack de TI/rede',rack())
reg('quadro_eletrico','tecnica','Quadro elétrico',Mesh().b(0,0,0,40,60,12,'branco').b(0,4,6.2,34,52,0.4,'cinza'))
def lockers():
    m=Mesh(); m.b(0,0,0,200,190,45,'madeira'); 
    for i in range(5): m.b(-80+i*40,4,23.2,38,182,1.4,'terracota'); m.b(-80+i*40+12,100,24.2,1.4,12,1,'champagne')
    return m
reg('armario_vestiario_200','funcionarios','Armário tipo vestiário 5 portas',lockers())
def frigobar():
    m=Mesh(); m.b(0,0,0,50,85,50,'inox'); m.b(0,40,25.2,48,1,0.3,'preto'); m.b(20,50,25.6,1.5,20,1.2,'preto'); return m
reg('frigobar','copa','Frigobar',frigobar())
def micro():
    m=Mesh(); m.b(0,0,0,46,27,35,'inox'); m.b(-5,4,17.6,28,19,0.4,'preto'); m.b(16,4,17.6,8,19,0.4,'cinza'); return m
reg('microondas','copa','Micro-ondas',micro())
def aereo(W):
    m=Mesh(); m.b(0,0,0,W,70,35,'madeira'); n=max(2,round(W/60)); dw=W/n
    for i in range(n): m.b(-W/2+dw*(i+.5),3,17.5+0.75,dw-1.5,64,1.5,'branco_quente'); m.b(-W/2+dw*(i+.5)+(dw/2-6),8,19.5,1.2,14,1.2,'champagne')
    return m
reg('armario_aereo_170','copa','Armário aéreo 170',aereo(170))
def mesa_copa():
    m=Mesh(); m.cy0(0,0,0,22,2,'madeira_escura',n=16); m.cy0(0,2,0,4,70,'madeira_escura',n=8); m.cy0(0,72,0,35,3,'madeira',n=24); return m
reg('mesa_copa_redonda','copa','Mesa redonda Ø70',mesa_copa())
