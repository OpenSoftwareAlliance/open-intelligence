#!/usr/bin/env python3
"""Migração de uso único (spec 001): README.md + data/overrides.json -> catalogo/.

Reaproveita o parser e a classificação antigos (readme_legado.py, cópia do
build_dataset.py anterior à spec 001) e congela o resultado em YAML:

    catalogo/_categorias.yml     manifesto (ordem, título, emoji, âncora, sumário, introdução)
    catalogo/<categoria>.yml     fontes com id, links e classificação explícitos
    tools/readme/cabecalho.md    trecho fixo antes do sumário
    tools/readme/rodape.md       trecho fixo depois do catálogo

Antes de terminar, relê catalogo/ e confere que o dataset gerado a partir
dele é idêntico ao que o parser antigo extrai do README. Fica versionado só
para auditoria; depois da migração não deve ser rodado de novo.

Uso:
    python3 tools/migracao/migrar_readme.py
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent))

import readme_legado as L  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402
from dataset import CABECALHO, RODAPE, monta_fontes  # noqa: E402
from readme_gerado import VOLTAR, renderiza_fonte  # noqa: E402

RAIZ = AQUI.parent.parent

RE_ANCORA_NOME = re.compile(r"<a\s+name=[\"']([^\"']*)[\"']", re.I)
RE_ITEM_SUMARIO = re.compile(r"^- \[(.*)\]\(#([^)]+)\)$")
RE_TITULO = re.compile(r"^(#{1,6})\s+(.*)$")
RE_TAG_DETAILS = re.compile(r"^\s*(<details>|</details>|<summary>.*</summary>)\s*$", re.I)
RE_SUMMARY = re.compile(r"<summary>(.*)</summary>", re.I)
RESUMO_PADRAO = "Links de pesquisa"
RE_PALAVRA = re.compile(r"\w+")


class ErroMigracao(Exception):
    pass


# --------------------------------------------------------------------------
# Extração
# --------------------------------------------------------------------------

def extrai_fontes_legado(texto, overrides, taxonomia):
    """Fontes como o build antigo as produzia: ids, links e classificação."""
    fontes, _, orfas = L.parse_readme(texto)
    if orfas:
        raise ErroMigracao(f"README.md:{orfas[0]['linha']}: URL órfã {orfas[0]['url']}")
    fontes = [L.classifica(f, overrides) for f in L.atribui_ids(fontes)]
    erros = L.valida(fontes, taxonomia)
    if erros:
        raise ErroMigracao(erros[0])
    return fontes


def decoracao(titulo):
    """Emoji e demais decorações de um título, na ordem em que aparecem."""
    return "".join(ch for ch in L.RE_ANCHOR.sub("", titulo) if L.eh_decoracao(ch)).strip()


def divide_corpo(linhas, inicio, fim):
    """Linhas [inicio, fim) sem as linhas em branco das pontas."""
    trecho = linhas[inicio:fim]
    while trecho and not trecho[0].strip():
        trecho = trecho[1:]
    while trecho and not trecho[-1].strip():
        trecho = trecho[:-1]
    return trecho


def spans_details(corpo):
    """[(abre, fecha, tem_link)] de cada bloco <details> do corpo, fora de code fences."""
    spans, abre, em_fence = [], None, False
    for i, linha in enumerate(corpo):
        if L.RE_FENCE.match(linha):
            em_fence = not em_fence
            continue
        if em_fence:
            continue
        if L.RE_DETAILS_ABRE.search(linha) and abre is None:
            abre = i
        if L.RE_DETAILS_FECHA.search(linha) and abre is not None:
            spans.append([abre, i, False])
            abre = None
    if abre is not None:
        spans.append([abre, len(corpo) - 1, False])
    for span in spans:
        fence = False
        for linha in corpo[span[0]:span[1] + 1]:
            if L.RE_FENCE.match(linha):
                fence = not fence
            elif not fence and L.urls_da_linha(linha):
                span[2] = True
    return spans


def fichas(texto):
    """Palavras e crases do texto, fora de URLs e das tags <details>/<summary>."""
    texto = L.RE_URL.sub(" ", texto)
    contagem = Counter(p.lower() for p in RE_PALAVRA.findall(texto))
    contagem["`"] = texto.count("`")
    for tag in ("details", "summary"):
        contagem.pop(tag, None)
    return contagem


def decompoe_fonte(fonte, corpo, n0):
    """Campos do YAML (links, resumo, markdown) para o corpo de uma fonte.

    Usa o layout estruturado quando o corpo não tem bloco de código nem
    tabela e o layout reproduz todo o texto dele. Senão (exemplos de API,
    crases de dorks, texto depois da URL, URL com vírgula), guarda o corpo
    literal em 'markdown', sem as linhas da descrição, e marca os links com
    em_markdown para não repeti-los na lista.
    """
    links, resumo, markdown, linhas_descricao = estrutura_fonte(fonte, corpo, n0)
    candidato = registro_yaml(fonte, links, resumo, markdown, None)
    tem_bloco = any(L.RE_FENCE.match(linha) or linha.strip().startswith("|") for linha in corpo)
    if not tem_bloco and not fichas("\n".join(corpo)) - fichas("\n".join(renderiza_fonte(candidato))):
        return links, resumo, markdown
    literal = [linha.rstrip() for i, linha in enumerate(corpo) if i not in linhas_descricao]
    literal = divide_corpo(literal, 0, len(literal))
    links = [dict(link, em_markdown=True) for link in fonte["links"]]
    return links, None, "\n".join(literal)


def estrutura_fonte(fonte, corpo, n0):
    """Separa o corpo Markdown de uma fonte em campos do YAML.

    Repete a máquina de estados de readme_legado.parse_readme para saber que
    linha virou descrição, link ou rótulo de link. O resto vira 'grupo' do
    link seguinte ou, sem link depois, o campo 'markdown'. 'n0' é o número
    da primeira linha do corpo no README, para as mensagens de erro.
    Retorna (links, resumo, markdown, índices das linhas da descrição).
    """
    links = [dict(link) for link in fonte["links"]]
    proximo = 0
    descricao, grupo, residuo = [], [], []
    linhas_descricao = set()
    pendente = None  # (indentação, texto da linha) de bullet sem URL
    em_details = False

    spans = spans_details(corpo)
    com_link = [s for s in spans if s[2]]
    sem_link = {s[0]: s[1] for s in spans if not s[2]}
    varios = len(com_link) > 1
    resumo = None
    if len(com_link) == 1:
        m = RE_SUMMARY.search("\n".join(corpo[com_link[0][0]:com_link[0][1] + 1]))
        resumo = m.group(1).strip() if m else RESUMO_PADRAO
    elif varios:
        resumo = RESUMO_PADRAO

    def solta_pendente():
        nonlocal pendente
        if pendente:
            grupo.append(pendente[1])
        pendente = None

    i = 0
    while i < len(corpo):
        crua = corpo[i].rstrip()
        n = n0 + i
        if i in sem_link:
            fim = sem_link[i]
            residuo.append([l.rstrip() for l in corpo[i:fim + 1]])
            i = fim + 1
            continue
        if L.RE_FENCE.match(crua):
            bloco = [crua]
            i += 1
            while i < len(corpo) and not L.RE_FENCE.match(corpo[i]):
                bloco.append(corpo[i].rstrip())
                i += 1
            if i < len(corpo):
                bloco.append(corpo[i].rstrip())
            residuo.append(bloco)
            i += 1
            continue
        if L.RE_DETAILS_ABRE.search(crua):
            em_details = True
        if L.RE_DETAILS_FECHA.search(crua):
            em_details = False
        if RE_TAG_DETAILS.match(crua):
            m = RE_SUMMARY.search(crua)
            if m and varios:
                grupo.append(f"**{m.group(1).strip()}**")
            i += 1
            continue

        urls = L.urls_da_linha(crua)
        if not urls:
            texto = crua.strip()
            m_bullet = L.RE_BULLET.match(crua)
            if L.RE_GRUPO_UF.match(texto) or L.RE_GRUPO_BOLD.match(texto):
                solta_pendente()
                grupo.append(texto)
            elif m_bullet:
                solta_pendente()
                pendente = (len(m_bullet.group(1)), texto)
            elif texto:
                if proximo == 0 and not em_details:
                    descricao.append(texto)
                    linhas_descricao.add(i)
                else:
                    grupo.append(texto)
            i += 1
            continue

        m_bullet = L.RE_BULLET.match(crua)
        indent = len(m_bullet.group(1)) if m_bullet else 0
        extraidos = [(u, r) for u, r in L.extrai_links(crua) if not L.eh_ignorada(u)]
        if len(extraidos) != len(L.extrai_links(crua)):
            raise ErroMigracao(f"README.md:{n}: badge dentro do corpo de uma fonte")
        usou_pendente = any(not r and pendente and indent > pendente[0] for _, r in extraidos)
        if pendente and not usou_pendente:
            grupo.append(pendente[1])
        pendente = None
        primeiro = proximo
        for url, _ in extraidos:
            if proximo >= len(links) or links[proximo]["url"] != url:
                raise ErroMigracao(f"README.md:{n}: link {url} fora da ordem do parser")
            proximo += 1
        if grupo and extraidos:
            links[primeiro]["grupo"] = "\n".join(grupo)
            grupo = []
        i += 1

    solta_pendente()
    if grupo:
        residuo.append(grupo)
    if proximo != len(links):
        raise ErroMigracao(f"README.md:{n0}: {len(links) - proximo} links de '{fonte['id']}' não encontrados no corpo")
    if " ".join(descricao).strip() != fonte["descricao"]:
        raise ErroMigracao(f"README.md:{n0}: descrição de '{fonte['id']}' diverge do parser")
    markdown = "\n\n".join("\n".join(bloco) for bloco in residuo)
    return links, resumo, markdown, linhas_descricao


def registro_yaml(fonte, links, resumo, markdown, subsecao):
    registro = {"id": fonte["id"], "nome": fonte["nome"], "descricao": fonte["descricao"]}
    if subsecao:
        registro["subsecao"] = subsecao
    if resumo:
        registro["resumo"] = resumo
    registro["links"] = []
    for link in links:
        item = {}
        if link.get("grupo"):
            item["grupo"] = link["grupo"]
        item["url"] = link["url"]
        if link["label"]:
            item["label"] = link["label"]
        if link["uf"]:
            item["uf"] = link["uf"]
        if link.get("em_markdown"):
            item["em_markdown"] = True
        registro["links"].append(item)
    registro["input"] = ListaCurta(fonte["input"])
    registro["output"] = ListaCurta(fonte["output"])
    registro["tipo_fonte"] = fonte["tipo_fonte"]
    registro["classificacao"] = fonte["classificacao"]
    if "observacao" in fonte:
        registro["observacao"] = fonte["observacao"]
    if markdown:
        registro["markdown"] = markdown
    return registro


def migra(texto, overrides, taxonomia):
    """Converte o README em (manifesto, {categoria_id: [fonte]}, cabecalho, rodape)."""
    fontes = extrai_fontes_legado(texto, overrides, taxonomia)
    por_linha = {f["_readme_linha"]: f for f in fontes}
    linhas = texto.splitlines()

    titulos = [(i, len(m.group(1)), m.group(2)) for i, l in enumerate(linhas) if (m := RE_TITULO.match(l))]
    i_sumario = next(i for i, l in enumerate(linhas) if l.strip() == "# Sumário")
    cabecalho = "\n".join(linhas[:i_sumario]) + "\n"

    sumario = {}
    for linha in linhas[i_sumario + 1:]:
        if linha.startswith("## "):
            break
        m = RE_ITEM_SUMARIO.match(linha.strip())
        if m:
            sumario.setdefault(m.group(2), m.group(1))

    secoes = [(i, t) for i, nivel, t in titulos if nivel == 2 and i > i_sumario]
    i_rodape = next(i for i, t in secoes if L.slug(L.limpa_titulo(t)) in L.CATEGORIAS_IGNORADAS)
    rodape = "\n".join(linhas[i_rodape:]) + ("\n" if texto.endswith("\n") else "")

    manifesto, catalogo = [], {}
    for k, (i, titulo_cru) in enumerate(secoes):
        if i >= i_rodape:
            break
        fim_secao = secoes[k + 1][0] if k + 1 < len(secoes) else i_rodape
        titulo = L.limpa_titulo(titulo_cru)
        categoria_id = L.slug(titulo)
        m = RE_ANCORA_NOME.search(titulo_cru)
        if not m:
            raise ErroMigracao(f"README.md:{i + 1}: categoria sem <a name>")
        ancora = m.group(1)
        if categoria_id not in catalogo:
            entrada = {"id": categoria_id, "titulo": titulo}
            if decoracao(titulo_cru):
                entrada["emoji"] = decoracao(titulo_cru)
            entrada["ancora"] = ancora
            entrada["sumario"] = sumario.get(ancora, titulo)
            manifesto.append(entrada)
            catalogo[categoria_id] = []
        elif ancora != next(e["ancora"] for e in manifesto if e["id"] == categoria_id):
            raise ErroMigracao(f"README.md:{i + 1}: seção repetida '{titulo}' com outra âncora")

        internos = [(j, nivel, t) for j, nivel, t in titulos if i < j < fim_secao]
        fim_intro = internos[0][0] if internos else fim_secao
        if i + 1 in por_linha:
            # Links soltos logo abaixo do ##: fonte implícita com o nome da categoria.
            alvos = [(i, fim_intro)]
        else:
            intro = divide_corpo(linhas, i + 1, fim_intro)
            if intro:
                entrada = next(e for e in manifesto if e["id"] == categoria_id)
                if "introducao" in entrada:
                    raise ErroMigracao(f"README.md:{i + 1}: introdução na segunda seção '{titulo}'")
                entrada["introducao"] = "\n".join(l.rstrip() for l in intro)
            alvos = []

        subsecao = None
        for x, (j, nivel, t) in enumerate(internos):
            fim = internos[x + 1][0] if x + 1 < len(internos) else fim_secao
            if nivel == 3:
                alvos.append((j, fim))
            elif nivel == 4:
                if divide_corpo(linhas, j + 1, fim):
                    raise ErroMigracao(f"README.md:{j + 1}: texto entre subtítulo #### e a fonte seguinte")
                alvos.append((j, None))
            elif linhas[j].strip() != VOLTAR or [l for l in linhas[j + 1:fim] if l.strip() not in ("", "---")]:
                raise ErroMigracao(f"README.md:{j + 1}: conteúdo inesperado no fim da categoria")

        for j, fim in alvos:
            if fim is None:
                subsecao = linhas[j].lstrip("#").strip()
                continue
            fonte = por_linha.pop(j + 1)
            if fonte["categoria_id"] != categoria_id:
                raise ErroMigracao(f"README.md:{j + 1}: fonte fora da categoria esperada")
            corpo = linhas[j + 1:fim]
            links, resumo, markdown = decompoe_fonte(fonte, corpo, j + 2)
            catalogo[categoria_id].append(registro_yaml(fonte, links, resumo, markdown, subsecao))
            subsecao = None
        if subsecao:
            raise ErroMigracao(f"README.md:{i + 1}: subtítulo #### sem fonte depois")

    if por_linha:
        primeira = min(por_linha)
        raise ErroMigracao(f"README.md:{primeira}: fonte não alocada a nenhuma categoria")
    return manifesto, catalogo, cabecalho, rodape


# --------------------------------------------------------------------------
# Escrita
# --------------------------------------------------------------------------

class ListaCurta(list):
    """Lista de termos escrita numa linha só: [cpf, nome]."""


class Escritor(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _texto(dumper, valor):
    estilo = "|" if "\n" in valor else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", valor, style=estilo)


def _lista_curta(dumper, valor):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", list(valor), flow_style=True)


Escritor.add_representer(str, _texto)
Escritor.add_representer(ListaCurta, _lista_curta)


def para_yaml(dados):
    return yaml.dump(dados, Dumper=Escritor, allow_unicode=True, sort_keys=False, width=10**6)


def escreve(raiz, manifesto, catalogo, cabecalho, rodape):
    raiz = Path(raiz)
    pasta = raiz / "catalogo"
    pasta.mkdir(exist_ok=True)
    (pasta / "_categorias.yml").write_text(
        "# Manifesto do catálogo: ordem das categorias no README.md e apresentação de cada uma.\n"
        "# Cada id corresponde a catalogo/<id>.yml. Formato: data/schemas/categorias.schema.json\n"
        + para_yaml({"categorias": manifesto}),
        encoding="utf-8",
    )
    for entrada in manifesto:
        (pasta / f"{entrada['id']}.yml").write_text(
            f"# Categoria: {entrada['titulo']}\n"
            "# Fontes na ordem de exibição no README.md. Formato: data/schemas/catalogo.schema.json\n"
            "# Depois de editar, rode: python3 tools/build_dataset.py\n"
            + para_yaml({"fontes": catalogo[entrada["id"]]}),
            encoding="utf-8",
        )
    for relativo, texto in ((CABECALHO, cabecalho), (RODAPE, rodape)):
        caminho = raiz / relativo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8")


def confere(raiz, fontes_legado):
    """Relê catalogo/ e exige o mesmo dataset que o parser antigo produz."""
    catalogo, erros = carrega_catalogo(raiz)
    if erros:
        raise ErroMigracao("catálogo migrado inválido:\n  " + "\n  ".join(erros[:20]))
    novas = {f["id"]: f for f in monta_fontes(catalogo)}
    for antiga in fontes_legado:
        esperado = {k: v for k, v in antiga.items() if not k.startswith("_")}
        if novas.get(antiga["id"]) != esperado:
            raise ErroMigracao(f"README.md:{antiga['_readme_linha']}: '{antiga['id']}' muda depois da migração")
    if len(novas) != len(fontes_legado):
        raise ErroMigracao(f"{len(novas)} fontes no catálogo, {len(fontes_legado)} no README")
    return catalogo


def main(argv=None, raiz=RAIZ):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args(argv)
    raiz = Path(raiz)
    texto = (raiz / "README.md").read_text(encoding="utf-8")
    overrides = L.carrega_json(raiz / "data" / "overrides.json").get("overrides", {})
    taxonomia = L.carrega_json(raiz / "data" / "taxonomy.json")
    try:
        manifesto, catalogo, cabecalho, rodape = migra(texto, overrides, taxonomia)
        escreve(raiz, manifesto, catalogo, cabecalho, rodape)
        confere(raiz, extrai_fontes_legado(texto, overrides, taxonomia))
    except ErroMigracao as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    total = sum(len(f) for f in catalogo.values())
    links = sum(len(f["links"]) for fs in catalogo.values() for f in fs)
    print(f"migrado: {len(manifesto)} categorias, {total} fontes, {links} links em catalogo/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
