"""Catálogo mínimo de teste, montado numa pasta temporária.

cria_repo(destino) escreve um repositório com duas categorias (alfa, beta),
a taxonomia e os schemas reais do projeto e trechos fixos curtos do README.
As linhas dos arquivos abaixo são citadas nos testes: ao mudar um texto,
confira as linhas esperadas.
"""

import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

MANIFESTO = """\
categorias:
  - id: alfa
    titulo: Alfa
    emoji: 🅰️
    ancora: alfa
    sumario: Alfa
    introducao: |-
      Introdução da categoria alfa.
  - id: beta
    titulo: Beta (Teste)
    ancora: beta
    sumario: Beta
"""

ALFA = """\
fontes:
  - id: alfa/primeira-fonte
    nome: Primeira Fonte
    descricao: Descrição da primeira.
    links:
      - url: https://primeira.gov.br/
    input: [cpf]
    output: [dados_cadastrais]
    tipo_fonte: federal
    classificacao: heuristica
  - id: alfa/segunda-fonte
    nome: Segunda Fonte
    descricao: ''
    subsecao: Subgrupo
    resumo: Links de pesquisa
    links:
      - url: https://segunda.sp.gov.br/
        label: Portal
        uf: SP
      - url: https://segunda.rj.gov.br/
        grupo: '**Rio de Janeiro (RJ)**'
        uf: RJ
    input: [nome]
    output: [processo]
    tipo_fonte: estadual
    classificacao: override
    observacao: Nota da curadoria.
    markdown: |-
      ```bash
      curl https://segunda.sp.gov.br/api
      ```
"""

BETA = """\
fontes:
  - id: beta/terceira-fonte
    nome: Terceira Fonte
    descricao: Descrição da terceira.
    links:
      - url: https://terceira.org.br/
    input: [nenhum]
    output: [dataset]
    tipo_fonte: ong
    classificacao: heuristica
"""

CABECALHO = "# Cabeçalho de teste\n\n---\n"
RODAPE = "## Créditos <a name=\"creditos\"></a>\n\nObrigado.\n"


def cria_repo(destino, arquivos=None):
    """Monta o repositório de teste em 'destino' e devolve o caminho.

    'arquivos' sobrepõe ou acrescenta arquivos: {"catalogo/alfa.yml": "texto"}.
    Valor None remove o arquivo.
    """
    destino = Path(destino)
    (destino / "data" / "schemas").mkdir(parents=True)
    shutil.copy(RAIZ / "data" / "taxonomy.json", destino / "data" / "taxonomy.json")
    for nome in ("catalogo.schema.json", "categorias.schema.json"):
        shutil.copy(RAIZ / "data" / "schemas" / nome, destino / "data" / "schemas" / nome)
    base = {
        "catalogo/_categorias.yml": MANIFESTO,
        "catalogo/alfa.yml": ALFA,
        "catalogo/beta.yml": BETA,
        "tools/readme/cabecalho.md": CABECALHO,
        "tools/readme/rodape.md": RODAPE,
    }
    base.update(arquivos or {})
    for relativo, texto in base.items():
        if texto is None:
            continue
        caminho = destino / relativo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8")
    return destino
