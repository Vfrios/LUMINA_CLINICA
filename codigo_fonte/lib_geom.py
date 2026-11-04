import math, os
import numpy as np
from PIL import Image

# ---------- materiais (r,g,b,alpha) ----------
def H(h):
    h=h.lstrip('#'); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
MATS = {
 'marsala':H('7A2E3A'), 'marsala_tecido':H('6E2733'), 'terracota':H('B8674A'), 'bege':H('D9C7A8'),
 'areia':H('E3D3B5'), 'nude':H('E6CDBB'), 'marrom_claro':H('A47B55'), 'branco_quente':H('F5EEE3'),
 'madeira':H('B98A5B'), 'madeira_escura':H('8A6039'), 'madeira_porta':H('C29A6B'),
 'champagne':H('E2CFA2'), 'dourado':H('B8975A'), 'inox':H('C9C9C6'), 'cinza':H('9A9A98'),
 'preto':H('232323'), 'branco':H('F4F4F2'), 'ceramica':H('F3F1EC'), 'marmore':H('E9E2D6'),
 'tecido_bege':H('CDBBA0'), 'estofado_nude':H('E9D6C6'), 'tela':H('1B2230'),
 'verde':H('4F7A4B'), 'verde_claro':H('6E9A62'), 'led':H('FFE7B0'), 'led_neutro':H('FFF6E0'),
 'espelho':H('C8D6DC'), 'caixa':H('C9A879'), 'esquadria':H('CDB98F'),
 'vidro':(0.72,0.86,0.92), 'piso':H('DCCBAE'), 'teto':H('F7F1E8'),
}
ALPHA = {'vidro':0.28, 'espelho':0.85}

