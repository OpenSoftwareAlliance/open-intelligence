# Tarefas da spec 001: fonte de verdade estruturada

> Roteiro histórico da implementação (PR #2). O código vigente está em `tools/` e `tests/`; em divergência, vale o código. Pendências novas vão para issues.

Plano: [`plan.md`](plan.md). Spec: [`spec.md`](spec.md). ADR: [`0001`](../../adr/0001-yaml-por-categoria-como-fonte-de-verdade.md).

Todos os comandos rodam na raiz do repositório, com o ambiente virtual da preparação ativo (`. .venv/bin/activate`). Cada tarefa termina com um commit assinado (a assinatura GPG vem do `~/.gitconfig`; nunca usar `--no-gpg-sign`). Os números de `Ran N tests` são cumulativos: a suíte inteira cresce a cada tarefa.

## Preparação

- [x] **Passo P1: criar a branch e o ambiente virtual.**

````bash
git switch -c feat/001-fonte-de-verdade-estruturada
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --quiet PyYAML==6.0.3
python3 -c "import yaml; print(yaml.__version__)"
````

Esperado: `6.0.3`. O `.venv/` já está no `.gitignore`.

- [x] **Passo P2: conferir o ponto de partida.**

````bash
python3 tools/build_dataset.py --check | tail -1
git status --porcelain | wc -l | tr -d ' '
````

Esperado: `OK: arquivos gerados estão atualizados.` e `0` (árvore limpa).

---

## Tarefa 1: validador mínimo de JSON Schema e dependência fixada

**Arquivos:**
- Criar: `requirements.txt`, `tools/esquema.py`
- Teste: `tests/test_esquema.py`

**Interfaces:**
- Consome: nada.
- Produz: `valida(valor, esquema, caminho=()) -> list[tuple[tuple, str]]` (pares caminho e mensagem; cobre `type`, `properties`, `required`, `additionalProperties: false`, `items`, `enum`, `pattern`, `minLength`, `minItems`, `uniqueItems`); `formata_caminho(caminho: tuple) -> str` (`("fontes", 3, "url")` vira `fontes[3].url`); `requirements.txt` com `PyYAML==6.0.3`.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_esquema.py`:**

````python
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from esquema import formata_caminho, valida  # noqa: E402

ESQUEMA = {
    "type": "object",
    "required": ["nome", "links"],
    "additionalProperties": False,
    "properties": {
        "nome": {"type": "string", "minLength": 1},
        "uf": {"type": ["string", "null"], "enum": ["SP", "RJ", None]},
        "links": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["url"],
                "properties": {"url": {"type": "string", "pattern": "^https?://\\S+$"}},
            },
        },
        "input": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
    },
}


class TestValida(unittest.TestCase):
    def test_documento_valido_nao_tem_erros(self):
        doc = {"nome": "X", "uf": None, "links": [{"url": "https://a.gov.br/"}], "input": ["cpf"]}
        self.assertEqual(valida(doc, ESQUEMA), [])

    def test_campo_obrigatorio_ausente_aponta_o_objeto(self):
        erros = valida({"links": [{"url": "https://a/"}]}, ESQUEMA)
        self.assertEqual(erros, [((), "campo obrigatório 'nome' ausente")])

    def test_campo_extra_e_recusado(self):
        erros = valida({"nome": "X", "links": [{"url": "https://a/"}], "cor": 1}, ESQUEMA)
        self.assertEqual(erros, [(("cor",), "campo 'cor' não permitido")])

    def test_tipo_errado(self):
        erros = valida({"nome": 3, "links": [{"url": "https://a/"}]}, ESQUEMA)
        self.assertEqual(erros, [(("nome",), "tipo integer, esperado string")])

    def test_lista_vazia_abaixo_do_minimo(self):
        erros = valida({"nome": "X", "links": []}, ESQUEMA)
        self.assertEqual(erros, [(("links",), "lista com 0 itens, mínimo 1")])

    def test_padrao_e_caminho_aninhado(self):
        erros = valida({"nome": "X", "links": [{"url": "ftp://a"}]}, ESQUEMA)
        self.assertEqual(len(erros), 1)
        self.assertEqual(erros[0][0], ("links", 0, "url"))
        self.assertIn("não segue o padrão", erros[0][1])

    def test_enum_e_item_repetido(self):
        erros = valida({"nome": "X", "uf": "XX", "links": [{"url": "https://a/"}], "input": ["cpf", "cpf"]}, ESQUEMA)
        self.assertEqual(erros, [
            (("uf",), "valor 'XX' fora da lista permitida"),
            (("input", 1), "item repetido 'cpf'"),
        ])

    def test_texto_vazio(self):
        erros = valida({"nome": "", "links": [{"url": "https://a/"}]}, ESQUEMA)
        self.assertEqual(erros, [(("nome",), "texto vazio")])

    def test_formata_caminho(self):
        self.assertEqual(formata_caminho(("fontes", 3, "links", 0, "url")), "fontes[3].links[0].url")
        self.assertEqual(formata_caminho(()), "(raiz)")


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_esquema.py
````

Esperado: falha com `ModuleNotFoundError: No module named 'esquema'` ao importar `test_esquema`.

- [x] **Passo 3: implementar. Criar `tools/esquema.py`:**

````python
"""Validador mínimo de JSON Schema, só com a biblioteca padrão.

Cobre o subconjunto usado em data/schemas/catalogo.schema.json e
data/schemas/categorias.schema.json: type, properties, required,
additionalProperties (booleano), items, enum, pattern, minLength,
minItems e uniqueItems. Palavras-chave fora dessa lista são ignoradas.

Cada erro é um par (caminho, mensagem). O caminho é uma tupla de chaves e
índices até o valor com problema, por exemplo ("fontes", 3, "links", 0, "url"),
e serve para achar a linha no arquivo YAML de origem.
"""

import re

TIPOS = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def _tem_tipo(valor, tipo):
    if tipo == "integer":
        return isinstance(valor, int) and not isinstance(valor, bool)
    return isinstance(valor, TIPOS[tipo])


def _nome_tipo(valor):
    for nome, classe in TIPOS.items():
        if isinstance(valor, classe):
            return nome
    if isinstance(valor, int):
        return "integer"
    return type(valor).__name__


def valida(valor, esquema, caminho=()):
    """Retorna a lista de erros (caminho, mensagem) de valor contra esquema."""
    erros = []
    tipo = esquema.get("type")
    if tipo is not None:
        tipos = tipo if isinstance(tipo, list) else [tipo]
        if not any(_tem_tipo(valor, t) for t in tipos):
            esperado = " ou ".join(tipos)
            erros.append((caminho, f"tipo {_nome_tipo(valor)}, esperado {esperado}"))
            return erros

    if "enum" in esquema and valor not in esquema["enum"]:
        erros.append((caminho, f"valor {valor!r} fora da lista permitida"))

    if isinstance(valor, str):
        if len(valor) < esquema.get("minLength", 0):
            erros.append((caminho, "texto vazio"))
        padrao = esquema.get("pattern")
        if padrao and not re.search(padrao, valor):
            erros.append((caminho, f"valor {valor!r} não segue o padrão {padrao}"))

    if isinstance(valor, dict):
        for campo in esquema.get("required", []):
            if campo not in valor:
                erros.append((caminho, f"campo obrigatório '{campo}' ausente"))
        propriedades = esquema.get("properties", {})
        for campo, sub in valor.items():
            if campo in propriedades:
                erros.extend(valida(sub, propriedades[campo], caminho + (campo,)))
            elif esquema.get("additionalProperties") is False:
                erros.append((caminho + (campo,), f"campo '{campo}' não permitido"))

    if isinstance(valor, list):
        if len(valor) < esquema.get("minItems", 0):
            erros.append((caminho, f"lista com {len(valor)} itens, mínimo {esquema['minItems']}"))
        if esquema.get("uniqueItems"):
            vistos = []
            for i, item in enumerate(valor):
                if item in vistos:
                    erros.append((caminho + (i,), f"item repetido {item!r}"))
                vistos.append(item)
        if "items" in esquema:
            for i, item in enumerate(valor):
                erros.extend(valida(item, esquema["items"], caminho + (i,)))

    return erros


def formata_caminho(caminho):
    """("fontes", 3, "links", 0) -> "fontes[3].links[0]"."""
    texto = ""
    for parte in caminho:
        if isinstance(parte, int):
            texto += f"[{parte}]"
        else:
            texto += f".{parte}" if texto else str(parte)
    return texto or "(raiz)"
````

- [x] **Passo 4: fixar a dependência. Criar `requirements.txt`:**

````text
# Única dependência fora da biblioteca padrão (ADR 0001). Versão fixada.
PyYAML==6.0.3
````

- [x] **Passo 5: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 9 tests` e `OK`.

- [x] **Passo 6: commit.**

````bash
git add requirements.txt tools/esquema.py tests/test_esquema.py
git commit -m "Adiciona validador mínimo de JSON Schema e fixa o PyYAML" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 2: leitura de YAML com a linha de origem de cada valor

**Arquivos:**
- Criar: `tools/yaml_linhas.py`
- Teste: `tests/test_yaml_linhas.py`

**Interfaces:**
- Consome: `formata_caminho` (Tarefa 1); PyYAML (`yaml.compose`, `yaml.CSafeLoader` quando existir).
- Produz: `le_yaml(texto: str, rotulo: str) -> tuple[object | None, dict[tuple, int], list[str]]` (dados, linha de cada caminho, erros `rotulo:linha: ...` de sintaxe, arquivo vazio e chave repetida); `linha_de(linhas: dict, caminho: tuple) -> int` (cai no objeto mais próximo quando o caminho não existe); `erro_em(rotulo, linhas, caminho, mensagem) -> str` (`arquivo:linha: caminho: mensagem`).

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_yaml_linhas.py`:**

````python
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from yaml_linhas import erro_em, le_yaml, linha_de  # noqa: E402

TEXTO = """\
# comentário
fontes:
  - id: alfa/um
    links:
      - url: https://um.gov.br/
      - url: https://dois.gov.br/
        uf: SP
"""


class TestLeYaml(unittest.TestCase):
    def test_dados_e_linha_de_cada_valor(self):
        dados, linhas, erros = le_yaml(TEXTO, "catalogo/alfa.yml")
        self.assertEqual(erros, [])
        self.assertEqual(dados["fontes"][0]["links"][1], {"url": "https://dois.gov.br/", "uf": "SP"})
        self.assertEqual(linhas[("fontes",)], 3)
        self.assertEqual(linhas[("fontes", 0, "id")], 3)
        self.assertEqual(linhas[("fontes", 0, "links", 1, "uf")], 7)

    def test_linha_de_cai_no_objeto_mais_proximo(self):
        _, linhas, _ = le_yaml(TEXTO, "catalogo/alfa.yml")
        self.assertEqual(linha_de(linhas, ("fontes", 0, "links", 0, "label")), 5)
        self.assertEqual(linha_de(linhas, ("fontes", 0, "nome")), 3)

    def test_erro_de_sintaxe_yaml_aponta_linha(self):
        quebrado = "fontes:\n  - id: alfa/um\n    nome: Um\n   links: []\n"
        dados, _, erros = le_yaml(quebrado, "catalogo/alfa.yml")
        self.assertIsNone(dados)
        self.assertEqual(len(erros), 1)
        self.assertTrue(erros[0].startswith("catalogo/alfa.yml:4: YAML inválido:"), erros[0])

    def test_chave_repetida_e_erro(self):
        _, _, erros = le_yaml("fontes:\n  - id: a/b\n    id: a/c\n", "catalogo/a.yml")
        self.assertEqual(erros, ["catalogo/a.yml:3: chave 'id' repetida"])

    def test_arquivo_vazio(self):
        self.assertEqual(le_yaml("", "catalogo/a.yml")[2], ["catalogo/a.yml:1: arquivo vazio"])

    def test_erro_em_formata_arquivo_linha_e_caminho(self):
        _, linhas, _ = le_yaml(TEXTO, "catalogo/alfa.yml")
        msg = erro_em("catalogo/alfa.yml", linhas, ("fontes", 0, "links", 1, "uf"), "UF inválida")
        self.assertEqual(msg, "catalogo/alfa.yml:7: fontes[0].links[1].uf: UF inválida")


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_yaml_linhas.py
````

Esperado: falha com `ModuleNotFoundError: No module named 'yaml_linhas'` ao importar `test_yaml_linhas`.

- [x] **Passo 3: implementar. Criar `tools/yaml_linhas.py`:**

````python
"""Leitura de YAML com a linha de origem de cada valor.

Base das mensagens de erro "arquivo:linha" do catálogo (R14).
"""

import yaml

from esquema import formata_caminho

# O carregador em C é bem mais rápido; o puro Python dá o mesmo resultado.
CARREGADOR = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def le_yaml(texto, rotulo):
    """Interpreta YAML guardando a linha de cada valor.

    Retorna (dados, linhas, erros). 'linhas' mapeia o caminho de cada valor,
    como ("fontes", 0, "links", 1, "url"), para a linha (a partir de 1).
    """
    try:
        raiz = yaml.compose(texto, Loader=CARREGADOR)
    except yaml.YAMLError as erro:
        marca = getattr(erro, "problem_mark", None) or getattr(erro, "context_mark", None)
        linha = marca.line + 1 if marca else 1
        problema = getattr(erro, "problem", None) or str(erro)
        return None, {}, [f"{rotulo}:{linha}: YAML inválido: {problema}"]
    if raiz is None:
        return None, {}, [f"{rotulo}:1: arquivo vazio"]
    linhas, erros = {}, []
    construtor = yaml.constructor.SafeConstructor()
    dados = _converte(raiz, (), linhas, erros, rotulo, construtor)
    return dados, linhas, erros


def _converte(no, caminho, linhas, erros, rotulo, construtor):
    linhas[caminho] = no.start_mark.line + 1
    if isinstance(no, yaml.MappingNode):
        resultado = {}
        for no_chave, no_valor in no.value:
            chave = construtor.construct_object(no_chave, deep=True)
            if chave in resultado:
                erros.append(f"{rotulo}:{no_chave.start_mark.line + 1}: chave '{chave}' repetida")
                continue
            resultado[chave] = _converte(no_valor, caminho + (chave,), linhas, erros, rotulo, construtor)
        return resultado
    if isinstance(no, yaml.SequenceNode):
        return [
            _converte(item, caminho + (i,), linhas, erros, rotulo, construtor)
            for i, item in enumerate(no.value)
        ]
    return construtor.construct_object(no, deep=True)


def linha_de(linhas, caminho):
    """Linha do valor em 'caminho' ou, se ele não existe, do objeto mais próximo."""
    caminho = tuple(caminho)
    while caminho and caminho not in linhas:
        caminho = caminho[:-1]
    return linhas.get(caminho, 1)


def erro_em(rotulo, linhas, caminho, mensagem):
    return f"{rotulo}:{linha_de(linhas, caminho)}: {formata_caminho(caminho)}: {mensagem}"
````

- [x] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 15 tests` e `OK`.

- [x] **Passo 5: commit.**

````bash
git add tools/yaml_linhas.py tests/test_yaml_linhas.py
git commit -m "Adiciona leitura de YAML com linha de origem" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 3: schemas e validação do catálogo

**Arquivos:**
- Criar: `data/schemas/catalogo.schema.json`, `data/schemas/categorias.schema.json`, `tools/catalogo_io.py`, `tests/apoio.py`
- Teste: `tests/test_catalogo_io.py`

**Interfaces:**
- Consome: `valida` (Tarefa 1); `le_yaml`, `linha_de`, `erro_em` (Tarefa 2); `data/taxonomy.json` (eixos `input`, `output`, `tipo_fonte`, `classificacao`).
- Produz: `carrega_catalogo(raiz=RAIZ) -> tuple[dict | None, list[str]]`, com `catalogo = {"categorias": [entrada do manifesto], "fontes": {categoria_id: [fonte]}}`; `urls_do_markdown(texto: str) -> set[str]`; `normaliza_url(url: str) -> str`; `carrega_json(caminho)`; `MANIFESTO = "_categorias.yml"`. Em `tests/apoio.py`: `cria_repo(destino, arquivos=None) -> Path` e os textos `MANIFESTO`, `ALFA`, `BETA`, `CABECALHO`, `RODAPE` usados pelas tarefas 3 a 8.
- Formato do YAML: fonte com `id`, `nome`, `descricao`, `links` (`url`, opcionais `label`, `uf`, `grupo`, `em_markdown`), `input`, `output`, `tipo_fonte`, `classificacao` e opcionais `subsecao`, `resumo`, `observacao`, `markdown`; manifesto com `id`, `titulo`, `ancora`, `sumario` e opcionais `emoji`, `introducao`.

- [x] **Passo 1: escrever o apoio dos testes. Criar `tests/apoio.py`:**

````python
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
````

- [x] **Passo 2: escrever o teste que falha. Criar `tests/test_catalogo_io.py`:**

````python
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import ALFA, BETA, MANIFESTO, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402


class TestCarregaCatalogo(unittest.TestCase):
    def carrega(self, arquivos=None):
        with tempfile.TemporaryDirectory() as tmp:
            return carrega_catalogo(cria_repo(tmp, arquivos))

    def test_catalogo_valido(self):
        catalogo, erros = self.carrega()
        self.assertEqual(erros, [])
        self.assertEqual([c["id"] for c in catalogo["categorias"]], ["alfa", "beta"])
        self.assertEqual([f["id"] for f in catalogo["fontes"]["alfa"]], ["alfa/primeira-fonte", "alfa/segunda-fonte"])

    def test_termo_fora_da_taxonomia(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("input: [nenhum]", "input: [nenhum, cpff]")})
        self.assertEqual(erros, ["catalogo/beta.yml:7: fontes[0].input[1]: input 'cpff' fora da taxonomia (data/taxonomy.json)"])

    def test_tipo_fonte_fora_da_taxonomia(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("tipo_fonte: ong", "tipo_fonte: igreja")})
        self.assertEqual(erros, ["catalogo/beta.yml:9: fontes[0].tipo_fonte: tipo_fonte 'igreja' fora da taxonomia (data/taxonomy.json)"])

    def test_id_duplicado_entre_arquivos(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("beta/terceira-fonte", "alfa/primeira-fonte")})
        self.assertEqual(erros, ["catalogo/beta.yml:2: fontes[0].id: id 'alfa/primeira-fonte' repetido; já usado em catalogo/alfa.yml:2"])

    def test_fonte_sem_link(self):
        sem_link = BETA.replace("    links:\n      - url: https://terceira.org.br/\n", "    links: []\n")
        _, erros = self.carrega({"catalogo/beta.yml": sem_link})
        self.assertEqual(erros, ["catalogo/beta.yml:5: fontes[0].links: lista com 0 itens, mínimo 1"])

    def test_campo_obrigatorio_ausente(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("    nome: Terceira Fonte\n", "")})
        self.assertEqual(erros, ["catalogo/beta.yml:2: fontes[0]: campo obrigatório 'nome' ausente"])

    def test_categoria_fora_do_manifesto(self):
        _, erros = self.carrega({"catalogo/gama.yml": BETA.replace("beta/", "gama/")})
        self.assertEqual(erros, ["catalogo/gama.yml:1: categoria 'gama' fora do manifesto catalogo/_categorias.yml"])

    def test_categoria_do_manifesto_sem_arquivo(self):
        _, erros = self.carrega({"catalogo/beta.yml": None})
        self.assertEqual(erros, ["catalogo/_categorias.yml:9: categorias[1]: categoria 'beta' sem arquivo catalogo/beta.yml"])

    def test_ancora_repetida_no_manifesto(self):
        _, erros = self.carrega({"catalogo/_categorias.yml": MANIFESTO.replace("ancora: beta", "ancora: alfa")})
        self.assertEqual(erros, ["catalogo/_categorias.yml:11: categorias[1].ancora: ancora 'alfa' repetido; já usado na linha 5"])

    def test_arquivo_com_outra_extensao(self):
        _, erros = self.carrega({"catalogo/beta.yaml": BETA})
        self.assertEqual(erros, ["catalogo/beta.yaml:1: arquivo inesperado; o catálogo só aceita arquivos .yml"])

    def test_url_invalida_e_campo_desconhecido(self):
        texto = ALFA.replace("https://primeira.gov.br/", "primeira.gov.br").replace("        label: Portal\n", "        rotulo: Portal\n")
        _, erros = self.carrega({"catalogo/alfa.yml": texto})
        self.assertEqual(erros, [
            "catalogo/alfa.yml:6: fontes[0].links[0].url: valor 'primeira.gov.br' não segue o padrão ^https?://\\S+$",
            "catalogo/alfa.yml:18: fontes[1].links[0].rotulo: campo 'rotulo' não permitido",
        ])

    def test_link_em_markdown_precisa_aparecer_no_markdown(self):
        _, erros = self.carrega({"catalogo/alfa.yml": ALFA.replace("        uf: RJ\n", "        uf: RJ\n        em_markdown: true\n")})
        self.assertEqual(erros, ["catalogo/alfa.yml:23: fontes[1].links[1].em_markdown: link https://segunda.rj.gov.br/ "
                                 "marcado em_markdown, mas a URL não aparece no campo markdown"])

    def test_url_no_markdown_precisa_estar_em_links(self):
        _, erros = self.carrega({"catalogo/alfa.yml": ALFA.replace("      ```\n", "      ```\n\n      Veja https://outra.gov.br/\n")})
        self.assertEqual(erros, ["catalogo/alfa.yml:28: fontes[1].markdown: URL https://outra.gov.br/ no campo markdown "
                                 "sem link correspondente em links"])

    def test_yaml_quebrado_aponta_linha(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("    nome: Terceira", "   nome: Terceira")})
        self.assertEqual(len(erros), 1)
        self.assertTrue(erros[0].startswith("catalogo/beta.yml:3: YAML inválido"), erros[0])


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 3: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_catalogo_io.py
````

