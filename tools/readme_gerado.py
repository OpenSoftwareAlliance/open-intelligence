"""Gera o README.md a partir do catálogo e dos trechos fixos.

Layout de cada fonte:

    ### <nome>

    <descricao>                         (se não vazia)

    <details>                           (só com 'resumo')
    <summary><resumo></summary>

    <grupo>                             (antes do link que o declara)
    - <label>: <url>   ou   - <url>     (exceto links com em_markdown)

    </details>

    <markdown>                          (se houver, sem alteração)
"""

AVISO = (
    "<!-- ARQUIVO GERADO por tools/build_dataset.py a partir de catalogo/. "
    "Não edite à mão: contribuidores editam catalogo/<categoria>.yml; "
    "os mantenedores regeneram com python3 tools/build_dataset.py -->"
)

VOLTAR = (
    "##### [![](https://img.shields.io/badge/Voltar-Sum%C3%A1rio-1E88E5"
    "?style=flat-square&logo=github&logoColor=white)](#sumário)"
)

# Itens do sumário que apontam para os trechos fixos, depois das categorias.
SUMARIO_FIXO = [
    "- [Autores](#autores)",
    "- [Contribuições](#contribuicoes)",
    "- [Créditos](#creditos)",
]


def renderiza_link(link):
    label = link.get("label")
    return f"- {label}: {link['url']}" if label else f"- {link['url']}"


def separa_linhas_do_grupo(grupo):
    """Linhas do grupo, com linha em branco entre duas linhas de texto seguidas.

    No GitHub, linhas consecutivas sem linha em branco viram um único parágrafo;
    itens de lista ("- ") não precisam da separação.
    """
    saida = []
    for linha in grupo.split("\n"):
        if saida and saida[-1].strip() and linha.strip() and not saida[-1].lstrip().startswith("- ") and not linha.lstrip().startswith("- "):
            saida.append("")
        saida.append(linha)
    return saida


def renderiza_fonte(fonte):
    linhas = [f"### {fonte['nome']}", ""]
    if fonte["descricao"]:
        linhas += [fonte["descricao"], ""]
    visiveis = [link for link in fonte["links"] if not link.get("em_markdown")]
    resumo = fonte.get("resumo") if visiveis else None
    if resumo:
        linhas += ["<details>", f"<summary>{resumo}</summary>", ""]
    for i, link in enumerate(visiveis):
        grupo = link.get("grupo")
        if grupo:
            if i > 0:
                linhas.append("")
            linhas += separa_linhas_do_grupo(grupo)
        linhas.append(renderiza_link(link))
    if visiveis:
        linhas.append("")
    if resumo:
        linhas += ["</details>", ""]
    if fonte.get("markdown"):
        linhas += fonte["markdown"].rstrip("\n").split("\n") + [""]
    return linhas


def renderiza_categoria(categoria, fontes):
    emoji = f" {categoria['emoji']}" if categoria.get("emoji") else ""
    linhas = [f"## {categoria['titulo']}{emoji} <a name=\"{categoria['ancora']}\"></a>", ""]
    if categoria.get("introducao"):
        linhas += categoria["introducao"].rstrip("\n").split("\n") + [""]
    for fonte in fontes:
        if fonte.get("subsecao"):
            linhas += [f"#### {fonte['subsecao']}", ""]
        linhas += renderiza_fonte(fonte)
    linhas += [VOLTAR, "", "---", ""]
    return linhas


def renderiza_sumario(categorias):
    linhas = ["# Sumário", ""]
    linhas += [f"- [{c['sumario']}](#{c['ancora']})" for c in categorias]
    linhas += SUMARIO_FIXO + ["", "---", ""]
    return linhas


def gera_readme(catalogo, cabecalho, rodape):
    """README.md completo: aviso, cabeçalho, sumário, categorias e rodapé."""
    linhas = renderiza_sumario(catalogo["categorias"])
    for categoria in catalogo["categorias"]:
        linhas += renderiza_categoria(categoria, catalogo["fontes"][categoria["id"]])
    return AVISO + "\n" + cabecalho + "\n".join(linhas) + "\n" + rodape
