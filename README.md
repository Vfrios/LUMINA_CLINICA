# LÚMINA · Clínica de Estética e Biomedicina — entrega web

Planta 2D, modelos 3D autorais e agora um **visualizador navegável** (web/PWA), tudo gerado por Python a partir de
`layout.py`, `models.py`, `lib_geom.py`, `scene.py`, `build_a.py` (nada foi remodelado).

## Como rodar
```bash
pip install numpy pillow matplotlib      # únicas dependências (Node só p/ servir/empacotar)
./build.sh                               # baixa mapas PBR, roda build_a→b→c→d e export_web.py
npx serve dist/web                       # abra o endereço mostrado (não use file://)
```
Para exportar apenas o site, rode `python baixar_texturas.py` antes de `python export_web.py` (ou `make web`).
`./build.sh --vendor` baixa `model-viewer` e `three` (versões fixas) para `dist/web/vendor/` → funciona offline.
Sem `--vendor` o site carrega essas bibliotecas de CDN (internet na 1ª visita; depois o service worker guarda cache).

## Publicar no Render
Este projeto é um site estático; use **New > Static Site**, não Web Service/Python. O arquivo `render.yaml` define a instalação das dependências, a execução do `build.sh` e a pasta publicada (`dist/web`). Não há Start Command nem plano de computação para configurar.

## Estrutura
```
codigo_fonte/   scripts originais (+ write_obj_web em lib_geom, OUT por LUMINA_OUT, RENDER_CAMS em build_b)
export_web.py   .obj(m) → .glb por peça + predio_completo.glb, data/*.json, dist/web, validação e zip
web/            fonte do site: index.html (model-viewer) · three/ (órbita + caminhada) · catalogo.html · PWA
dist/web/       site pronto p/ publicar (GitHub Pages/Vercel): modelos/*.glb, texturas/, data/, manifest, sw.js
dist/           verificacao_web.txt, LUMINA_WEB.zip
projeto/ planta/ renders/ modelos/ modelos_web/ texturas/   saídas legadas (.sh3d, PDF/PNG, OBJ em cm, OBJ em m)
electron/       casca desktop opcional
```

## O que mudou na exportação
- `lib_geom.write_obj_web`: metros, UVs planares por face (`vt`), normais `vn` por face (`f v/vt/vn`), faces degeneradas descartadas, `Tr = 1 − alpha`, `usemtl`/`mtllib` relativos. O `write_obj` original (cm) segue alimentando o `.sh3d`.
- `baixar_texturas.py`: baixa mapas diffuse, normal OpenGL e roughness 2K da Poly Haven para mármore, madeira, porcelanato e linho; o exportador embute os mapas PBR nos GLBs.
- Conversão OBJ→GLB em **Python puro** (numpy + Pillow; sem Blender/obj2gltf): cores em linear, `ALPHA` → `alphaMode: BLEND`, LEDs emissivos, `predio_completo.glb` (≈1,7 MB) a partir de `scene.full_scene(ceilings=True)`.
- Pisos viram 1 quad por ambiente com textura embutida (material `piso_<id>`), o que permite o realce do ambiente. Teto é face única (some na vista aérea).
- Se o GLB passar de 20 MB: `python3 export_web.py --otimizar meshopt` (usa `@gltf-transform/cli`; ou Draco).

## App
- **PWA** (pronto): `manifest.webmanifest` + `sw.js`; no Chrome/Edge/Android use "Instalar aplicativo".
- **Electron** (esqueleto, não testado aqui): `cd electron && npm i && npm run make`.

## Limitações
Ultraformer e Lavieen são volumes **ilustrativos**. Colisão do modo caminhada é simples (paredes + móveis grandes). Só um pavimento.
Validação feita aqui: GLB estrutural, escala, alcançabilidade a pé dos 16 ambientes, fiação do site em Chromium com stub do model-viewer.
**Não** foi possível testar o render real em model-viewer/Three.js (sem acesso à internet no ambiente): confira visualmente.

> **Projeto conceitual.** Não atesta conformidade com RDC 50/ANVISA, NBR 9050, instalações ou legislação local; validação por profissional habilitado é necessária.