Esperado: falha com `ModuleNotFoundError: No module named 'catalogo_io'` ao importar `test_catalogo_io`.

- [x] **Passo 4: criar o schema dos arquivos de categoria. Criar `data/schemas/catalogo.schema.json`:**

````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "catalogo.schema.json",
  "title": "Arquivo de categoria do catálogo (catalogo/<categoria_id>.yml)",
  "description": "Uma categoria do catálogo. A ordem das fontes é a ordem de exibição no README.md. Os termos de input, output e tipo_fonte são validados à parte contra data/taxonomy.json.",
  "type": "object",
  "required": ["fontes"],
  "additionalProperties": false,
  "properties": {
    "fontes": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "nome", "descricao", "links", "input", "output", "tipo_fonte", "classificacao"],
        "additionalProperties": false,
        "properties": {
          "id": {
            "description": "Identificador estável da fonte. Não muda quando o nome muda.",
            "type": "string",
            "pattern": "^[a-z0-9]+(-[a-z0-9]+)*/[a-z0-9]+(-[a-z0-9]+)*$"
          },
          "nome": {"type": "string", "minLength": 1},
          "descricao": {"description": "Texto exibido abaixo do título; pode ser vazio.", "type": "string"},
          "subsecao": {"description": "Abre um subtítulo (####) da categoria antes desta fonte.", "type": "string", "minLength": 1},
          "resumo": {"description": "Quando presente, os links ficam recolhidos num <details> com este <summary>.", "type": "string", "minLength": 1},
          "links": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "required": ["url"],
              "additionalProperties": false,
              "properties": {
                "url": {"type": "string", "pattern": "^https?://\\S+$"},
                "label": {"type": "string", "minLength": 1},
                "uf": {
                  "type": "string",
                  "enum": ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
                },
                "grupo": {"description": "Texto em Markdown exibido antes deste link, como cabeçalho de um grupo de links.", "type": "string", "minLength": 1},
                "em_markdown": {"description": "O link já aparece no campo markdown da fonte e não é repetido na lista de links.", "type": "boolean"}
              }
            }
          },
          "input": {"type": "array", "uniqueItems": true, "items": {"type": "string"}},
          "output": {"type": "array", "uniqueItems": true, "items": {"type": "string"}},
          "tipo_fonte": {"type": "string"},
          "classificacao": {"type": "string", "enum": ["heuristica", "override"]},
          "observacao": {"type": "string", "minLength": 1},
          "markdown": {"description": "Markdown livre (exemplos de código, tabelas, notas) reproduzido sem alteração depois dos links. Toda URL fora de bloco de código precisa estar em links.", "type": "string", "minLength": 1}
        }
      }
    }
  }
}
````

