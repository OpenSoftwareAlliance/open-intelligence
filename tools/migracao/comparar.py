#!/usr/bin/env python3
"""Compara o estado antes e depois da migração da spec 001 (CA1 a CA5).

"Antes" é lido do git (README.md, data/*.json e documentos no commit de
referência); "depois" é o diretório de trabalho atual. Sem --ref, a
referência é o pai do commit que criou catalogo/_categorias.yml.

Verifica:
    CA1  catalogo/ tem um arquivo por categoria_id anterior, mais o manifesto
    CA2  sources.json e index.json iguais, exceto '_sobre', 'fonte', a ordem
         das fontes de categorias que tinham duas seções (R13) e descrição
         reduzida ao seu início quando o resto foi para o campo markdown
    CA3  totais de fontes, links e classificação; mesmos ids
    CA4  mesmo conjunto de URLs no README.md
    CA5  toda âncora <a name> anterior existe; links README.md#x dos demais
         documentos que resolviam continuam resolvendo

Uso:
    python3 tools/migracao/comparar.py [--ref COMMIT]
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from readme_legado import urls_da_linha  # noqa: E402

RAIZ = AQUI.parent.parent
OUTROS_DOCS = ["README.en.md", "GUIA_RAPIDO.md", "EXEMPLOS_PRATICOS.md", "FLUXOGRAMA.md", "CONTRIBUICAO.md"]
RE_ANCORA = re.compile(r'<a name="([^"]+)"')
RE_LINK_README = re.compile(r"\]\(README\.md#([^)]+)\)")


def git(raiz, *args):
    return subprocess.run(["git", *args], cwd=raiz, check=True, capture_output=True, text=True).stdout


def ref_antes(raiz):
    criacao = git(raiz, "log", "--diff-filter=A", "--format=%H", "--", "catalogo/_categorias.yml").split()
    if not criacao:
        raise SystemExit("catalogo/_categorias.yml ainda não está em nenhum commit; use --ref")
    return criacao[-1] + "^"


def ordem_esperada(registros, chave):
    """Ordem antiga com cada categoria agrupada na posição da sua primeira seção (R13)."""
    posicao = {}
    for r in registros:
        posicao.setdefault(r[chave], len(posicao))
    return sorted(registros, key=lambda r: posicao[r[chave]])


def aceita_descricao_movida(antes, depois, lista):
    """Descrição que passou a ser só o início da anterior (o resto foi para o campo markdown)."""
    por_chave = {(r.get("id"), r.get("url")): r for r in depois[lista]}
    for r in antes[lista]:
        novo = por_chave.get((r.get("id"), r.get("url")))
        if novo and r.get("descricao") and novo.get("descricao") != r["descricao"] and r["descricao"].startswith(novo["descricao"] + " "):
            r["descricao"] = novo["descricao"]


def compara_json(antes, depois, lista):
    erros = []
    aceita_descricao_movida(antes, depois, lista)
    for doc in (antes, depois):
        doc.pop("_sobre", None)
        doc.pop("fonte", None)
    if antes["total"] != depois["total"]:
        erros.append(f"total {antes['total']} -> {depois['total']}")
    if ordem_esperada(antes[lista], "categoria_id") != depois[lista]:
        a = ordem_esperada(antes[lista], "categoria_id")
        for i, (x, y) in enumerate(zip(a, depois[lista])):
            if x != y:
                erros.append(f"{lista}[{i}] difere: {x.get('id') or x.get('url')}")
                break
        else:
            erros.append(f"{lista}: tamanhos diferentes")
    return erros


def urls(texto):
    return {u for linha in texto.splitlines() for u in urls_da_linha(linha)}


def slug_github(titulo):
    titulo = re.sub(r"<[^>]+>", "", titulo)
    titulo = re.sub(r"[^\w\s-]", "", titulo.strip().lower(), flags=re.UNICODE)
    return re.sub(r"\s+", "-", titulo).strip("-")


def ancoras(texto):
    nomes = set(RE_ANCORA.findall(texto))
    titulos = {slug_github(t) for t in re.findall(r"^#{1,6}\s+(.*)$", texto, re.M)}
    return nomes, nomes | titulos


def resolve(alvo, todas):
    return alvo in todas or alvo.lower() in todas


def compara(antes, depois, categorias_arquivos):
    """antes/depois: {"README.md": str, "data/sources.json": str, ...}. Retorna (erros, resumo)."""
    erros, resumo = [], []
    s_antes = json.loads(antes["data/sources.json"])
    s_depois = json.loads(depois["data/sources.json"])
    i_antes = json.loads(antes["data/index.json"])
    i_depois = json.loads(depois["data/index.json"])

    ids_categoria = {f["categoria_id"] for f in s_antes["sources"]}
    if set(categorias_arquivos) != ids_categoria:
        erros.append(f"CA1: arquivos de categoria {sorted(set(categorias_arquivos) ^ ids_categoria)} não batem com categoria_id")
    resumo.append(f"CA1 categorias: {len(categorias_arquivos)} arquivos + manifesto")

    classes = Counter(f["classificacao"] for f in s_depois["sources"])
    ids_iguais = {f["id"] for f in s_antes["sources"]} == {f["id"] for f in s_depois["sources"]}
    if not ids_iguais:
        erros.append("CA3: conjunto de ids mudou")
    resumo.append(
        f"CA3 fontes: {s_depois['total']} | links: {i_depois['total']} | "
        f"heuristica: {classes['heuristica']} | override: {classes['override']} | ids iguais: {ids_iguais}"
    )

    erros_ca2 = [f"CA2 sources.json: {e}" for e in compara_json(s_antes, s_depois, "sources")]
    erros_ca2 += [f"CA2 index.json: {e}" for e in compara_json(i_antes, i_depois, "links")]
    erros += erros_ca2
    resumo.append("CA2 sources.json e index.json: " + ("DIFERENTES" if erros_ca2 else
                  "iguais exceto _sobre, fonte e a ordem das categorias com duas seções"))

    u_antes, u_depois = urls(antes["README.md"]), urls(depois["README.md"])
    if u_antes != u_depois:
        erros.append(f"CA4: URLs só antes {sorted(u_antes - u_depois)[:5]}, só depois {sorted(u_depois - u_antes)[:5]}")
    resumo.append(f"CA4 URLs no README: {len(u_antes)} antes, {len(u_depois)} depois")

    nomes_antes, todas_antes = ancoras(antes["README.md"])
    nomes_depois, todas_depois = ancoras(depois["README.md"])
    faltando = sorted(nomes_antes - nomes_depois)
    if faltando:
        erros.append(f"CA5: âncoras <a name> sumiram: {faltando}")
    quebrados_antes = 0
    for doc in OUTROS_DOCS:
        for alvo in RE_LINK_README.findall(antes.get(doc, "")):
            if not resolve(alvo, todas_antes):
                quebrados_antes += 1
            elif not resolve(alvo, todas_depois):
                erros.append(f"CA5: {doc} -> README.md#{alvo} deixou de resolver")
    resumo.append(f"CA5 âncoras <a name>: {len(nomes_antes)} antes, {len(nomes_depois)} depois "
                  f"| links de outros documentos já quebrados antes: {quebrados_antes}")
    return erros, resumo


def main(argv=None, raiz=RAIZ):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", help="commit com o estado anterior à migração")
    args = ap.parse_args(argv)
    raiz = Path(raiz)
    ref = args.ref or ref_antes(raiz)
    arquivos = ["README.md", "data/sources.json", "data/index.json"] + OUTROS_DOCS
    antes = {a: git(raiz, "show", f"{ref}:{a}") for a in arquivos}
    depois = {a: (raiz / a).read_text(encoding="utf-8") for a in arquivos}
    categorias = sorted(p.stem for p in (raiz / "catalogo").glob("*.yml") if p.name != "_categorias.yml")
    erros, resumo = compara(antes, depois, categorias)
    print(f"referência: {ref}")
    for linha in resumo:
        print(linha)
    if erros:
        print("\nERROS:", file=sys.stderr)
        for e in erros:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("\nOK: migração preserva o catálogo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
