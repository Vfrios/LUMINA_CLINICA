#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baixa mapas PBR 2K da Poly Haven para a pasta texturas/."""
import hashlib
import json
import os
import urllib.request

from PIL import Image


RAIZ = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(RAIZ, 'texturas')
API = 'https://api.polyhaven.com'

# Poly Haven usa slugs específicos; estes materiais correspondem aos nomes
# solicitados para a clínica.
ASSETS = {
    'marble': 'marble_01',
    'wood_planks': 'wood_planks',
    'porcelain': 'interior_tiles',
    'fabric_linen': 'rough_linen',
}
MAPAS = {
    'diffuse': 'Diffuse',
    'normal': 'nor_gl',
    'roughness': 'Rough',
}
RESOLUCAO = '2k'
EXTENSAO = 'jpg'


def obter_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'LuminaClinic texture downloader'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def baixar(url, caminho, md5_esperado):
    request = urllib.request.Request(url, headers={'User-Agent': 'LuminaClinic texture downloader'})
    with urllib.request.urlopen(request, timeout=120) as response:
        dados = response.read()
    md5 = hashlib.md5(dados).hexdigest()
    if md5_esperado and md5.lower() != md5_esperado.lower():
        raise RuntimeError(f'Checksum MD5 inválido para {os.path.basename(caminho)}')

    with open(caminho, 'wb') as arquivo:
        arquivo.write(dados)
    with Image.open(caminho) as imagem:
        imagem.verify()


def main():
    os.makedirs(DESTINO, exist_ok=True)
    for nome, asset_id in ASSETS.items():
        arquivos = obter_json(f'{API}/files/{asset_id}')
        for mapa, chave_api in MAPAS.items():
            try:
                arquivo = arquivos[chave_api][RESOLUCAO][EXTENSAO]
            except KeyError as erro:
                raise RuntimeError(
                    f'A Poly Haven não disponibilizou {chave_api}/{RESOLUCAO}/{EXTENSAO} '
                    f'para o asset "{asset_id}".'
                ) from erro

            caminho = os.path.join(DESTINO, f'{nome}_{mapa}.jpg')
            baixar(arquivo['url'], caminho, arquivo.get('md5'))
            print(f'OK {nome}_{mapa}.jpg ({RESOLUCAO}, {os.path.getsize(caminho):,} bytes)')


if __name__ == '__main__':
    try:
        main()
    except Exception as erro:
        raise SystemExit(f'Erro ao baixar texturas PBR: {erro}') from erro