- [x] **Passo 5: criar o schema do manifesto. Criar `data/schemas/categorias.schema.json`:**

````json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "categorias.schema.json",
  "title": "Manifesto de categorias do catálogo (catalogo/_categorias.yml)",
  "description": "Ordem das categorias no README.md e a apresentação de cada uma. Cada id corresponde a um arquivo catalogo/<id>.yml.",
  "type": "object",
  "required": ["categorias"],
  "additionalProperties": false,
  "properties": {
    "categorias": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "titulo", "ancora", "sumario"],
        "additionalProperties": false,
        "properties": {
          "id": {"type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"},
          "titulo": {"description": "Título da seção (##) e valor do campo 'categoria' no dataset.", "type": "string", "minLength": 1},
          "emoji": {"type": "string", "minLength": 1},
          "ancora": {"description": "Nome da âncora HTML <a name=\"...\"> da seção.", "type": "string", "pattern": "^[^\"\\s]+$"},
          "sumario": {"description": "Texto do item da categoria no sumário do README.", "type": "string", "minLength": 1},
          "introducao": {"description": "Markdown exibido entre o título da seção e a primeira fonte.", "type": "string", "minLength": 1}
        }
      }
    }
  }
}
````

- [x] **Passo 6: implementar. Criar `tools/catalogo_io.py`:**

````python
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
````

- [x] **Passo 7: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 29 tests` e `OK`.

- [x] **Passo 8: commit.**

````bash
git add data/schemas/catalogo.schema.json data/schemas/categorias.schema.json tools/catalogo_io.py tests/apoio.py tests/test_catalogo_io.py
git commit -m "Adiciona schemas e validação do catálogo em YAML" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 4: renderização do README a partir do catálogo

**Arquivos:**
- Criar: `tools/readme_gerado.py`
- Teste: `tests/test_readme_gerado.py`

**Interfaces:**
- Consome: `carrega_catalogo` (Tarefa 3) e `tests/apoio.py`.
- Produz: `gera_readme(catalogo: dict, cabecalho: str, rodape: str) -> str`; `renderiza_sumario(categorias) -> list[str]`; `renderiza_categoria(categoria, fontes) -> list[str]`; `renderiza_fonte(fonte) -> list[str]`; `renderiza_link(link) -> str`; constantes `AVISO` (comentário HTML da R7), `VOLTAR` (badge de volta ao sumário) e `SUMARIO_FIXO`.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_readme_gerado.py`:**

````python
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import CABECALHO, RODAPE, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402
from readme_gerado import AVISO, VOLTAR, gera_readme, renderiza_fonte, renderiza_link  # noqa: E402

ESPERADO = f"""{AVISO}
# Cabeçalho de teste

---
# Sumário

- [Alfa](#alfa)
- [Beta](#beta)
- [Autores](#autores)
- [Contribuições](#contribuicoes)
- [Créditos](#creditos)

---

## Alfa 🅰️ <a name="alfa"></a>

Introdução da categoria alfa.

### Primeira Fonte

Descrição da primeira.

- https://primeira.gov.br/

#### Subgrupo

### Segunda Fonte

<details>
<summary>Links de pesquisa</summary>

- Portal: https://segunda.sp.gov.br/

**Rio de Janeiro (RJ)**
- https://segunda.rj.gov.br/

</details>

```bash
curl https://segunda.sp.gov.br/api
```

{VOLTAR}

---

## Beta (Teste) <a name="beta"></a>

### Terceira Fonte

Descrição da terceira.

- https://terceira.org.br/

{VOLTAR}

---

## Créditos <a name="creditos"></a>

Obrigado.
"""


