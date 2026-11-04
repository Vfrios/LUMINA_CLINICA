import math, numpy as np, random
import lib_geom as G
from lib_geom import Mesh, MATS, H as HEX
import layout as L
import build_a as A
from models import REG

def mat(hexs):
    k='w_'+hexs
    if k not in MATS: MATS[k]=HEX(hexs)
    return k

def cbox(polys,x0,y0,z0,x1,y1,z1,m6):
    fr=[[(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],[(x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)],
        [(x1,y0,z1),(x1,y0,z0),(x1,y1,z0),(x1,y1,z1)],[(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0)],
        [(x0,y1,z1),(x1,y1,z1),(x1,y1,z0),(x0,y1,z0)],[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)]]
    for f,m in zip(fr,m6): polys.append((m,f))

def wall_polys(ceiling_h=300):
    polys=[]
    for s in A.SEGS:
        horiz=abs(s['y0']-s['y1'])<1e-6; t=s['t']
        lo,hi=(min(s['x0'],s['x1']),max(s['x0'],s['x1'])) if horiz else (min(s['y0'],s['y1']),max(s['y0'],s['y1']))
        fixed=s['y0'] if horiz else s['x0']
        dx,dy=s['x1']-s['x0'],s['y1']-s['y0']; Ln=math.hypot(dx,dy); nx,ny=dy/Ln,-dx/Ln  # normal esquerda
        top=mat('7A6E62')
        # extensões nos cantos externos
        ops=[]
        for d in A.DOORS:
            if (d['axis']=='H')==horiz and abs((d['y'] if horiz else d['x'])-fixed)<1:
                c=d['x'] if horiz else d['y']
                if lo-0.1<=c<=hi+0.1: ops.append((c-d['W']/2,c+d['W']/2,0,d['H']))
        for w in A.WINDOWS:
            if (w['axis']=='H')==horiz and abs((w['y'] if horiz else w['x'])-fixed)<1:
                c=w['x'] if horiz else w['y']
                if lo-0.1<=c<=hi+0.1: ops.append((c-w['W']/2,c+w['W']/2,w['elev'],w['elev']+w['H']))
        ops.sort()
        cur=lo; parts=[]
        for (o0,o1,z0,z1) in ops:
            o0=max(o0,lo); o1=min(o1,hi)
            if o0>cur: parts.append((cur,o0,0,ceiling_h))
            if z0>0: parts.append((o0,o1,0,z0))
            if z1<ceiling_h: parts.append((o0,o1,z1,ceiling_h))
            cur=max(cur,o1)
        if cur<hi: parts.append((cur,hi,0,ceiling_h))
        lm,rm=mat(s['left']),mat(s['right'])
        for (p0,p1,y0,y1) in parts:
            if horiz:
                x0,x1,z0,z1=p0,p1,fixed-t/2,fixed+t/2
                # esquerda: normal (nx,ny) -> ny<0 => norte(-z)
                m_n=lm if ny<0 else rm; m_s=rm if ny<0 else lm
                cbox(polys,x0,y0,z0,x1,y1,z1,[m_s,m_n,top,top,top,top])
            else:
                x0,x1,z0,z1=fixed-t/2,fixed+t/2,p0,p1
                m_e=lm if nx>0 else rm; m_w=rm if nx>0 else lm
                cbox(polys,x0,y0,z0,x1,y1,z1,[top,top,m_e,m_w,top,top])
    return polys

def floor_polys(ceilings=False):
    polys=[]; rng=random.Random(4)
    base={'areia':'DCCBAE','claro':'E4DDD0','marmore':'E6DED0'}
    for k,n,(x0,y0,x1,y1),ft in L.ROOMS:
        b=base[ft]; step=60 if ft!='marmore' else 60
        xs=list(np.arange(x0,x1,step))+[x1]; ys=list(np.arange(y0,y1,step))+[y1]
        for i in range(len(xs)-1):
            for j in range(len(ys)-1):
                sh=1+rng.uniform(-0.03,0.03); c=''.join('%02X'%int(min(255,int(b[q:q+2],16)*sh)) for q in (0,2,4))
                m=mat(c); ax,bx,ay,by=xs[i]+0.4,xs[i+1]-0.4,ys[j]+0.4,ys[j+1]-0.4
                polys.append((m,[(ax,0.2,by),(bx,0.2,by),(bx,0.2,ay),(ax,0.2,ay)]))
        polys.append((mat('C7B899'),[(x0,0.1,y1),(x1,0.1,y1),(x1,0.1,y0),(x0,0.1,y0)]))
        if ceilings: polys.append(('teto',[(x0,300,y0),(x1,300,y0),(x1,300,y1),(x0,300,y1)]))
    return polys

def item_polys(items):
    out=[]
    for it in items:
        d=REG[it['model']]; th=it['angle']; c,s=math.cos(th),math.sin(th)
        for m,vs in d['polys']:
            out.append((m,[(it['x']+x*c-z*s, it['elev']+y, it['y']+x*s+z*c) for x,y,z in vs]))
    return out

def full_scene(ceilings=False,ground=True):
    polys=wall_polys()+floor_polys(ceilings)
    if ceilings:
        pass
    polys+=item_polys(A.DOORS+A.WINDOWS+A.ITEMS)
    if ground:
        polys.append((mat('BDB6A6'),[(-600,-0.5,2900),(1600,-0.5,2900),(1600,-0.5,-900),(-600,-0.5,-900)]))
    return polys
