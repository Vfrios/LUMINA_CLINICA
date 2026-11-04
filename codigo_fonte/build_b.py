import os, math, zipfile, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.path import Path
import lib_geom as G, layout as L, build_a as A, scene
from models import REG
OUT=A.OUT

# ================= PLANTA 2D =================
FLOORC={'areia':'#EFE3CF','claro':'#F3EEE4','marmore':'#EADFD0'}
def draw_plan(ax,show_furn=True):
    ax.set_aspect('equal'); ax.set_xlim(-140,1140); ax.set_ylim(2130,-120); ax.axis('off')
    for k,n,(x0,y0,x1,y1),ft in L.ROOMS:
        ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fc=FLOORC[ft],ec='none',zorder=1))
    # paredes
    for s in A.SEGS:
        t=s['t']; horiz=abs(s['y0']-s['y1'])<1e-6
        lo,hi=sorted((s['x0'],s['x1'])) if horiz else sorted((s['y0'],s['y1']))
        ext=s['kind']=='ext'
        if horiz: r=Rectangle((lo-(t/2 if ext else 0),s['y0']-t/2),hi-lo+(t if ext else 0),t,fc='#3d3a37' if ext else '#4a4642',ec='none',zorder=3)
        else: r=Rectangle((s['x0']-t/2,lo-(t/2 if ext else 0)),t,hi-lo+(t if ext else 0),fc='#3d3a37' if ext else '#4a4642',ec='none',zorder=3)
        ax.add_patch(r)
    # vãos de porta e janela
    for d in A.DOORS:
        t=d['D']; 
        if d['axis']=='H': ax.add_patch(Rectangle((d['x']-d['W']/2,d['y']-t/2-0.3),d['W'],t+0.6,fc='white',ec='none',zorder=4))
        else: ax.add_patch(Rectangle((d['x']-t/2-0.3,d['y']-d['W']/2),t+0.6,d['W'],fc='white',ec='none',zorder=4))
        secs=L.door_sector(d); secs=secs if isinstance(secs[0],list) else [secs]
        for sec in secs:
            hx,hy=sec[0]; arc=sec[1:]
            ax.plot([hx,arc[-1][0]],[hy,arc[-1][1]],color='#7a2e3a',lw=1.0,zorder=6)
            ax.plot([p[0] for p in arc],[p[1] for p in arc],color='#7a2e3a',lw=0.5,ls=(0,(3,2)),zorder=6)
    for w in A.WINDOWS:
        t=w['D']
        if w['axis']=='H': x0,y0,ww,hh=w['x']-w['W']/2,w['y']-t/2,w['W'],t
        else: x0,y0,ww,hh=w['x']-t/2,w['y']-w['W']/2,t,w['W']
        ax.add_patch(Rectangle((x0,y0),ww,hh,fc='white',ec='none',zorder=4))
        if w['axis']=='H':
            for yy in (w['y']-t/6,w['y'],w['y']+t/6): ax.plot([x0,x0+ww],[yy,yy],color='#2b6f8f',lw=0.6,zorder=5)
        else:
            for xx in (w['x']-t/6,w['x'],w['x']+t/6): ax.plot([xx,xx],[y0,y0+hh],color='#2b6f8f',lw=0.6,zorder=5)
    # mobiliário
    if show_furn:
        for it in A.ITEMS:
            if it['kind']=='light': continue
            fp=L.footprint(it); big=it['model'] in('maca_profissional','sofa_4_lugares','balcao_recepcao')
            col={'marsala':'#c99ea6'}.get('',None)
            fc='#d8c3b0' if it['elev']<60 else '#e9dccf'
            if 'marsala' in it['model'] or it['model']=='balcao_recepcao': fc='#c49aa2'
            if it['model'] in('planta_grande','planta_pequena'): fc='#9dbb8f'
            ax.add_patch(Polygon(fp,closed=True,fc=fc,ec='#5a4a3e',lw=0.5,zorder=7,alpha=0.95 if it['elev']<60 else 0.7))
        # círculo de manobra PNE
        ax.add_patch(Circle((890,1465),75,fc='none',ec='#2b6f8f',lw=0.8,ls=(0,(4,3)),zorder=8))
        ax.text(890,1465,'Ø1,50 m\nmanobra',ha='center',va='center',fontsize=4.5,color='#2b6f8f',zorder=9)
    # rótulos
    small={'banheiro_clientes','banheiro_acessivel','dml','area_tecnica'}
    for k,n,(x0,y0,x1,y1),ft in L.ROOMS:
        area=(x1-x0)*(y1-y0)/10000; wm,dm=(x1-x0)/100,(y1-y0)/100
        cx,cy=(x0+x1)/2,(y0+y1)/2
        lab={'circulacao':'CIRCULAÇÃO PRINCIPAL'}.get(k,n.upper())
        fs=4.6 if k in small else 5.6
        if k=='circulacao': ax.text(490,850,'CIRCULAÇÃO\nPRINCIPAL\n%.2f × %.2f m\n%.1f m²'%(wm,dm,area),ha='center',va='center',fontsize=5,rotation=0,zorder=10,color='#333',bbox=dict(fc='white',ec='none',alpha=0.75,pad=1))
        else:
            LP={'recepcao':(215,1935),'espera':(490,1760),'consultorio':(355,1470),'botox':(190,1290),'peeling':(200,928),'drenagem':(180,355),
                'tecnologia':(790,578),'deposito':(190,140),'descanso':(720,300),'area_tecnica':(800,112),'copa':(850,1172),'dml':(648,1120),
                'banheiro_clientes':(655,1450),'banheiro_acessivel':(825,1600),'ramal':(715,1305)}
            cx,cy=LP.get(k,(cx,cy)); xoff=yoff=0
            import textwrap
            nm='\n'.join(textwrap.wrap(lab,22 if k not in small else 16))
            ax.text(cx+xoff,cy+yoff,f'{nm}\n{wm:.2f} × {dm:.2f} m · {area:.1f} m²',ha='center',va='center',fontsize=fs,zorder=10,color='#222',fontweight='bold' if k not in small else 'normal',bbox=dict(fc='white',ec='none',alpha=0.8,pad=1.2),linespacing=1.15)
    # cotas gerais
    def dim(x0,y0,x1,y1,txt,off,horiz=True):
        ax.annotate('',xy=(x0,y0),xytext=(x1,y1),arrowprops=dict(arrowstyle='<->',lw=0.7,color='#333'),zorder=11)
        ax.text((x0+x1)/2+(off if not horiz else 0),(y0+y1)/2+(off if horiz else 0),txt,ha='center',va='center',fontsize=6.5,rotation=0 if horiz else 90,zorder=11,bbox=dict(fc='white',ec='none',pad=1))
    dim(0,2060,1000,2060,'10,00 m (fachada frontal)',18,True); dim(-70,0,-70,2000,'20,00 m',-18,False)
    ax.text(500,2105,'▲ FACHADA FRONTAL / ENTRADA PRINCIPAL (porta dupla 1,20 m)',ha='center',fontsize=6.5,color='#7a2e3a',fontweight='bold')
    ax.text(500,-60,'FUNDOS · saída de serviço 0,90 m',ha='center',fontsize=6,color='#555')
    # barra de escala
    ax.plot([1030,1130],[1960,1960],color='k',lw=2); ax.text(1080,1935,'1 m',ha='center',fontsize=6)