class TestGeraReadme(unittest.TestCase):
    def test_readme_completo_do_catalogo_de_teste(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalogo, erros = carrega_catalogo(cria_repo(tmp))
        self.assertEqual(erros, [])
        self.maxDiff = None
        self.assertEqual(gera_readme(catalogo, CABECALHO, RODAPE), ESPERADO)

    def test_readme_comeca_com_aviso_de_arquivo_gerado(self):
        self.assertTrue(AVISO.startswith("<!-- ARQUIVO GERADO por tools/build_dataset.py"))
        self.assertIn("python3 tools/build_dataset.py -->", AVISO)

    def test_links_em_markdown_nao_se_repetem_na_lista(self):
        fonte = {
            "nome": "Dorks",
            "descricao": "Buscas prontas.",
            "resumo": "Links de pesquisa",
            "links": [{"url": "https://www.google.com/search?q=site%3Agov.br", "label": "site:gov.br", "em_markdown": True}],
            "markdown": "- `site:gov.br`\n  - https://www.google.com/search?q=site%3Agov.br",
        }
        self.assertEqual(renderiza_fonte(fonte), [
            "### Dorks", "", "Buscas prontas.", "",
            "- `site:gov.br`", "  - https://www.google.com/search?q=site%3Agov.br", "",
        ])

    def test_link_com_e_sem_label(self):
        self.assertEqual(renderiza_link({"url": "https://a.gov.br/"}), "- https://a.gov.br/")
        self.assertEqual(renderiza_link({"url": "https://a.gov.br/", "label": "Portal"}), "- Portal: https://a.gov.br/")


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_readme_gerado.py
````

Esperado: falha com `ModuleNotFoundError: No module named 'readme_gerado'` ao importar `test_readme_gerado`.

- [x] **Passo 3: implementar. Criar `tools/readme_gerado.py`:**

````python
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
    "Não edite à mão: edite catalogo/<categoria>.yml e rode python3 tools/build_dataset.py -->"
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
            linhas += grupo.split("\n")
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
````

- [x] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 33 tests` e `OK`.

- [x] **Passo 5: commit.**

````bash
git add tools/readme_gerado.py tests/test_readme_gerado.py
git commit -m "Adiciona renderização do README a partir do catálogo" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 5: geração de sources.json e index.json

**Arquivos:**
- Criar: `tools/dataset.py`
- Teste: `tests/test_dataset.py`

**Interfaces:**
- Consome: `carrega_catalogo` (Tarefa 3), `gera_readme` (Tarefa 4).
- Produz: `monta_fontes(catalogo) -> list[dict]` (mesmo esquema de `data/sources.json`, `input` e `output` ordenados, `observacao` só quando existe); `monta_index(fontes) -> list[dict]`; `serializa(obj) -> str` (`json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)` mais quebra de linha final); `gera_saidas(raiz, catalogo) -> dict[str, str]` com as chaves `README.md`, `data/sources.json`, `data/index.json`; constantes `FONTE = "catalogo/"`, `SOBRE_SOURCES`, `SOBRE_INDEX`, `CABECALHO = "tools/readme/cabecalho.md"`, `RODAPE = "tools/readme/rodape.md"`.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_dataset.py`:**

````python
import difflib
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import ALFA, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402
from dataset import gera_saidas  # noqa: E402


def saidas(arquivos=None):
    with tempfile.TemporaryDirectory() as tmp:
        raiz = cria_repo(tmp, arquivos)
        catalogo, erros = carrega_catalogo(raiz)
        assert erros == [], erros
        return gera_saidas(raiz, catalogo)


def linhas_alteradas(antes, depois):
    return [
        linha for linha in difflib.unified_diff(antes.splitlines(), depois.splitlines(), lineterm="", n=0)
        if linha[:1] in "+-" and not linha.startswith(("+++", "---"))
    ]


class TestGeraSaidas(unittest.TestCase):
    def test_sources_json_no_esquema_atual(self):
        doc = json.loads(saidas()["data/sources.json"])
        self.assertEqual(doc["fonte"], "catalogo/")
        self.assertEqual(doc["total"], 3)
        self.assertEqual(doc["sources"][0], {
            "categoria": "Alfa",
            "categoria_id": "alfa",
            "classificacao": "heuristica",
            "descricao": "Descrição da primeira.",
            "id": "alfa/primeira-fonte",
            "input": ["cpf"],
            "links": [{"label": "", "uf": None, "url": "https://primeira.gov.br/"}],
            "nome": "Primeira Fonte",
            "output": ["dados_cadastrais"],
            "tipo_fonte": "federal",
        })
        self.assertEqual(doc["sources"][1]["observacao"], "Nota da curadoria.")
        self.assertEqual(doc["sources"][1]["links"][0], {"label": "Portal", "uf": "SP", "url": "https://segunda.sp.gov.br/"})
        self.assertNotIn("grupo", doc["sources"][1]["links"][1])

    def test_index_json_um_registro_por_link(self):
        doc = json.loads(saidas()["data/index.json"])
        self.assertEqual(doc["total"], 4)
        self.assertEqual(doc["links"][2], {
            "categoria": "Alfa",
            "categoria_id": "alfa",
            "descricao": "",
            "fonte": "Segunda Fonte",
            "fonte_id": "alfa/segunda-fonte",
            "input": ["nome"],
            "label": "",
            "output": ["processo"],
            "tipo_fonte": "estadual",
            "uf": "RJ",
            "url": "https://segunda.rj.gov.br/",
        })

    def test_input_e_output_saem_ordenados(self):
        doc = json.loads(saidas({"catalogo/alfa.yml": ALFA.replace("input: [cpf]", "input: [nome, cpf]")})["data/sources.json"])
        self.assertEqual(doc["sources"][0]["input"], ["cpf", "nome"])

    def test_geracao_deterministica(self):
        self.assertEqual(saidas(), saidas())

    def test_editar_descricao_altera_so_essa_fonte(self):
        antes = saidas()
        depois = saidas({"catalogo/alfa.yml": ALFA.replace("Descrição da primeira.", "Descrição nova.")})
        self.assertEqual(linhas_alteradas(antes["README.md"], depois["README.md"]),
                         ["-Descrição da primeira.", "+Descrição nova."])
        for arquivo, chave, campo in (("data/sources.json", "sources", "id"), ("data/index.json", "links", "fonte_id")):
            velhos = json.loads(antes[arquivo])[chave]
            novos = json.loads(depois[arquivo])[chave]
            mudaram = {n[campo] for v, n in zip(velhos, novos) if v != n}
            self.assertEqual(mudaram, {"alfa/primeira-fonte"}, arquivo)


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_dataset.py
````

Esperado: falha com `ModuleNotFoundError: No module named 'dataset'` ao importar `test_dataset`.

- [x] **Passo 3: implementar. Criar `tools/dataset.py`:**

````python
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
````

- [x] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 38 tests` e `OK`.

- [x] **Passo 5: commit.**

````bash
git add tools/dataset.py tests/test_dataset.py
git commit -m "Adiciona geração de sources.json e index.json a partir do catálogo" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 6: script de migração de uso único

**Arquivos:**
- Criar: `tools/migracao/readme_legado.py` (cópia literal do `tools/build_dataset.py` atual, para reaproveitar o parser), `tools/migracao/migrar_readme.py`
- Teste: `tests/test_migrar_readme.py`

**Interfaces:**
- Consome: de `readme_legado`: `parse_readme`, `atribui_ids`, `classifica`, `valida`, `carrega_json`, `extrai_links`, `urls_da_linha`, `limpa_titulo`, `slug`, `eh_decoracao`, `eh_ignorada` e as expressões `RE_*`; `carrega_catalogo` (Tarefa 3); `VOLTAR`, `renderiza_fonte` (Tarefa 4); `monta_fontes`, `CABECALHO`, `RODAPE` (Tarefa 5).
- Produz: `main(argv=None, raiz=RAIZ) -> int`; `migra(texto, overrides, taxonomia) -> tuple[list, dict, str, str]` (manifesto, fontes por categoria, cabeçalho, rodapé); `decompoe_fonte(fonte, corpo, n0) -> tuple[list, str | None, str]` (links, resumo, markdown); `confere(raiz, fontes_legado) -> dict`; `ErroMigracao`. Ao rodar, escreve `catalogo/_categorias.yml`, `catalogo/<categoria_id>.yml`, `tools/readme/cabecalho.md` e `tools/readme/rodape.md`.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_migrar_readme.py`:**

````python
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
sys.path.insert(0, str(RAIZ / "tools" / "migracao"))

from migrar_readme import main  # noqa: E402
from readme_gerado import VOLTAR  # noqa: E402

README = f"""<h1>Teste</h1>

# Sumário

- [Telecom](#telecom)
- [Outras Buscas](#outras-buscas)
- [Autores](#autores)

---

## Telecom 📡 <a name="telecom"></a>

Introdução de telecom.

### Consulta de Operadora
Consulta da operadora de um telefone.
Segunda linha da descrição.

<details>
<summary>Links por estado</summary>

**São Paulo (SP)**
- Portal: https://operadora.sp.gov.br/consulta
- https://outra.exemplo.com.br/ (Transferência)

</details>

#### Painéis

### Painel de Telefonia
Painel de estatísticas de telefone.
- https://painel.anatel.gov.br/
- Consulta por API:
  - https://painel.anatel.gov.br/api

Nota final sem link.

{VOLTAR}

---

## Outras Buscas 🔎 <a name="outras-buscas"></a>

### Busca de CPF
Consulta por CPF.
- https://cpf.exemplo.gov.br/

```bash
curl https://cpf.exemplo.gov.br/api
```

{VOLTAR}

---

## Estação Rádio Base / ERBs 📻 <a name="estacoes-radio-erbs"></a>

Estações conectam celulares.

- https://erb.exemplo.com.br/

{VOLTAR}

---

## Outras Buscas 🔎 <a name="outras-buscas"></a>

### Busca de CNPJ
Consulta por CNPJ.
- `site:gov.br "CNPJ"`
  - https://cnpj.exemplo.gov.br/

{VOLTAR}

---

## Contribuições ✨ <a name="contribuicoes"></a>

Obrigado.
"""

OVERRIDES = {"overrides": {"telecom/painel-de-telefonia": {
    "input": ["nenhum"], "output": ["estatistica"], "observacao": "Painel público."}}}


def cria(readme):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "data" / "schemas").mkdir(parents=True)
    shutil.copy(RAIZ / "data" / "taxonomy.json", tmp / "data" / "taxonomy.json")
    for nome in ("catalogo.schema.json", "categorias.schema.json"):
        shutil.copy(RAIZ / "data" / "schemas" / nome, tmp / "data" / "schemas" / nome)
    (tmp / "data" / "overrides.json").write_text(json.dumps(OVERRIDES), encoding="utf-8")
    (tmp / "README.md").write_text(readme, encoding="utf-8")
    return tmp


def roda(raiz):
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        codigo = main([], raiz=raiz)
    return codigo, saida.getvalue(), erro.getvalue()


def le(raiz, nome):
    return yaml.safe_load((raiz / "catalogo" / nome).read_text(encoding="utf-8"))


