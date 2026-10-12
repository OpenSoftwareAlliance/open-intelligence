#!/usr/bin/env python3
"""Gera README.md e o dataset JSON a partir de catalogo/ (fonte de verdade).

Lê (manuais):
    catalogo/_categorias.yml     ordem e apresentação das categorias
    catalogo/<categoria>.yml     fontes, links e classificação
    data/taxonomy.json           vocabulário de input, output e tipo_fonte
    tools/readme/*.md            trechos fixos do README

Gera (nunca editar à mão):
    README.md, data/sources.json, data/index.json

Uso:
    python3 tools/build_dataset.py            valida e regenera os arquivos
    python3 tools/build_dataset.py --check    falha se algo estiver inválido ou desatualizado
    python3 tools/build_dataset.py --report   estatísticas do catálogo

Requer PyYAML (pip install -r requirements.txt).
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml  # noqa: F401
except ImportError:
    sys.exit("ERRO: falta o PyYAML. Rode: python3 -m pip install -r requirements.txt")

from catalogo_io import carrega_catalogo
from dataset import gera_saidas

RAIZ = Path(__file__).resolve().parent.parent


def grava(caminho, conteudo):
    """Grava em UTF-8 com fim de linha LF em qualquer sistema (no Windows o modo texto usaria CRLF)."""
    Path(caminho).write_bytes(conteudo.encode("utf-8"))


def primeira_diferenca(atual, gerado):
    """Número (a partir de 1) da primeira linha em que os textos divergem."""
    a, g = atual.splitlines(), gerado.splitlines()
    for n, (x, y) in enumerate(zip(a, g), start=1):
        if x != y:
            return n
    return min(len(a), len(g)) + 1


def relatorio(saidas):
    fontes = json.loads(saidas["data/sources.json"])["sources"]
    links = json.loads(saidas["data/index.json"])["links"]
    classes = Counter(f["classificacao"] for f in fontes)
    print(f"categorias .......... {len({f['categoria_id'] for f in fontes})}")
    print(f"fontes .............. {len(fontes)}")
    print(f"links ............... {len(links)}")
    print(f"classificação: heurística {classes['heuristica']} | override {classes['override']}")


def main(argv=None, raiz=RAIZ):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="falha se o catálogo for inválido ou os arquivos gerados estiverem desatualizados")
    ap.add_argument("--report", action="store_true", help="imprime estatísticas do catálogo")
    args = ap.parse_args(argv)
    raiz = Path(raiz)

    catalogo, erros = carrega_catalogo(raiz)
    if erros:
        print(f"ERROS NO CATÁLOGO ({len(erros)}):", file=sys.stderr)
        for erro in erros:
            print(f"  {erro}", file=sys.stderr)
        return 1

    saidas = gera_saidas(raiz, catalogo)
    if args.report:
        relatorio(saidas)

    if args.check:
        desatualizados = []
        for relativo, conteudo in saidas.items():
            caminho = raiz / relativo
            atual = caminho.read_text(encoding="utf-8") if caminho.exists() else ""
            if atual != conteudo:
                desatualizados.append(f"{relativo}:{primeira_diferenca(atual, conteudo)}: difere do gerado a partir de catalogo/")
        if desatualizados:
            print("ERRO: arquivos gerados desatualizados ou editados à mão:", file=sys.stderr)
            for linha in desatualizados:
                print(f"  {linha}", file=sys.stderr)
            print("Edite catalogo/<categoria>.yml (nunca o README.md) e rode: python3 tools/build_dataset.py",
                  file=sys.stderr)
            return 1
        print("OK: catálogo válido e arquivos gerados atualizados.")
        return 0

    if not args.report:
        for relativo, conteudo in saidas.items():
            grava(raiz / relativo, conteudo)
            print(f"escrito {relativo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
