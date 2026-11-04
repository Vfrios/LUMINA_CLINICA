import os, shutil, zipfile, glob
import layout as L, build_a as A
from models import REG
OUT=A.OUT
rows=[]; tot=0
for k,n,(x0,y0,x1,y1),ft in L.ROOMS:
    w,d=(x1-x0)/100,(y1-y0)/100; rows.append(f'| {n} | {w:.2f} × {d:.2f} | {w*d:.1f} |'); tot+=w*d
prog={ 'Recepção':'4,00×3,50 → 4,00×3,50 (igual)','Sala de espera':'6,00×3,50 → 5,60×3,50 (−0,40 m: o vão livre de 9,70 m é dividido com a recepção de 4,00 m e a parede)',
 'Consultório':'3,20×3,50 → 4,00×2,80 (mesma área, 11,2 m², reorientado para caber na coluna de 4,00 m)','Botox / Peeling / Drenagem':'3,50×4,00 → 4,00×3,50 (mesma área, 14 m², girados)',
 'Tecnologia':'4,00×5,00 → 4,20×4,80 (20,2 m² ≈ 20 m²)','Banheiro de clientes':'2,20×2,50 → 1,90×2,50 (4,75 m²)','Banheiro acessível':'2,20×2,50 (igual, com círculo de manobra Ø1,50 m)',
 'DML':'1,50×2,00 → 1,60×3,00 (4,8 m²)','Copa':'2,50×3,00 (igual)','Depósito':'2,00×2,50 → 4,00×2,40 (9,6 m², ampliado para aproveitar a coluna)'}
md=f"""# LÚMINA — Lista de ambientes, dimensões e áreas

Imóvel: 10,00 × 20,00 m (200 m²), pavimento único, pé-direito 3,00 m, paredes externas 15 cm e internas 10 cm.
Dimensões abaixo = **líquidas internas** (face a face das paredes). Área líquida somada: **{tot:.1f} m²**; paredes e espessuras: **{200-tot:.1f} m²**.

| Ambiente | Dimensões líquidas (m) | Área (m²) |
|---|---|---|
""" + '\n'.join(rows) + f"""

## Ajustes em relação ao programa pedido (explicados)
Com paredes de 15/10 cm o vão interno útil é 9,70 × 19,70 m, então algumas medidas conceituais foram ajustadas para caberem sem sobreposição:

""" + '\n'.join(f'- **{k}**: {v}' for k,v in prog.items()) + """

## Ambientes acrescentados (não estavam na lista)
Sobrou área após o programa pedido; ela foi usada, conforme o enunciado ("circulação, áreas técnicas e ajustes"), para:
- **Área de funcionários (descanso/vestiário)** 4,20 × 2,50 m — complementa a Copa (item 11).
- **Área técnica (TI/elétrica)** 4,20 × 1,60 m.
- **Ramal de circulação** 4,20 × 1,20 m, que dá acesso aos sanitários, DML e copa (mantém os sanitários próximos à espera).

## Pontos de atenção do partido
- O corredor principal tem 1,30 m de largura e ~16 m de comprimento (o "corredor longo" que o enunciado pede para evitar não pôde ser eliminado com este programa em 10 m de frente); foi mitigado com painéis ripados, spots contínuos, portas de saída de serviço ao fundo e janela no ramal.
- Recepção e espera são integradas visualmente por divisória ripada parcial e vão de 1,85 m; as salas de procedimento ficam atrás da parede da recepção (privacidade).
- Copa, DML, depósito e banheiro de clientes não têm janela (ventilação/exaustão mecânica a projetar).
"""
open(f'{OUT}/LISTA_AMBIENTES.md','w').write(md)

