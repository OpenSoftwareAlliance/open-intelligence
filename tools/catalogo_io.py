"""Leitura e validação do catálogo em catalogo/ (fonte de verdade).

catalogo/_categorias.yml   manifesto: ordem e apresentação das categorias
catalogo/<categoria>.yml   fontes de uma categoria, na ordem de exibição

Toda mensagem de erro começa com "arquivo:linha: ", com a linha do YAML
onde está o valor com problema (ou o objeto que o contém).
"""

import json
import re
from pathlib import Path

from esquema import valida
from yaml_linhas import erro_em, le_yaml, linha_de

RAIZ = Path(__file__).resolve().parent.parent
MANIFESTO = "_categorias.yml"

# Mesma regra de URL do parser anterior à spec 001, para o campo 'markdown'.
RE_URL = re.compile(r"https?://[^\s<>()\[\]\"`'|,]+")
RE_FENCE = re.compile(r"^\s*```")


def carrega_json(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def normaliza_url(url):
    """Remove fragmento vazio e pontuação grudados no fim da URL."""
    return re.sub(r"#+$", "", url.strip()).rstrip(".,;:!)")


def urls_do_markdown(texto):
    """URLs do texto fora de blocos de código (```), normalizadas."""
    urls, em_fence = set(), False
    for linha in texto.split("\n"):
        if RE_FENCE.match(linha):
            em_fence = not em_fence
        elif not em_fence:
            urls.update(normaliza_url(u) for u in RE_URL.findall(linha))
    return urls - {""}


def carrega_catalogo(raiz=RAIZ):
    """Lê e valida catalogo/. Retorna (catalogo, erros).

    catalogo = {"categorias": [entrada do manifesto, ...],
                "fontes": {categoria_id: [fonte, ...]}}
    Com qualquer erro, catalogo é None.
    """
    raiz = Path(raiz)
    pasta = raiz / "catalogo"
    taxonomia = carrega_json(raiz / "data" / "taxonomy.json")
    esquema_categoria = carrega_json(raiz / "data" / "schemas" / "catalogo.schema.json")
    esquema_manifesto = carrega_json(raiz / "data" / "schemas" / "categorias.schema.json")
    termos = {eixo: set(taxonomia[eixo]["termos"]) for eixo in ("input", "output", "tipo_fonte", "classificacao")}

    rotulo_manifesto = f"catalogo/{MANIFESTO}"
    caminho_manifesto = pasta / MANIFESTO
    if not caminho_manifesto.exists():
        return None, [f"{rotulo_manifesto}:1: manifesto não encontrado"]
    manifesto, linhas_manifesto, erros = le_yaml(caminho_manifesto.read_text(encoding="utf-8"), rotulo_manifesto)
    if erros:
        return None, erros
    erros = [erro_em(rotulo_manifesto, linhas_manifesto, c, m) for c, m in valida(manifesto, esquema_manifesto)]
    if erros:
        return None, erros

    categorias = manifesto["categorias"]
    vistos = {}
    for i, categoria in enumerate(categorias):
        for campo in ("id", "ancora"):
            chave = (campo, categoria[campo])
            if chave in vistos:
                erros.append(erro_em(rotulo_manifesto, linhas_manifesto, ("categorias", i, campo),
                                     f"{campo} '{categoria[campo]}' repetido; já usado na linha {vistos[chave]}"))
            else:
                vistos[chave] = linha_de(linhas_manifesto, ("categorias", i, campo))

    ids_manifesto = {c["id"] for c in categorias}
    for arquivo in sorted(pasta.iterdir()):
        if arquivo.name == MANIFESTO:
            continue
        if arquivo.suffix != ".yml":
            erros.append(f"catalogo/{arquivo.name}:1: arquivo inesperado; o catálogo só aceita arquivos .yml")
        elif arquivo.stem not in ids_manifesto:
            erros.append(f"catalogo/{arquivo.name}:1: categoria '{arquivo.stem}' fora do manifesto {rotulo_manifesto}")

    fontes = {}
    ids_vistos = {}
    for i, categoria in enumerate(categorias):
        caminho = pasta / f"{categoria['id']}.yml"
        rotulo = f"catalogo/{caminho.name}"
        if not caminho.exists():
            erros.append(erro_em(rotulo_manifesto, linhas_manifesto, ("categorias", i),
                                 f"categoria '{categoria['id']}' sem arquivo {rotulo}"))
            continue
        dados, linhas, erros_yaml = le_yaml(caminho.read_text(encoding="utf-8"), rotulo)
        if erros_yaml:
            erros.extend(erros_yaml)
            continue
        erros_esquema = [erro_em(rotulo, linhas, c, m) for c, m in valida(dados, esquema_categoria)]
        if erros_esquema:
            erros.extend(erros_esquema)
            continue
        for j, fonte in enumerate(dados["fontes"]):
            base = ("fontes", j)
            for eixo in ("input", "output"):
                for k, termo in enumerate(fonte[eixo]):
                    if termo not in termos[eixo]:
                        erros.append(erro_em(rotulo, linhas, base + (eixo, k),
                                             f"{eixo} '{termo}' fora da taxonomia (data/taxonomy.json)"))
            for eixo in ("tipo_fonte", "classificacao"):
                if fonte[eixo] not in termos[eixo]:
                    erros.append(erro_em(rotulo, linhas, base + (eixo,),
                                         f"{eixo} '{fonte[eixo]}' fora da taxonomia (data/taxonomy.json)"))
            urls_md = urls_do_markdown(fonte.get("markdown", ""))
            for k, link in enumerate(fonte["links"]):
                if link.get("em_markdown") and link["url"] not in urls_md:
                    erros.append(erro_em(rotulo, linhas, base + ("links", k, "em_markdown"),
                                         f"link {link['url']} marcado em_markdown, mas a URL não aparece no campo markdown"))
            for url in sorted(urls_md - {link["url"] for link in fonte["links"]}):
                erros.append(erro_em(rotulo, linhas, base + ("markdown",),
                                     f"URL {url} no campo markdown sem link correspondente em links"))
            local = f"{rotulo}:{linha_de(linhas, base + ('id',))}"
            if fonte["id"] in ids_vistos:
                erros.append(erro_em(rotulo, linhas, base + ("id",),
                                     f"id '{fonte['id']}' repetido; já usado em {ids_vistos[fonte['id']]}"))
            else:
                ids_vistos[fonte["id"]] = local
        fontes[categoria["id"]] = dados["fontes"]

    if erros:
        return None, erros
    return {"categorias": categorias, "fontes": fontes}, []
