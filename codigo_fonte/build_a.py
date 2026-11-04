import os, math, zipfile, shutil, random
import numpy as np
from PIL import Image, ImageFilter
from xml.sax.saxutils import quoteattr
import lib_geom as G
from lib_geom import Mesh, MATS, H as HEX
import layout as L
from models import REG

OUT=os.environ.get('LUMINA_OUT') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
for sub in ['projeto','texturas','planta','renders','modelos']: os.makedirs(f'{OUT}/{sub}',exist_ok=True)
ITEMS=L.build_items(); DOORS=L.build_doors(); WINDOWS=L.build_windows()

# ---------------- paredes: divisão e cores ----------------
ROOMCOL={'recepcao':'F1E8DA','espera':'EAD9C6','circulacao':'EBDCCB','ramal':'EBDCCB','consultorio':'F3EBDF','botox':'F4EEE4','peeling':'F4EEE4',
 'drenagem':'EBD5C2','deposito':'F1ECE3','banheiro_clientes':'E3CDB4','banheiro_acessivel':'E3CDB4','dml':'F2EDE4','copa':'E9D8C0','tecnologia':'F1EADF',
 'descanso':'EBD9C7','area_tecnica':'F0ECE4'}
EXT='DDCDB6'; FRONT='CF9A7A'; MARSALA='7A2E3A'; WOOD='B98A5B'
def room_at(x,y):
    for k,(x0,y0,x1,y1) in L.RECT.items():
        if x0-0.01<=x<=x1+0.01 and y0-0.01<=y<=y1+0.01: return k
    return None
def side_color(seg,px,py,nx,ny):
    kind=seg[5]
    k=room_at(px,py)
    if kind=='div': return MARSALA if ny>0 or True and (px<420) else WOOD
    if k is None: 
        return FRONT if (seg[1]>1900 and seg[3]>1900) else EXT
    if k=='recepcao' and ny>0 and abs(seg[1]-1630)<1 and seg[0]<420: return MARSALA
    if k=='drenagem' and ny>0 and abs(seg[1]-260)<1 and False: return 'D9A98C'
    return ROOMCOL[k]
def split_walls():
    segs=[]
    for wi,w in enumerate(L.BASE_WALLS):
        xs,ys,xe,ye,t,kind=w; horiz=abs(ys-ye)<1e-6
        a0,a1=(xs,xe) if horiz else (ys,ye); lo,hi=min(a0,a1),max(a0,a1); fixed=ys if horiz else xs
        cuts=set()
        for wj,o in enumerate(L.BASE_WALLS):
            if wj==wi: continue
            for (px,py) in ((o[0],o[1]),(o[2],o[3])):
                perp=py if horiz else px; along=px if horiz else py
                if abs(perp-fixed)<=t/2+0.5 and lo+0.5<along<hi-0.5: cuts.add(round(along,2))
        pts=sorted(set([lo,hi]+list(cuts)))
        if a0>a1: pts=pts[::-1]
        for p,q in zip(pts,pts[1:]):
            s=(p,fixed,q,fixed) if horiz else (fixed,p,fixed,q)
            dx,dy=s[2]-s[0],s[3]-s[1]; Ln=math.hypot(dx,dy); nx,ny=dy/Ln,-dx/Ln
            mx,my=(s[0]+s[2])/2,(s[1]+s[3])/2; off=t/2+3
            lc=side_color(w,mx+nx*off,my+ny*off,nx,ny); rc=side_color(w,mx-nx*off,my-ny*off,-nx,-ny)
            segs.append(dict(x0=s[0],y0=s[1],x1=s[2],y1=s[3],t=t,kind=kind,left=lc,right=rc,base=wi))
    return segs
SEGS=split_walls()
for i,s in enumerate(SEGS): s['id']=f'wall{i}'
# junções do contorno externo
ext=[s for s in SEGS if s['kind']=='ext']
for i,s in enumerate(ext):
    s['prev']=ext[i-1]['id']; s['next']=ext[(i+1)%len(ext)]['id']

