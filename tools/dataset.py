"""Monta os arquivos gerados a partir do catálogo validado.

    README.md           catálogo legível, com trechos fixos de tools/readme/
    data/sources.json   uma entrada por fonte, com links aninhados
    data/index.json     um registro por link, achatado para busca

O esquema dos dois JSON é o mesmo de antes da spec 001; só '_sobre' e
'fonte' mudam, porque a origem passou a ser catalogo/.
"""

import json
from pathlib import Path

from readme_gerado import gera_readme

FONTE = "catalogo/"
SOBRE_SOURCES = (
    "GERADO por tools/build_dataset.py a partir de catalogo/. "
    "Não editar à mão: edite catalogo/<categoria>.yml."
)
SOBRE_INDEX = "GERADO por tools/build_dataset.py a partir de catalogo/. Índice achatado de links para busca."
CABECALHO = "tools/readme/cabecalho.md"
RODAPE = "tools/readme/rodape.md"


def monta_fontes(catalogo):
    fontes = []
    for categoria in catalogo["categorias"]:
        for fonte in catalogo["fontes"][categoria["id"]]:
            registro = {
                "categoria": categoria["titulo"],
                "categoria_id": categoria["id"],
                "classificacao": fonte["classificacao"],
                "descricao": fonte["descricao"],
                "id": fonte["id"],
                "input": sorted(fonte["input"]),
                "links": [
                    {"label": link.get("label", ""), "uf": link.get("uf"), "url": link["url"]}
                    for link in fonte["links"]
                ],
                "nome": fonte["nome"],
                "output": sorted(fonte["output"]),
                "tipo_fonte": fonte["tipo_fonte"],
            }
            if "observacao" in fonte:
                registro["observacao"] = fonte["observacao"]
            fontes.append(registro)
    return fontes


def monta_index(fontes):
    links = []
    for fonte in fontes:
        for link in fonte["links"]:
            links.append({
                "url": link["url"],
                "label": link["label"],
                "uf": link["uf"],
                "fonte_id": fonte["id"],
                "fonte": fonte["nome"],
                "categoria": fonte["categoria"],
                "categoria_id": fonte["categoria_id"],
                "descricao": fonte["descricao"],
                "tipo_fonte": fonte["tipo_fonte"],
                "input": fonte["input"],
                "output": fonte["output"],
            })
    return links


def serializa(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def gera_saidas(raiz, catalogo):
    """{caminho relativo: conteúdo} dos três arquivos gerados."""
    raiz = Path(raiz)
    fontes = monta_fontes(catalogo)
    links = monta_index(fontes)
    cabecalho = (raiz / CABECALHO).read_text(encoding="utf-8")
    rodape = (raiz / RODAPE).read_text(encoding="utf-8")
    return {
        "README.md": gera_readme(catalogo, cabecalho, rodape),
        "data/sources.json": serializa({"_sobre": SOBRE_SOURCES, "fonte": FONTE, "total": len(fontes), "sources": fontes}),
        "data/index.json": serializa({"_sobre": SOBRE_INDEX, "fonte": FONTE, "total": len(links), "links": links}),
    }
