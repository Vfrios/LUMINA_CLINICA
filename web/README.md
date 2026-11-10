# web/ — fonte do site

Esta pasta é a **fonte**. O site publicável é `dist/web/` (gerado por `export_web.py`, que copia esta pasta, adiciona `modelos/`, `data/`, `texturas/` e preenche `sw.js`).

```bash
python3 baixar_texturas.py       # baixa diffuse, normal e roughness 2K
python3 export_web.py            # gera dist/web (ou: make web)
npx serve dist/web               # http://localhost:3000
```
- `index.html` + `js/app.js`: `<model-viewer>` com 8 vistas (= renders 01–08), seletor de ambiente com realce do piso, teto liga/desliga.
- `three/`: Three.js 0.160 (GLTFLoader) — órbita livre com amortecimento, **modo caminhada** (WASD/setas, Shift corre, C colisão, T teto; joysticks no celular e seletor de sensibilidade para órbita e caminhada). A barra de vistas mostra Recepção, Sala de espera, Consultório 1, Consultório 2 e Banheiro.
- `catalogo.html`: as 89 peças `.glb` individuais.
- `data/*.json` (views, rooms, collision, catalogo) são gerados — não edite à mão.
- Bibliotecas: model-viewer 3.5.0 e three 0.160.0 (versões fixas). Offline: `python3 export_web.py --vendor`.
- Publicar: envie o conteúdo de `dist/web/` ao GitHub Pages/Vercel/Netlify (site estático, caminhos relativos).