# ---------------- texturas ----------------
def tex_marble(path,base,vein,seed):
    rng=np.random.RandomState(seed); n=512
    def noise(scale):
        a=rng.rand(n//scale+2,n//scale+2); im=Image.fromarray((a*255).astype('uint8')).resize((n,n),Image.BICUBIC); return np.asarray(im)/255
    f=noise(64)*0.6+noise(32)*0.3+noise(8)*0.1
    x=np.linspace(0,1,n)[None,:]; y=np.linspace(0,1,n)[:,None]
    v=np.abs(np.sin((x*3.2+y*1.6+f*2.4)*math.pi*2)); v=np.clip(1-v*9,0,1)**2
    v2=np.abs(np.sin((x*1.1-y*2.8+f*3.1)*math.pi*2)); v2=np.clip(1-v2*14,0,1)**2*0.6
    img=np.zeros((n,n,3))
    for c in range(3): img[:,:,c]=base[c]*(0.94+0.06*f)+(vein[c]-base[c])*np.clip(v+v2,0,1)*0.55
    return img
def make_textures():
    T={}
    def save(name,img):
        im=Image.fromarray(np.clip(img*255,0,255).astype('uint8')); im.save(f'{OUT}/texturas/{name}.png'); T[name]=im
    # porcelanato areia (2x2 placas com rejunte)
    m=tex_marble('',HEX('DDCDB0'),HEX('C7B393'),3); g=m.copy(); n=512
    for k in (0,n//2): g[k:k+2,:]=HEX('B9A98C'); g[:,k:k+2]=HEX('B9A98C')
    g[-2:,:]=HEX('B9A98C'); g[:,-2:]=HEX('B9A98C'); save('porcelanato_areia',g)
    m=tex_marble('',HEX('E9E3D8'),HEX('D0C7B8'),8); g=m.copy()
    for k in (0,n//2): g[k:k+2,:]=HEX('C9C0B0'); g[:,k:k+2]=HEX('C9C0B0')
    g[-2:,:]=HEX('C9C0B0'); g[:,-2:]=HEX('C9C0B0'); save('porcelanato_claro',g)
    save('marmore_bege',tex_marble('',HEX('EDE6DA'),HEX('B79F82'),21))
    rng=np.random.RandomState(5); img=np.zeros((n,n,3)); base=np.array(HEX('B98A5B'))
    for i in range(0,n,32):
        sh=0.9+0.1*rng.rand(); col=base*sh; img[:,i:i+30]=col; img[:,i+30:i+32]=np.array(HEX('6E4A2C'))
    grain=rng.rand(n,n)*0.06; img=img*(1-grain[:,:,None]); save('madeira_ripada',img)
    for nm,hx in(('marsala_liso','7A2E3A'),('terracota','B8674A'),('areia_liso','E3D3B5')):
        base=np.array(HEX(hx)); noise=rng.rand(n,n)*0.04; save(nm,np.ones((n,n,3))*base*(1-noise[:,:,None]))
    return T
TEX=make_textures()
FLOORTEX={'areia':'porcelanato_areia','claro':'porcelanato_claro','marmore':'marmore_bege'}

# ---------------- ícones ----------------
def icon_for(name,polys,dimsv):
    w,h,d=dimsv; c=np.array([0,h/2,0]); dist=max(w,h,d)*2.6
    eye=c+np.array([0.9,0.7,1.15])*dist/1.6
    im=G.render(polys,eye,c,fov=32,size=(96,96),ss=2,bg=(0.94,0.92,0.9))
    return im
def model_export():
    files={}; icons={}
    for name,d in REG.items():
        polys,dm=d['mesh'].normalized()
        cat_dir={'maca':'maca','recepcao':'recepcao','ultraformer':'ultraformer','lavieen':'lavieen','armarios':'armarios','decoracao':'decoracao'}.get(d['cat'],d['cat'])
        folder=f'{OUT}/modelos/{cat_dir}/{name}'
        G.write_obj(polys,folder,name)
        G.write_obj_web(polys,f'{OUT}/modelos_web/{cat_dir}/{name}',name)   # OBJ em metros + normais + Tr (para web)
        d['dims']=tuple(round(float(v),1) for v in dm); d['folder']=folder; d['catdir']=cat_dir
        ic=icon_for(name,polys,dm); ic.save(f'{folder}/{name}_icone.png'); icons[name]=ic
        d['polys']=polys
    return icons
ICONS=model_export()

# ---------------- Home.xml ----------------
def hx(c): return 'FF'+c
def a(k,v): 
    if isinstance(v,float): v=('%.2f'%v)
    return f'{k}={quoteattr(str(v))}'
def piece_xml(tag,idn,name,model,x,y,elev,ang,W,D,Hh,extra='',inner='',movable=True):
    at=' '.join([a('id',idn),a('name',name),a('model',f'm/{model}/{model}.obj'),a('icon',f'i/{model}.png'),a('x',float(x)),a('y',float(y)),a('elevation',float(elev)),
        a('angle',float(ang)),a('width',float(W)),a('depth',float(D)),a('height',float(Hh)),a('movable','true' if movable else 'false'),a('visible','true'),a('nameVisible','false'),a('modelRotation','1 0 0 0 1 0 0 0 1'),a('backFaceShown','true')])
    return f"  <{tag} {at} {extra}>{inner}</{tag}>\n" if inner else f"  <{tag} {at} {extra}/>\n"
def build_xml():
    o=["<?xml version='1.0' encoding='UTF-8'?>\n"]
    o.append("<home version='5300' name='LUMINA_Clinica.sh3d' camera='observerCamera' wallHeight='300' basePlanLocked='false'>\n")
    o.append("  <environment groundColor='FFD5CFC4' skyColor='FFDCE8F2' lightColor='FFD0D0D0' ceillingLightColor='FFC8C8C8' drawingMode='FILL' wallsAlpha='0.0' allLevelsVisible='false' photoWidth='1600' photoHeight='1000' photoQuality='3'/>\n")
    o.append("  <compass x='-120' y='120' diameter='100' northDirection='0' visible='true'/>\n")
    o.append("  <observerCamera attribute='observerCamera' lens='PINHOLE' x='490' y='1945' z='165' yaw='3.6' pitch='0.05' fieldOfView='1.2' time='1'/>\n")
    o.append("  <camera attribute='topCamera' lens='PINHOLE' x='500' y='3300' z='2300' yaw='3.14159' pitch='0.85' fieldOfView='1.0' time='1'/>\n")
    for s in SEGS:
        j=''
        if s['kind']=='ext': j=f" wallAtStart='{s['prev']}' wallAtEnd='{s['next']}'"
        o.append(f"  <wall id='{s['id']}'{j} xStart='{s['x0']:.1f}' yStart='{s['y0']:.1f}' xEnd='{s['x1']:.1f}' yEnd='{s['y1']:.1f}' height='300' thickness='{s['t']}' pattern='hatchUp' topColor='FF7A6E62' leftSideColor='{hx(s['left'])}' rightSideColor='{hx(s['right'])}'/>\n")
    for k,(nm,(x0,y0,x1,y1),ft) in {k:(n,r,f) for k,n,r,f in [(k,n,r,f) for k,n,r,f in L.ROOMS]}.items():
        tx=FLOORTEX[ft]; w,h=TEX[tx].size
        o.append(f"  <room id='room_{k}' name={quoteattr(nm)} areaVisible='true' floorVisible='true' ceilingVisible='true' ceilingColor='FFF7F1E8'>\n")
        o.append(f"    <texture attribute='floorTexture' name='{tx}' width='120.0' height='120.0' image='t/{tx}.png'/>\n")
        for px,py in((x0,y0),(x1,y0),(x1,y1),(x0,y1)): o.append(f"    <point x='{px}' y='{py}'/>\n")
        o.append("  </room>\n")
    n=0
    for d in DOORS:
        sw=d['swing']; th=d['angle']; ux,uy=math.cos(th),math.sin(th); uax=uy if d['axis']=='V' else ux
        def hxa(h):
            if uax>0: return 0 if h=='min' else 1
            return 1 if h=='min' else 0
        if d['hinge']=='both':
            sash=[(0,0,0,-math.pi/2,0.5),(1,0,math.pi,1.5*math.pi,0.5)]
        else:
            h=hxa(d['hinge']); sash=[(h,0,0 if h==0 else math.pi,-math.pi/2 if h==0 else 1.5*math.pi,1.0)]
        inner=''.join(f"<sash xAxis='{s[0]}' yAxis='0.5' width='{s[4]}' startAngle='{s[2]:.5f}' endAngle='{s[3]:.5f}'/>" for s in sash)
        ex="wallThickness='1' wallDistance='0' wallWidth='1' wallLeft='0' wallHeight='1' wallTop='0' widthDepthDeformable='false' boundToWall='true'"
        o.append(piece_xml('doorOrWindow',f'door{n}',d['id'],d['model'],d['x'],d['y'],0,th,d['W'],d['D'],d['H'],ex,inner,False)); n+=1
    for w in WINDOWS:
        ex="wallThickness='1' wallDistance='0' wallWidth='1' wallLeft='0' wallHeight='1' wallTop='0' widthDepthDeformable='false' boundToWall='true'"
        o.append(piece_xml('doorOrWindow',f'win{n}',w['id'],w['model'],w['x'],w['y'],w['elev'],w['angle'],w['W'],w['D'],w['H'],ex,'',False)); n+=1
    for i,it in enumerate(ITEMS):
        if it['kind']=='light':
            col='FFFFE0A8' if it['model'] not in('painel_led_60',) else 'FFFFF6E0'
            ls=f"<lightSource x='0.5' y='0.5' z='0.0' color='{col}' diameter='6.0'/>"
            o.append(piece_xml('light',f'p{i}',it['name'],it['model'],it['x'],it['y'],it['elev'],it['angle'],it['W'],it['D'],it['H'],a('power',float(it['power'] or 0.4)),ls))
        else:
            o.append(piece_xml('pieceOfFurniture',f'p{i}',it['name'],it['model'],it['x'],it['y'],it['elev'],it['angle'],it['W'],it['D'],it['H']))
    o.append("</home>\n")
    return ''.join(o)

def write_sh3d(path):
    xml=build_xml(); used=set(d['model'] for d in DOORS+WINDOWS+ITEMS)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('Home.xml',xml)
        for m in sorted(used):
            f=REG[m]['folder']
            z.write(f'{f}/{m}.obj',f'm/{m}/{m}.obj'); z.write(f'{f}/{m}.mtl',f'm/{m}/{m}.mtl'); z.write(f'{f}/{m}_icone.png',f'i/{m}.png')
        for t in set(FLOORTEX.values()): z.write(f'{OUT}/texturas/{t}.png',f't/{t}.png')
    return xml,used

if __name__=='__main__':
    xml,used=write_sh3d(f'{OUT}/projeto/LUMINA_Clinica.sh3d')
    import xml.dom.minidom as md; md.parseString(xml.encode()); print('XML ok', len(xml), 'modelos usados', len(used), 'paredes', len(SEGS))
