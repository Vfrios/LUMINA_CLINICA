#!/usr/bin/env bash
# LÚMINA · pipeline completo e reprodutível.
# Gera: planta 2D, renders, .sh3d, OBJ/MTL (cm e metros), verificação (build_a..d) e depois dist/web + .glb + zip (export_web).
# Uso:  ./build.sh            (padrão; modelos e site em dist/web)
#       ./build.sh --vendor   (também baixa model-viewer/three p/ dist/web/vendor — uso offline; precisa de internet)
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
( cd codigo_fonte \
  && "$PY" build_a.py && "$PY" build_b.py && "$PY" build_c.py && "$PY" build_d.py )
"$PY" baixar_texturas.py
"$PY" export_web.py "$@"
echo "OK → dist/web/index.html  (teste: npx serve dist/web)"
