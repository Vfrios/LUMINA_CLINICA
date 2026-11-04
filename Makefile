# LÚMINA · make all | make web | make serve | make clean
PY ?= python3
.PHONY: all legado texturas web serve vendor clean
all: legado web
legado:            ## planta 2D, renders, .sh3d, OBJ/MTL, verificação
	cd codigo_fonte && $(PY) build_a.py && $(PY) build_b.py && $(PY) build_c.py && $(PY) build_d.py
texturas:          ## baixa mapas PBR 2K da Poly Haven
	$(PY) baixar_texturas.py
web: texturas      ## .obj -> .glb + dist/web + zip
	$(PY) export_web.py
vendor: texturas   ## idem, baixando model-viewer/three p/ uso offline
	$(PY) export_web.py --vendor
serve:             ## servidor local em http://localhost:3000
	npx --yes serve dist/web
clean:
	rm -rf dist modelos modelos_web projeto planta renders texturas verificacao.txt LISTA_AMBIENTES.md LEIAME_INSTRUCOES.md ../LUMINA_CLINICA.zip