class TestMigracao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raiz = cria(README)
        cls.resultado = roda(cls.raiz)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.raiz)

    def test_migracao_termina_sem_erro(self):
        codigo, saida, erro = self.resultado
        self.assertEqual(codigo, 0, erro)
        self.assertEqual(saida.strip(), "migrado: 3 categorias, 5 fontes, 7 links em catalogo/")

    def test_manifesto_funde_secoes_repetidas(self):
        self.assertEqual(le(self.raiz, "_categorias.yml"), {"categorias": [
            {"id": "telecom", "titulo": "Telecom", "emoji": "📡", "ancora": "telecom", "sumario": "Telecom",
             "introducao": "Introdução de telecom."},
            {"id": "outras-buscas", "titulo": "Outras Buscas", "emoji": "🔎", "ancora": "outras-buscas",
             "sumario": "Outras Buscas"},
            {"id": "estacao-radio-base-erbs", "titulo": "Estação Rádio Base / ERBs", "emoji": "📻",
             "ancora": "estacoes-radio-erbs", "sumario": "Estação Rádio Base / ERBs"},
        ]})
        ids = [f["id"] for f in le(self.raiz, "outras-buscas.yml")["fontes"]]
        self.assertEqual(ids, ["outras-buscas/busca-de-cpf", "outras-buscas/busca-de-cnpj"])

    def test_fonte_com_details_grupo_e_uf(self):
        fonte = le(self.raiz, "telecom.yml")["fontes"][0]
        self.assertEqual(fonte, {
            "id": "telecom/consulta-de-operadora",
            "nome": "Consulta de Operadora",
            "descricao": "Consulta da operadora de um telefone. Segunda linha da descrição.",
            "resumo": "Links por estado",
            "links": [
                {"grupo": "**São Paulo (SP)**", "url": "https://operadora.sp.gov.br/consulta", "label": "Portal", "uf": "SP"},
                {"url": "https://outra.exemplo.com.br/", "label": "Transferência", "uf": "SP"},
            ],
            "input": ["telefone"],
            "output": ["operadora"],
            "tipo_fonte": "estadual",
            "classificacao": "heuristica",
        })

    def test_override_congelado_subsecao_rotulo_e_markdown(self):
        fonte = le(self.raiz, "telecom.yml")["fontes"][1]
        self.assertEqual(fonte["subsecao"], "Painéis")
        self.assertEqual(fonte["links"], [
            {"url": "https://painel.anatel.gov.br/"},
            {"url": "https://painel.anatel.gov.br/api", "label": "Consulta por API"},
        ])
        self.assertEqual(fonte["markdown"], "Nota final sem link.")
        self.assertEqual((fonte["input"], fonte["output"], fonte["classificacao"], fonte["observacao"]),
                         (["nenhum"], ["estatistica"], "override", "Painel público."))

    def test_bloco_de_codigo_guarda_corpo_literal(self):
        fonte = le(self.raiz, "outras-buscas.yml")["fontes"][0]
        self.assertEqual(fonte["descricao"], "Consulta por CPF.")
        self.assertEqual(fonte["links"], [{"url": "https://cpf.exemplo.gov.br/", "em_markdown": True}])
        self.assertEqual(fonte["markdown"], "- https://cpf.exemplo.gov.br/\n\n```bash\ncurl https://cpf.exemplo.gov.br/api\n```")

    def test_dork_entre_crases_guarda_corpo_literal(self):
        fonte = le(self.raiz, "outras-buscas.yml")["fontes"][1]
        self.assertEqual(fonte["links"], [{"url": "https://cnpj.exemplo.gov.br/", "label": 'site:gov.br "CNPJ"', "em_markdown": True}])
        self.assertEqual(fonte["markdown"], '- `site:gov.br "CNPJ"`\n  - https://cnpj.exemplo.gov.br/')
        self.assertNotIn("resumo", fonte)

    def test_fonte_implicita_vira_fonte_com_nome_da_categoria(self):
        fonte = le(self.raiz, "estacao-radio-base-erbs.yml")["fontes"][0]
        self.assertEqual((fonte["id"], fonte["nome"], fonte["descricao"]),
                         ("estacao-radio-base-erbs/estacao-radio-base-erbs", "Estação Rádio Base / ERBs",
                          "Estações conectam celulares."))

    def test_trechos_fixos(self):
        self.assertEqual((self.raiz / "tools" / "readme" / "cabecalho.md").read_text(encoding="utf-8"), "<h1>Teste</h1>\n\n")
        self.assertEqual((self.raiz / "tools" / "readme" / "rodape.md").read_text(encoding="utf-8"),
                         "## Contribuições ✨ <a name=\"contribuicoes\"></a>\n\nObrigado.\n")

    def test_categoria_sem_ancora_falha_com_linha(self):
        raiz = cria(README.replace("## Telecom 📡 <a name=\"telecom\"></a>", "## Telecom 📡"))
        try:
            codigo, _, erro = roda(raiz)
        finally:
            shutil.rmtree(raiz)
        self.assertEqual(codigo, 1)
        self.assertIn("README.md:11: categoria sem <a name>", erro)


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_migrar_readme.py
````

Esperado: falha com `ModuleNotFoundError: No module named 'migrar_readme'` ao importar `test_migrar_readme`.

- [x] **Passo 3: copiar o parser atual sem alteração.**

````bash
mkdir -p tools/migracao
cp tools/build_dataset.py tools/migracao/readme_legado.py
cmp tools/build_dataset.py tools/migracao/readme_legado.py && echo copia-identica
````

Esperado: `copia-identica`.

- [x] **Passo 4: implementar. Criar `tools/migracao/migrar_readme.py`:**

````python
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
````

- [x] **Passo 5: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 47 tests` e `OK`.

- [x] **Passo 6: commit.**

````bash
git add tools/migracao/readme_legado.py tools/migracao/migrar_readme.py tests/test_migrar_readme.py
git commit -m "Adiciona script de migração do README para catalogo/" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 7: script de comparação antes e depois (CA1 a CA5)

**Arquivos:**
- Criar: `tools/migracao/comparar.py`
- Teste: `tests/test_comparar.py`

**Interfaces:**
- Consome: `urls_da_linha` de `readme_legado` (Tarefa 6); `git show <ref>:<arquivo>` para o estado anterior.
- Produz: `main(argv=None, raiz=RAIZ) -> int` com `--ref COMMIT` (padrão: pai do commit que criou `catalogo/_categorias.yml`); `compara(antes: dict[str, str], depois: dict[str, str], categorias_arquivos: list[str]) -> tuple[list[str], list[str]]` (erros, resumo); `ordem_esperada(registros, chave) -> list` (ordem antiga com cada categoria agrupada na primeira seção, R13); `ref_antes(raiz) -> str`.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_comparar.py`:**

````python
import copy
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools" / "migracao"))

from comparar import compara, ordem_esperada  # noqa: E402


def fonte(ident, categoria, url, classificacao="heuristica"):
    return {"id": ident, "categoria_id": categoria, "classificacao": classificacao,
            "links": [{"label": "", "uf": None, "url": url}]}


def link(ident, categoria, url):
    return {"fonte_id": ident, "categoria_id": categoria, "url": url}


# "outras" aparece em duas seções no README antigo: a fonte o/2 vem depois de b/1.
FONTES = [fonte("o/1", "outras", "https://o1.gov.br/"), fonte("b/1", "beta", "https://b1.gov.br/", "override"),
          fonte("o/2", "outras", "https://o2.gov.br/")]
LINKS = [link("o/1", "outras", "https://o1.gov.br/"), link("b/1", "beta", "https://b1.gov.br/"),
         link("o/2", "outras", "https://o2.gov.br/")]
README_ANTES = ('## Outras <a name="outras"></a>\n- https://o1.gov.br/\n## Beta <a name="beta"></a>\n'
                '- https://b1.gov.br/\n## Outras <a name="outras"></a>\n- https://o2.gov.br/\n')
README_DEPOIS = ('## Outras <a name="outras"></a>\n- https://o1.gov.br/\n- https://o2.gov.br/\n'
                 '## Beta <a name="beta"></a>\n- https://b1.gov.br/\n')


def estado(fontes, links, readme, sobre="x", outros=None):
    base = {
        "README.md": readme,
        "data/sources.json": json.dumps({"_sobre": sobre, "fonte": sobre, "total": len(fontes), "sources": fontes}),
        "data/index.json": json.dumps({"_sobre": sobre, "fonte": sobre, "total": len(links), "links": links}),
    }
    base.update(outros or {})
    return base


DEPOIS_OK = estado([FONTES[0], FONTES[2], FONTES[1]], [LINKS[0], LINKS[2], LINKS[1]], README_DEPOIS, sobre="novo")


class TestCompara(unittest.TestCase):
    def test_ordem_esperada_agrupa_na_primeira_secao(self):
        self.assertEqual([f["id"] for f in ordem_esperada(FONTES, "categoria_id")], ["o/1", "o/2", "b/1"])

    def test_migracao_fiel_passa(self):
        erros, resumo = compara(estado(FONTES, LINKS, README_ANTES), DEPOIS_OK, ["beta", "outras"])
        self.assertEqual(erros, [])
        self.assertIn("CA3 fontes: 3 | links: 3 | heuristica: 2 | override: 1 | ids iguais: True", resumo)

    def test_link_alterado_falha_ca2_e_ca4(self):
        depois = copy.deepcopy(DEPOIS_OK)
        depois["README.md"] = depois["README.md"].replace("o2.gov.br", "o3.gov.br")
        fontes = json.loads(depois["data/sources.json"])
        fontes["sources"][1]["links"][0]["url"] = "https://o3.gov.br/"
        depois["data/sources.json"] = json.dumps(fontes)
        erros, _ = compara(estado(FONTES, LINKS, README_ANTES), depois, ["beta", "outras"])
        self.assertTrue(any(e.startswith("CA2 sources.json: sources[1] difere: o/2") for e in erros), erros)
        self.assertTrue(any(e.startswith("CA4:") for e in erros), erros)

    def test_categoria_sem_arquivo_falha_ca1(self):
        erros, _ = compara(estado(FONTES, LINKS, README_ANTES), DEPOIS_OK, ["beta"])
        self.assertEqual(erros, ["CA1: arquivos de categoria ['outras'] não batem com categoria_id"])

    def test_ancora_perdida_e_link_externo_quebrado_falham_ca5(self):
        outros = {"GUIA_RAPIDO.md": "[Beta](README.md#beta) e [Velho](README.md#nao-existia)"}
        depois = dict(DEPOIS_OK)
        depois["README.md"] = README_DEPOIS.replace('## Beta <a name="beta"></a>', "## Bravo")
        erros, resumo = compara(estado(FONTES, LINKS, README_ANTES, outros=outros), depois, ["beta", "outras"])
        self.assertIn("CA5: âncoras <a name> sumiram: ['beta']", erros)
        self.assertIn("CA5: GUIA_RAPIDO.md -> README.md#beta deixou de resolver", erros)
        self.assertTrue(resumo[-1].endswith("links de outros documentos já quebrados antes: 1"), resumo[-1])


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_comparar.py
````