class Mesh:
    def __init__(s): s.p=[]
    def _q(s,m,pts):
        q=[pts[0]]
        for a in pts[1:]:
            if max(abs(a[i]-q[-1][i]) for i in range(3))>1e-9: q.append(a)
        if len(q)>2 and max(abs(q[0][i]-q[-1][i]) for i in range(3))<=1e-9: q.pop()
        if len(q)>=3: s.p.append((m,q))
    def bb(s,x0,y0,z0,x1,y1,z1,m):
        for pts in (
         [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
         [(x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)],
         [(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],
         [(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],
         [(x0,y1,z1),(x1,y1,z1),(x1,y1,z0),(x0,y1,z0)],
         [(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)]): s._q(m,pts)
        return s
    def b(s,cx,y0,cz,sx,sy,sz,m): return s.bb(cx-sx/2,y0,cz-sz/2,cx+sx/2,y0+sy,cz+sz/2,m)
    def cyl(s,cx,cy,cz,r,h,m,axis='y',n=16,r2=None):
        r2=r if r2 is None else r2
        P=lambda a,rr,y:(rr*math.cos(a),y,rr*math.sin(a))
        polys=[]
        for i in range(n):
            a0=2*math.pi*i/n; a1=2*math.pi*(i+1)/n
            polys.append([P(a1,r,-h/2),P(a0,r,-h/2),P(a0,r2,h/2),P(a1,r2,h/2)])
        polys.append([P(-2*math.pi*i/n,r2,h/2) for i in range(n)])
        polys.append([P(2*math.pi*i/n,r,-h/2) for i in range(n)])
        for pl in polys:
            out=[]
            for (x,y,z) in pl:
                if axis=='z': x,y,z=x,-z,y
                elif axis=='x': x,y,z=-y,x,z
                out.append((x+cx,y+cy,z+cz))
            s._q(m,out)
        return s
    def cy0(s,cx,y0,cz,r,h,m,n=16,r2=None): return s.cyl(cx,y0+h/2,cz,r,h,m,'y',n,r2)
    def sph(s,cx,cy,cz,rx,ry,rz,m,n=12,k=8):
        def P(i,j):
            th=math.pi*i/k; ph=2*math.pi*j/n
            return (cx+rx*math.sin(th)*math.cos(ph),cy+ry*math.cos(th),cz+rz*math.sin(th)*math.sin(ph))
        for i in range(k):
            for j in range(n):
                s._q(m,[P(i,j),P(i,j+1),P(i+1,j+1),P(i+1,j)])
        return s
    def prism(s,pts,z0,z1,m):
        n=len(pts)
        for i in range(n):
            a=pts[i]; b=pts[(i+1)%n]
            s._q(m,[(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)])
        s._q(m,[(x,y,z1) for x,y in pts]); s._q(m,[(x,y,z0) for x,y in reversed(pts)])
        return s
    def stroke(s,x0,y0,x1,y1,w,z0,z1,m):
        dx,dy=x1-x0,y1-y0; L=math.hypot(dx,dy); dx/=L; dy/=L; nx,ny=-dy*w/2,dx*w/2
        return s.prism([(x0-nx,y0-ny),(x1-nx,y1-ny),(x1+nx,y1+ny),(x0+nx,y0+ny)],z0,z1,m)
    def add(s,o,rx=0,ry=0,rz=0,px=0,py=0,pz=0,tx=0,ty=0,tz=0):
        a,b,c=map(math.radians,(rx,ry,rz))
        Rx=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
        Ry=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
        Rz=np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
        R=Rz@Ry@Rx; pv=np.array([px,py,pz]); tv=np.array([px+tx,py+ty,pz+tz])
        for m,vs in o.p: s.p.append((m,[tuple(R@(np.array(v)-pv)+tv) for v in vs]))
        return s
    def bbox(s):
        a=np.array([v for _,vs in s.p for v in vs]); return a.min(0),a.max(0)
    def normalized(s):
        lo,hi=s.bbox(); c=np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])
        return [(m,[tuple(np.array(v)-c) for v in vs]) for m,vs in s.p], tuple(hi-lo)

def write_obj(polys, folder, name):
    os.makedirs(folder,exist_ok=True)
    verts={}; vl=[]; groups={}
    def vid(v):
        k=(round(v[0],2),round(v[1],2),round(v[2],2))
        if k not in verts: verts[k]=len(vl)+1; vl.append(k)
        return verts[k]
    for m,vs in polys:
        ids=[vid(v) for v in vs]
        for i in range(1,len(ids)-1): groups.setdefault(m,[]).append((ids[0],ids[i],ids[i+1]))
    with open(os.path.join(folder,name+'.obj'),'w') as f:
        f.write(f'# LUMINA - {name}\nmtllib {name}.mtl\no {name}\n')
        for v in vl: f.write('v %.2f %.2f %.2f\n'%v)
        for m,fs in groups.items():
            f.write(f'usemtl {m}\n')
            for t in fs: f.write('f %d %d %d\n'%t)
    with open(os.path.join(folder,name+'.mtl'),'w') as f:
        for m in groups:
            r,g,b=MATS[m]; a=ALPHA.get(m,1.0)
            f.write(f'newmtl {m}\nKa {r*.4:.3f} {g*.4:.3f} {b*.4:.3f}\nKd {r:.3f} {g:.3f} {b:.3f}\nKs 0.12 0.12 0.12\nNs 25\nd {a}\nillum 2\n\n')

# ---------- exportação OBJ para web (metros + normais + Tr) ----------
def newell(vs):
    """Normal unitária e área de um polígono (método de Newell, vale p/ quadriláteros e n-gonos).
    Retorna (None, 0) se o polígono for degenerado."""
    n=np.zeros(3); k=len(vs)
    for i in range(k):
        a=vs[i]; b=vs[(i+1)%k]
        n+=((a[1]-b[1])*(a[2]+b[2]), (a[2]-b[2])*(a[0]+b[0]), (a[0]-b[0])*(a[1]+b[1]))
    ln=float(np.linalg.norm(n))
    return ((n/ln) if ln>1e-9 else None), ln/2

def write_obj_web(polys, folder, name, unit=0.01):
    """OBJ/MTL compatível com navegador:
       - vértices em METROS (cm * unit, unit=0.01);
       - normais (vn) recalculadas por face, faces no formato 'f v//vn';
       - faces degeneradas descartadas;
       - MTL com 'Tr = 1 - alpha' (em vez de 'd'), 'Ke' para materiais luminosos;
       - 'usemtl' por material e 'mtllib' relativo (mesmo diretório).
       Retorna (faces escritas, faces descartadas)."""
    os.makedirs(folder,exist_ok=True)
    V={}; vl=[]; N={}; nl=[]; groups={}; dropped=0
    def vid(v):
        k=(round(v[0]*unit,4),round(v[1]*unit,4),round(v[2]*unit,4))
        if k not in V: V[k]=len(vl)+1; vl.append(k)
        return V[k]
    def nid(n):
        k=(round(float(n[0]),4),round(float(n[1]),4),round(float(n[2]),4))
        if k not in N: N[k]=len(nl)+1; nl.append(k)
        return N[k]
    for m,vs in polys:
        nrm,area=newell(vs)
        if nrm is None or area<1e-4: dropped+=1; continue   # área em cm²
        ni=nid(nrm); ids=[vid(v) for v in vs]
        for i in range(1,len(ids)-1):
            tri=(ids[0],ids[i],ids[i+1])
            if len(set(tri))<3: dropped+=1; continue
            groups.setdefault(m,[]).append(tri+(ni,))
    nf=0
    with open(os.path.join(folder,name+'.obj'),'w') as f:
        f.write(f'# LUMINA (web) - {name}\n# unidade: metros | normais por face | y para cima\nmtllib {name}.mtl\no {name}\n')
        for v in vl: f.write('v %.4f %.4f %.4f\n'%v)
        for n in nl: f.write('vn %.4f %.4f %.4f\n'%n)
        for m,fs in groups.items():
            f.write(f'usemtl {m}\n')
            for a,b,c,n in fs: f.write(f'f {a}//{n} {b}//{n} {c}//{n}\n'); nf+=1
    EMIT={'led','led_neutro'}
    with open(os.path.join(folder,name+'.mtl'),'w') as f:
        for m in groups:
            r,g,b=MATS[m]; a=ALPHA.get(m,1.0)
            f.write(f'newmtl {m}\nKa {r*.4:.3f} {g*.4:.3f} {b*.4:.3f}\nKd {r:.3f} {g:.3f} {b:.3f}\nKs 0.12 0.12 0.12\nNs 25\n')
            if m in EMIT: f.write(f'Ke {r:.3f} {g:.3f} {b:.3f}\n')
            f.write(f'Tr {1-a:.3f}\nillum 2\n\n')
    return nf,dropped

# ---------- renderer (z-buffer) ----------
def look_at(eye,target,up=(0,1,0)):
    eye=np.array(eye,float); f=np.array(target,float)-eye; f/=np.linalg.norm(f)
    r=np.cross(f,up); r/=np.linalg.norm(r); u=np.cross(r,f)
    return eye,r,u,f

def render(polys, eye, target, fov=60, size=(1600,1000), ss=1.4, bg=(0.93,0.91,0.88), sun=(-0.35,-0.8,-0.5), alpha_mats=ALPHA, ambient=0.52):
    W,Hh=int(size[0]*ss),int(size[1]*ss)
    eye,r,u,f=look_at(eye,target)
    tris=[];cols=[];als=[];nrm=[]
    for m,vs in polys:
        c=MATS.get(m,(0.7,0.7,0.7)); a=alpha_mats.get(m,1.0)
        for i in range(1,len(vs)-1):
            tris.append((vs[0],vs[i],vs[i+1])); cols.append(c); als.append(a)
    T=np.array(tris,float); C=np.array(cols); A=np.array(als)
    n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); ln=np.linalg.norm(n,axis=1); ok=ln>1e-9
    T,C,A,n,ln=T[ok],C[ok],A[ok],n[ok],ln[ok]; n/=ln[:,None]
    cen=T.mean(1); vdir=eye-cen; flip=np.sign((n*vdir).sum(1)); flip[flip==0]=1; n=n*flip[:,None]
    L1=-np.array(sun,float); L1/=np.linalg.norm(L1); L2=np.array([0.5,0.3,0.8]); L2/=np.linalg.norm(L2)
    shade=ambient+0.36*np.clip(n@L1,0,1)+0.16*np.clip(n@L2,0,1)
    C=np.clip(C*shade[:,None]*np.array([1.02,1.0,0.96]),0,1)
    # camera space
    rel=T-eye; cam=np.stack([rel@r,rel@u,rel@f],axis=2)  # (N,3verts,3) x,y,z(depth positive forward)
    near=8.0
    depth=cam[:,:,2]
    allin=(depth>near).all(1); anyin=(depth>near).any(1)
    keep=[]; extra_t=[]; extra_c=[]; extra_a=[]
    idx_cross=np.where(anyin&~allin)[0]
    for k in idx_cross:
        poly=[cam[k,i] for i in range(3)]; out=[]
        for i in range(3):
            a,b=poly[i],poly[(i+1)%3]
            ain,bin_=a[2]>near,b[2]>near
            if ain: out.append(a)
            if ain!=bin_:
                t=(near-a[2])/(b[2]-a[2]); out.append(a+t*(b-a))
        for j in range(1,len(out)-1):
            extra_t.append([out[0],out[j],out[j+1]]); extra_c.append(C[k]); extra_a.append(A[k])
    cam=cam[allin]; Cc=C[allin]; Aa=A[allin]
    if extra_t:
        cam=np.concatenate([cam,np.array(extra_t)]); Cc=np.concatenate([Cc,np.array(extra_c)]); Aa=np.concatenate([Aa,np.array(extra_a)])
    fpx=(Hh/2)/math.tan(math.radians(fov)/2)
    sx=W/2+fpx*cam[:,:,0]/cam[:,:,2]; sy=Hh/2-fpx*cam[:,:,1]/cam[:,:,2]; iz=1.0/cam[:,:,2]
    img=np.zeros((Hh,W,3)); img[:]=np.array(bg); zb=np.zeros((Hh,W))
    order=np.argsort(Aa<1.0,kind='stable')  # opaque first
    for k in order:
        xs,ys,zs=sx[k],sy[k],iz[k]
        minx=max(int(math.floor(xs.min())),0); maxx=min(int(math.ceil(xs.max())),W-1)
        miny=max(int(math.floor(ys.min())),0); maxy=min(int(math.ceil(ys.max())),Hh-1)
        if maxx<minx or maxy<miny: continue
        den=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
        if abs(den)<1e-9: continue
        px=np.arange(minx,maxx+1)+0.5; py=np.arange(miny,maxy+1)+0.5
        PX,PY=np.meshgrid(px,py)
        w0=((ys[1]-ys[2])*(PX-xs[2])+(xs[2]-xs[1])*(PY-ys[2]))/den
        w1=((ys[2]-ys[0])*(PX-xs[2])+(xs[0]-xs[2])*(PY-ys[2]))/den
        w2=1-w0-w1
        m=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
        if not m.any(): continue
        z=w0*zs[0]+w1*zs[1]+w2*zs[2]
        sub=zb[miny:maxy+1,minx:maxx+1]; im=img[miny:maxy+1,minx:maxx+1]
        vis=m&(z>sub)
        if not vis.any(): continue
        if Aa[k]>=1.0:
            sub[vis]=z[vis]; im[vis]=Cc[k]
        else:
            im[vis]=im[vis]*(1-Aa[k])+Cc[k]*Aa[k]
    out=Image.fromarray((np.clip(img,0,1)*255).astype('uint8'))
    return out.resize(size,Image.LANCZOS)