def make_plan():
    fig=plt.figure(figsize=(11.69,16.54)); ax=fig.add_axes([0.03,0.09,0.94,0.83])
    draw_plan(ax)
    fig.text(0.5,0.955,'LÚMINA · Clínica de Estética e Biomedicina',ha='center',fontsize=18,color='#7a2e3a',fontweight='bold')
    fig.text(0.5,0.935,'PLANTA BAIXA CONCEITUAL · pavimento único · 10,00 × 20,00 m (200 m²) · pé-direito 3,00 m',ha='center',fontsize=10)
    fig.text(0.04,0.06,'Legenda: parede externa 15 cm · parede interna 10 cm · arcos vinho = giro das portas · azul = janelas / círculo de manobra Ø1,50 m\n'
      'Projeto CONCEITUAL. Não atesta conformidade com normas sanitárias (ex.: RDC 50/ANVISA), acessibilidade (NBR 9050), instalações ou legislação local;\n'
      'validação por profissional habilitado (arquiteto/engenheiro) é necessária. Áreas = dimensões líquidas internas (face a face das paredes).',fontsize=7,va='top',color='#333')
    fig.text(0.96,0.02,'Escala aprox. 1:75 (A3)',ha='right',fontsize=7)
    return fig
def table_page():
    fig=plt.figure(figsize=(11.69,16.54)); fig.text(0.5,0.95,'LÚMINA · Quadro de ambientes e áreas',ha='center',fontsize=16,color='#7a2e3a',fontweight='bold')
    rows=[]; tot=0
    for k,n,(x0,y0,x1,y1),ft in L.ROOMS:
        w,d=(x1-x0)/100,(y1-y0)/100; rows.append([n,f'{w:.2f} × {d:.2f}',f'{w*d:.1f}']); tot+=w*d
    rows.append(['TOTAL líquido (ambientes)','',f'{tot:.1f}']); rows.append(['Paredes, espessuras e demais (200,0 − líquido)','',f'{200-tot:.1f}']); rows.append(['ÁREA CONSTRUÍDA TOTAL (10,00 × 20,00)','','200.0'])
    ax=fig.add_axes([0.06,0.45,0.88,0.45]); ax.axis('off')
    t=ax.table(cellText=rows,colLabels=['Ambiente','Dimensões líquidas (m)','Área (m²)'],loc='upper center',cellLoc='left',colWidths=[0.6,0.25,0.15]); t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1,1.5)
    for (r,c),cell in t.get_celld().items():
        if r==0: cell.set_facecolor('#7a2e3a'); cell.set_text_props(color='white',fontweight='bold')
        elif r>=len(rows)-2: cell.set_facecolor('#efe3cf')
    return fig,tot