Esperado: falha com `ModuleNotFoundError: No module named 'comparar'` ao importar `test_comparar`.

- [x] **Passo 3: implementar. Criar `tools/migracao/comparar.py`:**

````python
#!/usr/bin/env python3
"""Compara o estado antes e depois da migração da spec 001 (CA1 a CA5).

"Antes" é lido do git (README.md, data/*.json e documentos no commit de
referência); "depois" é o diretório de trabalho atual. Sem --ref, a
referência é o pai do commit que criou catalogo/_categorias.yml.

Verifica:
    CA1  catalogo/ tem um arquivo por categoria_id anterior, mais o manifesto
    CA2  sources.json e index.json iguais, exceto '_sobre', 'fonte' e a ordem
         das fontes de categorias que tinham duas seções (R13)
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


def compara_json(antes, depois, lista):
    erros = []
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
````

- [x] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 52 tests` e `OK`.

- [x] **Passo 5: commit.**

````bash
git add tools/migracao/comparar.py tests/test_comparar.py
git commit -m "Adiciona script de comparação antes e depois da migração" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 8: novo build a partir de catalogo/ e migração do catálogo

**Arquivos:**
- Modificar (substituir por inteiro): `tools/build_dataset.py`
- Gerar: `catalogo/_categorias.yml`, `catalogo/<categoria_id>.yml` (40 arquivos), `tools/readme/cabecalho.md`, `tools/readme/rodape.md`, `README.md`, `data/sources.json`, `data/index.json`
- Teste: `tests/test_build_dataset.py`

**Interfaces:**
- Consome: `carrega_catalogo` (Tarefa 3), `gera_saidas` (Tarefa 5), `migrar_readme.main` (Tarefa 6), `comparar.main` (Tarefa 7).
- Produz: `tools/build_dataset.py` com `main(argv=None, raiz=RAIZ) -> int` e as opções `--check` (falha com `arquivo:linha` se o catálogo for inválido ou se `README.md`, `data/sources.json` ou `data/index.json` diferirem do gerado) e `--report` (só estatísticas); `primeira_diferenca(atual, gerado) -> int`; o catálogo migrado em `catalogo/`.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_build_dataset.py`:**

````python
import contextlib
import io
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import BETA, cria_repo  # noqa: E402
from build_dataset import main  # noqa: E402

GERADOS = ("README.md", "data/sources.json", "data/index.json")
MODULOS_DO_BUILD = ("build_dataset.py", "catalogo_io.py", "dataset.py", "readme_gerado.py", "yaml_linhas.py", "esquema.py")


def roda(raiz, *args):
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        codigo = main(list(args), raiz=raiz)
    return codigo, saida.getvalue(), erro.getvalue()


class TestBuild(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = cria_repo(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_gera_e_depois_check_passa(self):
        codigo, saida, _ = roda(self.raiz)
        self.assertEqual(codigo, 0)
        self.assertIn("escrito README.md", saida)
        codigo, saida, _ = roda(self.raiz, "--check")
        self.assertEqual((codigo, saida.strip()), (0, "OK: catálogo válido e arquivos gerados atualizados."))

    def test_rodar_duas_vezes_nao_muda_nada(self):
        roda(self.raiz)
        primeira = {a: (self.raiz / a).read_bytes() for a in GERADOS}
        roda(self.raiz)
        self.assertEqual({a: (self.raiz / a).read_bytes() for a in GERADOS}, primeira)

    def test_check_falha_com_readme_editado(self):
        roda(self.raiz)
        readme = self.raiz / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace("Descrição da terceira.", "Editado à mão."), encoding="utf-8")
        codigo, _, erro = roda(self.raiz, "--check")
        self.assertEqual(codigo, 1)
        linha = next(n for n, l in enumerate(readme.read_text(encoding="utf-8").splitlines(), 1) if l == "Editado à mão.")
        self.assertIn(f"README.md:{linha}: difere do gerado a partir de catalogo/", erro)

    def test_check_falha_com_json_desatualizado(self):
        roda(self.raiz)
        (self.raiz / "catalogo" / "beta.yml").write_text(BETA.replace("Terceira Fonte", "Terceira Fonte Renomeada"), encoding="utf-8")
        codigo, _, erro = roda(self.raiz, "--check")
        self.assertEqual(codigo, 1)
        self.assertRegex(erro, r"data/sources\.json:\d+: difere")
        self.assertRegex(erro, r"data/index\.json:\d+: difere")
        self.assertRegex(erro, r"README\.md:\d+: difere")

    def test_check_falha_com_catalogo_invalido_citando_arquivo_e_linha(self):
        roda(self.raiz)
        (self.raiz / "catalogo" / "beta.yml").write_text(BETA.replace("output: [dataset]", "output: [datset]"), encoding="utf-8")
        codigo, _, erro = roda(self.raiz, "--check")
        self.assertEqual(codigo, 1)
        self.assertIn("catalogo/beta.yml:8: fontes[0].output[0]: output 'datset' fora da taxonomia", erro)

    def test_report(self):
        codigo, saida, _ = roda(self.raiz, "--report")
        self.assertEqual(codigo, 0)
        self.assertIn("fontes .............. 3", saida)
        self.assertIn("classificação: heurística 2 | override 1", saida)
        self.assertFalse((self.raiz / "README.md").exists())


class TestBuildDoRepositorio(unittest.TestCase):
    def test_build_nao_le_overrides_nem_heuristica(self):
        for nome in MODULOS_DO_BUILD:
            texto = (RAIZ / "tools" / nome).read_text(encoding="utf-8")
            for proibido in ("overrides", "REGRAS_PALAVRA", "REGRAS_CATEGORIA", "readme_legado", "parse_readme"):
                self.assertNotIn(proibido, texto, f"{nome} cita {proibido}")

    def test_check_do_repositorio_passa_em_menos_de_10_segundos(self):
        inicio = time.monotonic()
        resultado = subprocess.run([sys.executable, "tools/build_dataset.py", "--check"], cwd=RAIZ,
                                   capture_output=True, text=True)
        duracao = time.monotonic() - inicio
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertLess(duracao, 10)

    def test_catalogo_tem_40_categorias_mais_o_manifesto(self):
        arquivos = sorted(p.name for p in (RAIZ / "catalogo").iterdir())
        self.assertEqual(len(arquivos), 41)
        self.assertIn("_categorias.yml", arquivos)
        self.assertTrue(all(re.fullmatch(r"[a-z0-9-_]+\.yml", a) for a in arquivos))


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_build_dataset.py
````

Esperado: falha com `TypeError: main() got an unexpected keyword argument 'raiz'` (o `main()` antigo não aceita parâmetros) e `FileNotFoundError` em `catalogo`.

- [x] **Passo 3: implementar. Substituir o conteúdo de `tools/build_dataset.py`:**

````python
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
            (raiz / relativo).write_text(conteudo, encoding="utf-8")
            print(f"escrito {relativo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [x] **Passo 4: migrar o README e os overrides para `catalogo/`.**

````bash
python3 tools/migracao/migrar_readme.py
````

Esperado: `migrado: 40 categorias, 874 fontes, 2313 links em catalogo/`.

- [x] **Passo 5: gerar README e dataset a partir de `catalogo/`.**

````bash
python3 tools/build_dataset.py
````

Esperado: `escrito README.md`, `escrito data/sources.json` e `escrito data/index.json`.

- [x] **Passo 6: comparar com o estado anterior (CA1 a CA5); `HEAD` ainda é o commit anterior à migração.**

````bash
python3 tools/migracao/comparar.py --ref HEAD
````

Esperado: `CA1 categorias: 40 arquivos + manifesto`, `CA3 fontes: 874 | links: 2313 | heuristica: 667 | override: 207 | ids iguais: True`, `CA2 sources.json e index.json: iguais exceto _sobre, fonte e a ordem das categorias com duas seções`, `CA4 URLs no README: 2322 antes, 2322 depois`, `CA5 âncoras <a name>: 43 antes, 43 depois | links de outros documentos já quebrados antes: 1` e `OK: migração preserva o catálogo.`

- [x] **Passo 7: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
python3 tools/validar_docs.py
````

Esperado: `Ran 61 tests` e `OK`. e `OK: documentos seguem as regras de formatação.`

- [x] **Passo 8: commit.**

````bash
git add tools/build_dataset.py tests/test_build_dataset.py catalogo tools/readme README.md data/sources.json data/index.json
git commit -m "Migra o catálogo para catalogo/ e gera README e dataset a partir dele" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 9: CI e hook de pre-commit

**Arquivos:**
- Modificar (substituir por inteiro): `.github/workflows/validar-dataset.yml`, `tools/hooks/pre-commit` (e torná-lo executável no git)
- Teste: `tests/test_ci.py`

**Interfaces:**
- Consome: `requirements.txt` (Tarefa 1), `python3 tools/build_dataset.py --check` (Tarefa 8), `python3 tools/validar_docs.py`.
- Produz: workflow que instala `requirements.txt`, roda os testes, `build_dataset.py --check` e `validar_docs.py` em push para `main` e em PR que toque `catalogo/**`; hook `tools/hooks/pre-commit` (modo `100755`) que roda as mesmas verificações quando `catalogo`, `README.md`, `data`, `tools` ou `requirements.txt` mudam.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_ci.py`:**

````python
import os
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOW = RAIZ / ".github" / "workflows" / "validar-dataset.yml"
HOOK = RAIZ / "tools" / "hooks" / "pre-commit"


class TestCI(unittest.TestCase):
    def test_workflow_instala_dependencia_fixada_e_roda_verificacoes(self):
        texto = WORKFLOW.read_text(encoding="utf-8")
        for passo in ("python3 -m pip install -r requirements.txt",
                      "python3 -m unittest discover -s tests -v",
                      "python3 tools/build_dataset.py --check",
                      "python3 tools/validar_docs.py"):
            self.assertIn(f"run: {passo}", texto)
        self.assertEqual(texto.count('"catalogo/**"'), 2)
        self.assertEqual(texto.count('"requirements.txt"'), 2)
        self.assertNotIn("--report", texto)

    def test_hook_valida_catalogo_e_e_executavel(self):
        texto = HOOK.read_text(encoding="utf-8")
        self.assertIn("python3 tools/build_dataset.py --check", texto)
        self.assertIn("git diff --cached --quiet -- catalogo README.md data tools requirements.txt", texto)
        self.assertNotIn("overrides.json", texto)
        self.assertTrue(os.access(HOOK, os.X_OK))
        modo = subprocess.run(["git", "ls-files", "-s", "tools/hooks/pre-commit"], cwd=RAIZ,
                              capture_output=True, text=True, check=True).stdout.split()[0]
        self.assertEqual(modo, "100755")

    def test_requirements_fixa_so_o_pyyaml(self):
        linhas = [l for l in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
        self.assertEqual(linhas, ["PyYAML==6.0.3"])


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_ci.py
````

Esperado: `AssertionError: 'run: python3 -m pip install -r requirements.txt' not found` e `FAILED (failures=2)`.

- [x] **Passo 3: implementar o workflow. Substituir o conteúdo de `.github/workflows/validar-dataset.yml`:**

````yaml
name: Validar catálogo e dataset

on:
  push:
    branches: [main]
    paths: ["*.md", "catalogo/**", "data/**", "tools/**", "tests/**", "requirements.txt", ".github/workflows/validar-dataset.yml"]
  pull_request:
    paths: ["*.md", "catalogo/**", "data/**", "tools/**", "tests/**", "requirements.txt", ".github/workflows/validar-dataset.yml"]

jobs:
  validar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Dependências (versão fixada)
        run: python3 -m pip install -r requirements.txt

      - name: Testes das ferramentas
        run: python3 -m unittest discover -s tests -v

      - name: Catálogo válido e arquivos gerados atualizados
        run: python3 tools/build_dataset.py --check

      - name: Regras de formatação dos documentos
        run: python3 tools/validar_docs.py
````

- [x] **Passo 4: implementar o hook. Substituir o conteúdo de `tools/hooks/pre-commit`:**

````sh
#!/bin/sh
# Valida catálogo, arquivos gerados e documentos antes do commit. Ativar com:
#   git config core.hooksPath tools/hooks
# Requer PyYAML: python3 -m pip install -r requirements.txt
set -e
cd "$(git rev-parse --show-toplevel)"

# 1. Regras de formatação (travessão, menu, âncoras) e avisos de curadoria
if ! git diff --cached --quiet -- '*.md' catalogo data tools; then
  python3 tools/validar_docs.py --avisos
fi

# 2. Catálogo (schema, taxonomia, ids, links) e README.md/data/*.json gerados em dia
if ! git diff --cached --quiet -- catalogo README.md data tools requirements.txt; then
  python3 tools/build_dataset.py --check
fi
````

- [x] **Passo 5: tornar o hook executável também no índice do git.**

````bash
chmod +x tools/hooks/pre-commit
git add --chmod=+x tools/hooks/pre-commit
git ls-files -s tools/hooks/pre-commit | cut -c1-6
````

Esperado: `100755`.

- [x] **Passo 6: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 64 tests` e `OK`.

- [x] **Passo 7: commit.**

````bash
git add .github/workflows/validar-dataset.yml tools/hooks/pre-commit tests/test_ci.py
git commit -m "Atualiza CI e hook de pre-commit para validar catalogo/" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 10: travessão também em catalogo/

**Arquivos:**
- Modificar (substituir por inteiro): `tools/validar_docs.py`
- Teste: `tests/test_validar_docs.py`

**Interfaces:**
- Consome: `DOCS` e as demais funções atuais de `tools/validar_docs.py`.
- Produz: `checa_travessao(raiz=RAIZ) -> list[str]`, que passa a ler também `catalogo/*.yml` e aponta `arquivo:linha`; `le(nome, raiz=RAIZ) -> str`; constante `TRAVESSAO = "\u2014"`. O comportamento de `checa_menu`, `checa_ancoras` e `--avisos` não muda.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_validar_docs.py`:**

````python
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from validar_docs import DOCS, checa_travessao  # noqa: E402

TRAVESSAO = "\u2014"


def cria(tmp, catalogo):
    raiz = Path(tmp)
    for nome in DOCS:
        (raiz / nome).write_text("# Documento\n", encoding="utf-8")
    (raiz / "catalogo").mkdir()
    (raiz / "catalogo" / "alfa.yml").write_text(catalogo, encoding="utf-8")
    return raiz


class TestTravessao(unittest.TestCase):
    def test_travessao_em_arquivo_do_catalogo_e_erro(self):
        with tempfile.TemporaryDirectory() as tmp:
            erros = checa_travessao(cria(tmp, f"fontes:\n  - nome: IBAMA {TRAVESSAO} Autuações\n"))
        self.assertEqual(erros, [f"catalogo/alfa.yml:2: travessão ({TRAVESSAO}); use vírgula, dois-pontos, ponto final ou parênteses"])

    def test_travessao_entre_crases_e_permitido(self):
        with tempfile.TemporaryDirectory() as tmp:
            erros = checa_travessao(cria(tmp, f"fontes:\n  - descricao: Não use `{TRAVESSAO}` em textos\n"))
        self.assertEqual(erros, [])

    def test_repositorio_sem_travessao(self):
        self.assertEqual(checa_travessao(), [])


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_validar_docs.py
````

Esperado: `TypeError: checa_travessao() takes 0 positional arguments but 1 was given` e `FAILED (errors=2)`.

- [x] **Passo 3: implementar. Substituir o conteúdo de `tools/validar_docs.py`:**

````python
#!/usr/bin/env python3
"""Valida as regras de formatação dos documentos do OSINT Brazuca.