leia="""# LÚMINA — Instruções para abrir o projeto no Sweet Home 3D

## Conteúdo
```
LUMINA_CLINICA/
├── projeto/LUMINA_Clinica.sh3d      ← projeto completo (paredes, ambientes, portas, janelas, móveis, luzes)
├── modelos/                         ← todos os modelos 3D em OBJ + MTL (1 pasta por peça, com ícone .png)
│   ├── recepcao/  maca/  ultraformer/  lavieen/  armarios/  decoracao/
│   ├── portas/  banheiros/  copa/  dml/  deposito/  equipamentos/  espera/  funcionarios/
│   ├── iluminacao/  salas/  tecnica/  consultorio/
│   └── predio_completo/LUMINA_Clinica_completa.obj   ← prédio inteiro em 1 peça (plano B)
├── texturas/                        ← porcelanato areia/claro, mármore, madeira ripada, marsala, terracota
├── planta/planta_2D.pdf, planta_2D.png
├── renders/                         ← 8 imagens conceituais (vista aérea, superior, recepção, espera, tecnologia, botox, corredor, WC acessível)
├── codigo_fonte/                    ← scripts Python que geram tudo (ajuste e rode de novo se quiser mudar o layout)
├── LISTA_AMBIENTES.md   verificacao.txt   LEIAME_INSTRUCOES.md
```

## Caminho A (preferencial): abrir o .sh3d
1. Instale o Sweet Home 3D (versão 6.x ou superior recomendada).
2. Menu **Arquivo > Abrir…** e escolha `projeto/LUMINA_Clinica.sh3d`.
3. Use **Vista 3D > Vista aérea** (ou "Modificar vista 3D") e o **modo visitante virtual** para percorrer a clínica.

**Aviso honesto:** o arquivo foi montado programaticamente (formato Home.xml dentro do .sh3d) e **não pôde ser aberto no Sweet Home 3D real** durante a criação, pois o programa não estava disponível no ambiente. A estrutura foi validada (XML bem formado, todas as referências internas existem), mas o carregamento real precisa ser confirmado por você. Se o programa recusar o arquivo, use o Caminho B.

Também vale conferir depois de abrir: (a) o sentido de abertura das portas na planta (arcos) — se algum vier invertido, selecione a porta e use Modificar > espelhar; (b) o brilho das luzes; (c) as cores/texturas dos pisos.

## Caminho B (plano de contingência): importar os modelos
1. Abra o Sweet Home 3D com um projeto novo.
2. **Mobiliário > Importar mobiliário…** e escolha o `.obj` desejado (por exemplo `modelos/predio_completo/LUMINA_Clinica_completa.obj`). Na janela, marque a orientação "frente" para o lado que dá para você; as dimensões já são reais (cm).
3. Com o prédio completo importado como uma peça (1000 × 2000 × 300 cm), posicione em x=500, y=1000. Para montar você mesmo, importe as peças de `modelos/*` individualmente e use `planta/planta_2D.png` como **imagem de fundo** (Planta > Importar imagem de fundo, escala: 10,00 m de largura).
4. Texturas: **Modificar cômodo > Textura do piso > Importar** com os PNG de `texturas/`.

## Observações sobre os modelos
- Ultraformer e Lavieen são **representações volumétricas ilustrativas** (console com tela, braço e peça de mão), em tamanho compatível com equipamentos reais; não são réplicas oficiais das marcas.
- Os renders (`renders/`) foram gerados por um rasterizador simples próprio: são conceituais, sem sombras/reflexos. Para imagens fotorrealistas use **Foto > Criar foto** dentro do Sweet Home 3D.

## Aviso importante
Projeto **CONCEITUAL**. Não afirma conformidade com normas sanitárias (ex.: RDC 50/ANVISA), acessibilidade (NBR 9050), instalações elétricas/hidráulicas, prevenção de incêndio ou legislação local. Essas verificações devem ser feitas por profissional habilitado.
"""
open(f'{OUT}/LEIAME_INSTRUCOES.md','w').write(leia)
os.makedirs(f'{OUT}/codigo_fonte',exist_ok=True)
for f in ['lib_geom.py','models.py','layout.py','build_a.py','scene.py','build_b.py','build_c.py','build_d.py']:
    if os.path.abspath(f)!=os.path.abspath(f'{OUT}/codigo_fonte/{f}'): shutil.copy(f,f'{OUT}/codigo_fonte/{f}')
open(f'{OUT}/codigo_fonte/COMO_REGERAR.txt','w').write('Requer Python 3 com numpy, pillow, matplotlib.\nOrdem: python3 build_a.py ; python3 build_b.py ; python3 build_c.py ; python3 build_d.py\n(ajuste o caminho OUT em build_a.py)\n')
zp=os.path.join(os.path.dirname(OUT),'LUMINA_CLINICA.zip')
if os.path.exists(zp): os.remove(zp)
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
    for root,dirs,fs in os.walk(OUT):
        dirs[:]=[x for x in dirs if x not in ('dist','__pycache__')]
        for f in fs: 
            p=os.path.join(root,f); z.write(p,os.path.relpath(p,os.path.dirname(OUT)))
print('zip',os.path.getsize(zp)//1024,'KB'); 
print(sorted(os.listdir(f'{OUT}/modelos')))