def make_planta_files():
    fig=make_plan(); fig.savefig(f'{OUT}/planta/planta_2D.png',dpi=200); 
    with PdfPages(f'{OUT}/planta/planta_2D.pdf') as pdf:
        pdf.savefig(fig); f2,tot=table_page(); pdf.savefig(f2)
    plt.close('all'); return tot

# ================= RENDERS =================
# Câmeras dos renders (fonte única: também usadas pelo web app via export_web.py)
# nome: (olho (x, y_cima, z) cm, alvo (x, y, z) cm, fov vertical °, tamanho px, com_teto)
RENDER_CAMS={
 'render_01_vista_aerea_fachada':((560,2350,3300),(500,0,950),42,(1600,1100),False),
 'render_02_vista_superior':((500,3700,1080),(500,0,1000),34,(1000,1800),False),
 'render_03_recepcao':((500,165,1960),(215,150,1700),80,(1600,1000),True),
 'render_04_sala_espera':((452,160,1655),(880,85,1900),82,(1600,1000),True),
 'render_05_sala_tecnologia':((600,165,905),(900,85,640),82,(1600,1000),True),
 'render_06_sala_botox':((80,165,1318),(300,70,1120),82,(1600,1000),True),
 'render_07_corredor':((490,160,1610),(490,150,700),62,(1600,1000),True),
 'render_08_banheiro_acessivel':((775,150,1385),(920,60,1560),85,(1400,1000),True),
 'render_09_sala_ti':((615,165,55),(840,80,95),82,(1400,1000),True),
 'render_10_sala_peeling':((80,165,950),(300,70,800),82,(1600,1000),True),
 'render_11_sala_drenagem':((80,165,590),(300,70,440),82,(1600,1000),True),
 'render_12_banheiro_clientes':((640,155,1405),(690,65,1515),82,(1400,1000),True),
}
def make_renders():
    P0=scene.full_scene(ceilings=False,ground=False)
    ground=[(scene.mat('CFC8B8'),[(-500,-0.6,2700),(1500,-0.6,2700),(1500,-0.6,-700),(-500,-0.6,-700)])]
    P0+=ground
    Pc=scene.full_scene(ceilings=True,ground=False)
    for name,(eye,tg,fov,size,teto) in RENDER_CAMS.items():
        P=Pc if teto else P0
        im=G.render(P,eye,tg,fov=fov,size=size,ss=1.5 if size[0]>=1400 else 1.4,bg=(0.93,0.91,0.88),ambient=0.72 if teto else 0.52)
        im.save(f'{OUT}/renders/{name}.png'); print('ok',name)

# ================= OBJ do prédio completo =================
def whole_obj():
    P=scene.full_scene(ceilings=False,ground=False)
    d=f'{OUT}/modelos/predio_completo'; os.makedirs(d,exist_ok=True)
    G.write_obj(P,d,'LUMINA_Clinica_completa'); return len(P)

def whole_obj_web():
    """Prédio completo (com teto) em OBJ web: metros + normais + Tr."""
    P=scene.full_scene(ceilings=True,ground=False)
    G.write_obj_web(P,f'{OUT}/modelos_web/predio_completo','predio_completo'); return len(P)

if __name__=='__main__':
    tot=make_planta_files(); print('planta ok, area liquida',round(tot,2))
    print('obj polys',whole_obj()); print('obj web polys',whole_obj_web())
    make_renders()