Erros (saída 1), conforme CONTRIBUICAO.md:
    travessão (U+2014) fora de crases em qualquer .md e em catalogo/*.yml
    menu de navegação (bloco de badges) diferente entre os documentos
    link interno (#ancora) sem âncora correspondente no README.md

Avisos (não falham; só com --avisos):
    URL repetida em mais de uma fonte do catálogo
    URL em http:// em vez de https://

Uso:
    python3 tools/validar_docs.py            só erros
    python3 tools/validar_docs.py --avisos   erros e avisos
"""

import argparse
import json
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = ["README.md", "README.en.md", "CONTRIBUICAO.md", "EXEMPLOS_PRATICOS.md", "FLUXOGRAMA.md", "GUIA_RAPIDO.md"]

TRAVESSAO = "\u2014"
RE_TRAVESSAO = re.compile(f"(?<!`){TRAVESSAO}(?!`)")
RE_MENU = re.compile(r'^<p align="center">\n((?:  <a href=.*\n)+)</p>$', re.M)
RE_ANCORA = re.compile(r'<a name="([^"]+)"')
RE_LINK_INTERNO = re.compile(r"\]\(#([^)]+)\)")


def le(nome, raiz=RAIZ):
    return (raiz / nome).read_text(encoding="utf-8")


def checa_travessao(raiz=RAIZ):
    erros = []
    catalogo = sorted(f"catalogo/{p.name}" for p in (raiz / "catalogo").glob("*.yml"))
    for nome in DOCS + catalogo:
        for n, linha in enumerate(le(nome, raiz).splitlines(), start=1):
            if RE_TRAVESSAO.search(linha):
                erros.append(f"{nome}:{n}: travessão ({TRAVESSAO}); use vírgula, dois-pontos, ponto final ou parênteses")
    return erros


def checa_menu():
    menus = {}
    for nome in DOCS:
        m = RE_MENU.search(le(nome))
        if not m:
            return [f"{nome}: menu de navegação (bloco de badges) não encontrado"]
        menus[nome] = m.group(1)
    referencia = menus["README.md"]
    return [
        f"{nome}: menu de navegação diferente do README.md; replique a mudança em todos os documentos"
        for nome, menu in menus.items()
        if menu != referencia
    ]


def checa_ancoras():
    texto = le("README.md")
    ancoras = set(RE_ANCORA.findall(texto))
    # Títulos também geram âncoras no GitHub; aceita o slug simples deles.
    for titulo in re.findall(r"^#{1,6}\s+(.*)$", texto, re.M):
        ancoras.add(slug_github(titulo))
    erros = []
    for n, linha in enumerate(texto.splitlines(), start=1):
        for alvo in RE_LINK_INTERNO.findall(linha):
            alvo = urllib.parse.unquote(alvo)
            if alvo not in ancoras and alvo.lower() not in ancoras:
                erros.append(f"README.md:{n}: link interno #{alvo} sem âncora correspondente")
    return erros


def slug_github(titulo):
    titulo = re.sub(r"<[^>]+>", "", titulo)
    titulo = re.sub(r"[^\w\s-]", "", titulo.strip().lower(), flags=re.UNICODE)
    return re.sub(r"\s+", "-", titulo).strip("-")


def avisos_catalogo():
    caminho = RAIZ / "data" / "index.json"
    if not caminho.exists():
        return ["data/index.json não existe; rode tools/build_dataset.py"]
    links = json.loads(caminho.read_text(encoding="utf-8"))["links"]
    avisos = []
    por_url = defaultdict(set)
    for link in links:
        por_url[link["url"]].add(link["fonte_id"])
    for url, fontes in sorted(por_url.items()):
        if len(fontes) > 1:
            avisos.append(f"URL repetida em {len(fontes)} fontes: {url}\n    " + "\n    ".join(sorted(fontes)))
    inseguras = sorted({l["url"] for l in links if l["url"].startswith("http://")})
    if inseguras:
        avisos.append(f"{len(inseguras)} URLs em http://; confira se há versão https:")
        avisos.extend(f"    {u}" for u in inseguras)
    return avisos


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--avisos", action="store_true", help="mostra também URLs repetidas e http://")
    args = parser.parse_args()

    erros = checa_travessao() + checa_menu() + checa_ancoras()

    if args.avisos:
        avisos = avisos_catalogo()
        if avisos:
            print(f"AVISOS ({len(avisos)}):")
            for a in avisos:
                print(f"  {a}")
            print()

    if erros:
        print(f"ERROS ({len(erros)}):", file=sys.stderr)
        for e in erros:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("OK: documentos seguem as regras de formatação.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [x] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
python3 tools/validar_docs.py
````

Esperado: `Ran 67 tests` e `OK`. e `OK: documentos seguem as regras de formatação.`

- [x] **Passo 5: commit.**

````bash
git add tools/validar_docs.py tests/test_validar_docs.py
git commit -m "Verifica travessão também nos arquivos de catalogo/" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 11: documentação: CONTRIBUICAO, seção do dataset no README e modelos

**Arquivos:**
- Modificar: `CONTRIBUICAO.md`, `tools/readme/cabecalho.md`, `data/schemas/sources.schema.json`, `data/schemas/index.schema.json`
- Gerar: `README.md`
- Teste: `tests/test_documentacao.py`

**Interfaces:**
- Consome: `python3 tools/build_dataset.py` (Tarefa 8).
- Produz: nota curta no `CONTRIBUICAO.md` (R16); seção "Dataset Estruturado" do README apontando `catalogo/` em vez de `overrides.json`; modelos `sources.schema.json` e `index.schema.json` com `"fonte": "catalogo/"`.

- [x] **Passo 1: escrever o teste que falha. Criar `tests/test_documentacao.py`:**

````python
import json
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def le(relativo):
    return (RAIZ / relativo).read_text(encoding="utf-8")


class TestDocumentacao(unittest.TestCase):
    def test_contribuicao_explica_que_fontes_ficam_em_catalogo(self):
        texto = le("CONTRIBUICAO.md")
        self.assertIn("As fontes do catálogo ficam em `catalogo/<categoria>.yml`", texto)
        self.assertIn("são gerados a partir desses arquivos: não os edite à mão", texto)
        self.assertNotIn("O README é a fonte de verdade do catálogo", texto)
        self.assertNotIn("sem dependências", texto)

    def test_readme_gerado_aponta_catalogo_como_fonte(self):
        readme = le("README.md")
        self.assertTrue(readme.startswith("<!-- ARQUIVO GERADO por tools/build_dataset.py a partir de catalogo/."))
        self.assertNotIn("overrides.json", readme)
        self.assertNotIn("a partir deste README", readme)
        self.assertIn("Correções de classificação vão no arquivo da categoria em `catalogo/`.", readme)

    def test_modelos_do_dataset_indicam_catalogo(self):
        for nome in ("sources.schema.json", "index.schema.json"):
            self.assertEqual(json.loads(le(f"data/schemas/{nome}"))["fonte"], "catalogo/")


if __name__ == "__main__":
    unittest.main()
````

- [x] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_documentacao.py
````

Esperado: `FAILED (failures=3)`.

- [x] **Passo 3: aplicar as edições (cada trecho antigo precisa aparecer uma única vez; o script para com `AssertionError` se não aparecer).**

````bash
python3 - <<'EOF'
from pathlib import Path


def troca(caminho, pares):
    arquivo = Path(caminho)
    texto = arquivo.read_text(encoding="utf-8")
    for velho, novo in pares:
        assert texto.count(velho) == 1, (caminho, velho)
        texto = texto.replace(velho, novo)
    arquivo.write_text(texto, encoding="utf-8")


troca("CONTRIBUICAO.md", [
    ("O README é a fonte de verdade do catálogo. A pasta `data/` contém uma versão estruturada dele, usada para busca por tipo de entrada e de retorno.",
     "> [!IMPORTANT]\n"
     "> As fontes do catálogo ficam em `catalogo/<categoria>.yml`, um arquivo YAML por categoria, com a classificação (`input`, `output`, `tipo_fonte`) declarada em cada fonte. "
     "O `README.md`, o `data/sources.json` e o `data/index.json` são gerados a partir desses arquivos: não os edite à mão. "
     "O `data/overrides.json` e a classificação automática por palavra-chave não são mais usados pelo build."),
    ("python3 tools/build_dataset.py            # regenera o dataset",
     "python3 tools/build_dataset.py            # valida catalogo/ e regenera README.md e o dataset"),
    ("python3 tools/build_dataset.py --report   # mostra estatísticas e fontes sem classificação",
     "python3 tools/build_dataset.py --report   # mostra estatísticas do catálogo"),
    ("Requer apenas Python 3, sem dependências.",
     "Requer Python 3 e PyYAML, com versão fixada em `requirements.txt`: `python3 -m pip install -r requirements.txt`."),
])

troca("tools/readme/cabecalho.md", [
    ("gerada automaticamente a partir deste README.",
     "gerada automaticamente a partir de [`catalogo/`](catalogo/), a mesma fonte que gera este README."),
    ("| [`data/overrides.json`](data/overrides.json) | Correções manuais de classificação. |",
     "| [`catalogo/`](catalogo/) | Fonte de verdade: um arquivo YAML por categoria, com os links e a classificação de cada fonte. |"),
    ("Correções de classificação vão em `overrides.json`.",
     "Correções de classificação vão no arquivo da categoria em `catalogo/`."),
    ("Para regenerar depois de alterar o README:",
     "Para regenerar depois de alterar `catalogo/`:"),
    ("Requer apenas Python 3, sem dependências.",
     "Requer Python 3 e PyYAML (`python3 -m pip install -r requirements.txt`)."),
])

troca("data/schemas/sources.schema.json", [
    ('"fonte": "README.md"', '"fonte": "catalogo/"'),
    ("O campo 'observacao' só aparece quando definido em overrides.json.",
     "O campo 'observacao' só aparece quando definido no arquivo da categoria em catalogo/."),
])

troca("data/schemas/index.schema.json", [
    ('"fonte": "README.md"', '"fonte": "catalogo/"'),
])
EOF
````

- [x] **Passo 4: regenerar o README.**

````bash
python3 tools/build_dataset.py
````

Esperado: `escrito README.md`.

- [x] **Passo 5: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
python3 tools/validar_docs.py
python3 tools/build_dataset.py --check
````

Esperado: `Ran 70 tests` e `OK`., `OK: documentos seguem as regras de formatação.` e `OK: catálogo válido e arquivos gerados atualizados.`

- [x] **Passo 6: commit.**

````bash
git add CONTRIBUICAO.md tools/readme/cabecalho.md data/schemas/sources.schema.json data/schemas/index.schema.json README.md tests/test_documentacao.py
git commit -m "Documenta catalogo/ como fonte de verdade" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 12: verificação final dos critérios de aceite

**Arquivos:** nenhum (só verificação; não há commit).

**Interfaces:**
- Consome: tudo das tarefas 1 a 11.
- Produz: a evidência dos critérios de aceite para a descrição do PR.

- [x] **Passo 1: suíte completa, `--check` e documentos (CA6, CA8, CA11, CA12).**

````bash
python3 -m unittest discover -s tests
python3 tools/build_dataset.py --check
python3 tools/validar_docs.py
````

Esperado: `Ran 70 tests` e `OK`., `OK: catálogo válido e arquivos gerados atualizados.` e `OK: documentos seguem as regras de formatação.`

- [x] **Passo 2: totais (CA3).**

````bash
python3 tools/build_dataset.py --report
````

Esperado: `categorias .......... 40`, `fontes .............. 874`, `links ............... 2313` e `classificação: heurística 667 | override 207`.

- [x] **Passo 3: equivalência com o estado anterior à migração, sem `--ref` (CA1, CA2, CA4, CA5).**

````bash
python3 tools/migracao/comparar.py
````

Esperado: `CA4 URLs no README: 2322 antes, 2322 depois` e `OK: migração preserva o catálogo.`

- [x] **Passo 4: gerar duas vezes seguidas não deixa diff (R9, CA7).**

````bash
python3 tools/build_dataset.py >/dev/null
python3 tools/build_dataset.py >/dev/null
test -z "$(git status --porcelain)" && echo git-status-limpo
````

Esperado: `git-status-limpo`.

- [x] **Passo 5: tempo do build completo (CA10).**

````bash
python3 - <<'EOF'
import subprocess, sys, time
inicio = time.monotonic()
subprocess.run([sys.executable, "tools/build_dataset.py", "--check"], check=True, capture_output=True)
print("build em menos de 10 s:", time.monotonic() - inicio < 10)
EOF
````

Esperado: `build em menos de 10 s: True`.

- [x] **Passo 6: nenhum código do build lê overrides nem roda a heurística (CA12).**

````bash
grep -l -E 'overrides|REGRAS_PALAVRA|parse_readme' tools/build_dataset.py tools/catalogo_io.py tools/dataset.py tools/readme_gerado.py tools/yaml_linhas.py tools/esquema.py || echo build-sem-heuristica
````

Esperado: `build-sem-heuristica`.
