# Tarefas da spec 002: fluxo de contribuição

> Roteiro histórico da implementação (PR #6). O código vigente está em `tools/` e `tests/`; em divergência, vale o código. Pendências novas vão para issues.

Plano: [`plan.md`](plan.md). Spec: [`spec.md`](spec.md). ADR: [`0002`](../../adr/0002-arquivos-gerados-regenerados-no-main.md).

Todos os comandos rodam na raiz do repositório, com o ambiente virtual da preparação ativo (`. .venv/bin/activate`). Cada tarefa termina com um commit assinado (a assinatura GPG vem do `~/.gitconfig`; nunca usar `--no-gpg-sign`). Os números de `Ran N tests` são cumulativos: a suíte inteira cresce a cada tarefa. Passos "Em `arquivo`, trocar" substituem o primeiro bloco pelo segundo, exatamente uma vez.

## Preparação

- [ ] **Passo P1: criar a branch e o ambiente virtual.**

````bash
git switch -c feat/002-fluxo-de-contribuicao webminas/main
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --quiet -r requirements.txt
````

- [ ] **Passo P2: conferir o ponto de partida.**

````bash
python3 -m unittest discover -s tests
python3 tools/build_dataset.py --check
````

Esperado: `Ran 82 tests`, `OK` e `OK: catálogo válido e arquivos gerados atualizados.`

---

## Tarefa 1: fim de linha LF e arquivos gerados marcados

**Arquivos:**
- Criar: `.gitattributes`
- Modificar: `tools/build_dataset.py`
- Teste: `tests/test_fim_de_linha.py`

**Interfaces:**
- Consome: `tools/build_dataset.py` da spec 001.
- Produz: `grava(caminho, conteudo)` em `build_dataset.py` (bytes UTF-8, LF em qualquer sistema); `.gitattributes` com `* text=auto eol=lf` e `linguist-generated=true` nos três gerados.

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_fim_de_linha.py`:**

````python
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from build_dataset import grava  # noqa: E402

GERADOS = ("README.md", "data/sources.json", "data/index.json")


def atributo(nome, caminho):
    saida = subprocess.run(["git", "check-attr", nome, "--", caminho], cwd=RAIZ,
                           capture_output=True, text=True, check=True).stdout
    return saida.strip().rsplit(": ", 1)[-1]


class TestFimDeLinha(unittest.TestCase):
    def test_grava_usa_lf_e_utf8_em_qualquer_sistema(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "saida.md"
            grava(caminho, "Ação\nlinha 2\n")
            self.assertEqual(caminho.read_bytes(), "Ação\nlinha 2\n".encode("utf-8"))

    def test_gitattributes_fixa_lf_no_texto_versionado(self):
        for caminho in ("catalogo/saude.yml", "tools/build_dataset.py", "CONTRIBUICAO.md") + GERADOS:
            with self.subTest(caminho=caminho):
                self.assertEqual(atributo("eol", caminho), "lf")

    def test_arquivos_gerados_marcados_para_o_github(self):
        for caminho in GERADOS:
            with self.subTest(caminho=caminho):
                self.assertEqual(atributo("linguist-generated", caminho), "true")
        self.assertEqual(atributo("linguist-generated", "catalogo/saude.yml"), "unspecified")


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_fim_de_linha.py
````

Esperado: `ImportError: cannot import name 'grava' from 'build_dataset'`.

- [ ] **Passo 3: implementar. Criar `.gitattributes`:**

````text
# Fim de linha LF em todo arquivo de texto versionado, também no Windows (spec 002).
* text=auto eol=lf

# Gerados por tools/build_dataset.py a partir de catalogo/; nunca editar à mão.
# O GitHub recolhe o diff deles nos PRs e os deixa fora das estatísticas.
README.md linguist-generated=true
data/sources.json linguist-generated=true
data/index.json linguist-generated=true
````

- [ ] **Passo 4: implementar. Em `tools/build_dataset.py`, trocar:**

````python
def primeira_diferenca(atual, gerado):
````

por:

````python
def grava(caminho, conteudo):
    """Grava em UTF-8 com fim de linha LF em qualquer sistema (no Windows o modo texto usaria CRLF)."""
    Path(caminho).write_bytes(conteudo.encode("utf-8"))


def primeira_diferenca(atual, gerado):
````

- [ ] **Passo 5: implementar. Em `tools/build_dataset.py`, trocar:**

````python
            (raiz / relativo).write_text(conteudo, encoding="utf-8")
````

por:

````python
            grava(raiz / relativo, conteudo)
````

- [ ] **Passo 6: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
git ls-files --eol | awk '{print $1}' | sort -u
````

Esperado: `Ran 85 tests` e `OK`; só `i/lf` e `i/-text` (nenhum arquivo versionado com CRLF, então o `.gitattributes` não renormaliza nada).

- [ ] **Passo 7: commit.**

````bash
git add .gitattributes tools/build_dataset.py tests/test_fim_de_linha.py
git commit -m "Fixa fim de linha LF e marca os arquivos gerados para o GitHub" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 2: dicas em português para erros de sintaxe YAML

**Arquivos:**
- Modificar (substituir por inteiro): `tools/yaml_linhas.py`
- Teste: `tests/test_dicas_yaml.py`

**Interfaces:**
- Consome: `le_yaml(texto, rotulo)` da spec 001.
- Produz: `dica(problema: str) -> str`; erros de sintaxe no formato `arquivo:linha: YAML inválido: <mensagem do PyYAML>. Dica: <texto>`; aspas sem fechar apontam a linha de abertura.

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_dicas_yaml.py`:**

````python
import sys
import unittest
from pathlib import Path
from unittest import mock

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

import yaml_linhas  # noqa: E402
from yaml_linhas import le_yaml  # noqa: E402

FONTE = "fontes:\n  - id: alfa/um\n    nome: Um\n    descricao: {}\n    input: [cpf]\n"

# (valor da descrição, linha esperada, trecho da dica)
CASOS = {
    "dois-pontos": ("Consulta: CPF e CNPJ", 4, "texto com ': ' precisa ficar entre aspas simples"),
    "crase": ("`curl` na linha de comando", 4, "começa com crase, @ ou % precisa ficar entre aspas simples"),
    "arroba": ("@perfil oficial", 4, "começa com crase, @ ou % precisa ficar entre aspas simples"),
    "asterisco": ("*destaque* do texto", 4, "começa com * ou & precisa ficar entre aspas simples"),
    "colchete": ("[Beta] consulta gratuita", 4, "começa com [ ou { precisa ficar entre aspas simples"),
    "exclamacao": ("!importante consulta", 4, "começa com ! precisa ficar entre aspas simples"),
    "aspas-abertas": ("'texto sem fechar", 4, "aspas abertas e não fechadas"),
}


class TestDicasYaml(unittest.TestCase):
    def confere(self, carregador):
        with mock.patch.object(yaml_linhas, "CARREGADOR", carregador):
            for nome, (valor, linha, dica) in CASOS.items():
                with self.subTest(carregador=carregador.__name__, caso=nome):
                    dados, _, erros = le_yaml(FONTE.format(valor), "catalogo/alfa.yml")
                    self.assertIsNone(dados)
                    self.assertEqual(len(erros), 1, erros)
                    self.assertTrue(erros[0].startswith(f"catalogo/alfa.yml:{linha}: YAML inválido: "), erros[0])
                    self.assertIn(". Dica: ", erros[0])
                    self.assertIn(dica, erros[0])

    def test_dicas_com_o_carregador_em_c(self):
        self.confere(yaml_linhas.CARREGADOR)

    def test_dicas_com_o_carregador_em_python(self):
        self.confere(yaml.SafeLoader)

    def test_indentacao_errada_ganha_dica_de_alinhamento(self):
        for texto in ("fontes:\n  - id: alfa/um\n    nome: Um\n   descricao: x\n",
                      "fontes:\n  - id: alfa/um\n    links:\n    - url: https://a.gov.br/\n     label: A\n"):
            with self.subTest(texto=texto):
                _, _, erros = le_yaml(texto, "catalogo/alfa.yml")
                self.assertIn("alinhe a linha com os campos vizinhos", erros[0])

    def test_tabulacao_ganha_dica(self):
        _, _, erros = le_yaml("fontes:\n\t- id: alfa/um\n", "catalogo/alfa.yml")
        self.assertIn("nunca com tabulação", erros[0])

    def test_erro_sem_dica_conhecida_fica_como_esta(self):
        self.assertEqual(yaml_linhas.dica("problema que ninguém previu"), "")


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_dicas_yaml.py
````

Esperado: `FAILED`, com `AttributeError: module 'yaml_linhas' has no attribute 'dica'` e asserções sem `. Dica: `.

- [ ] **Passo 3: implementar. Substituir o conteúdo de `tools/yaml_linhas.py`:**

````python
"""Leitura de YAML com a linha de origem de cada valor.

Base das mensagens de erro "arquivo:linha" do catálogo (R14).
"""

import yaml

from esquema import formata_caminho

# O carregador em C é bem mais rápido; o puro Python dá o mesmo resultado.
CARREGADOR = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

ALINHAMENTO = "alinhe a linha com os campos vizinhos (2 espaços por nível, só espaços)"

# Dicas em português para as mensagens do PyYAML, que vêm em inglês. A chave é
# um trecho da mensagem, igual no carregador em C e no puro Python.
DICAS = (
    ("mapping values are not allowed",
     f"texto com ': ' precisa ficar entre aspas simples (descricao: 'Consulta: CPF'); se não for isso, {ALINHAMENTO}"),
    ("cannot start any token",
     "texto que começa com crase, @ ou % precisa ficar entre aspas simples; indente só com espaços, nunca com tabulação"),
    ("alphabetic or numeric character", "texto que começa com * ou & precisa ficar entre aspas simples"),
    ("undefined alias", "texto que começa com * ou & precisa ficar entre aspas simples"),
    ("constructor for the tag", "texto que começa com ! precisa ficar entre aspas simples"),
    ("did not find expected key", f"texto que começa com [ ou {{ precisa ficar entre aspas simples; se não for isso, {ALINHAMENTO}"),
    ("expected <block end>", f"texto que começa com [ ou {{ precisa ficar entre aspas simples; se não for isso, {ALINHAMENTO}"),
    ("expected '-' indicator", ALINHAMENTO),
    ("end of stream", "aspas abertas e não fechadas; para um apóstrofo dentro de aspas simples, escreva duas aspas ('')"),
    ("could not find expected ':'", "falta ': ' depois do nome do campo, ou um texto longo quebrou a linha sem aspas"),
)


def dica(problema):
    """Dica em português para a mensagem do PyYAML, ou "" se não houver."""
    for trecho, texto in DICAS:
        if trecho in problema:
            return texto
    return ""


def _invalido(rotulo, linha, problema):
    texto = dica(problema)
    sufixo = f". Dica: {texto}" if texto else ""
    return f"{rotulo}:{linha}: YAML inválido: {problema}{sufixo}"


def le_yaml(texto, rotulo):
    """Interpreta YAML guardando a linha de cada valor.

    Retorna (dados, linhas, erros). 'linhas' mapeia o caminho de cada valor,
    como ("fontes", 0, "links", 1, "url"), para a linha (a partir de 1).
    """
    try:
        raiz = yaml.compose(texto, Loader=CARREGADOR)
    except yaml.YAMLError as erro:
        marca = getattr(erro, "problem_mark", None) or getattr(erro, "context_mark", None)
        if "quoted scalar" in (getattr(erro, "context", None) or ""):
            marca = erro.context_mark  # aspas sem fechar: a linha útil é a que abre as aspas
        linha = marca.line + 1 if marca else 1
        problema = getattr(erro, "problem", None) or str(erro)
        return None, {}, [_invalido(rotulo, linha, problema)]
    if raiz is None:
        return None, {}, [f"{rotulo}:1: arquivo vazio"]
    linhas, erros = {}, []
    construtor = yaml.constructor.SafeConstructor()
    try:
        dados = _converte(raiz, (), linhas, erros, rotulo, construtor)
    except _ErroNo as erro:
        return None, {}, erros + [erro.args[0]]
    return dados, linhas, erros


class _ErroNo(Exception):
    pass


def _constroi(no, construtor, rotulo):
    try:
        return construtor.construct_object(no, deep=True)
    except yaml.YAMLError as erro:
        problema = getattr(erro, "problem", None) or str(erro)
        raise _ErroNo(_invalido(rotulo, no.start_mark.line + 1, problema)) from None
    except TypeError:
        raise _ErroNo(f"{rotulo}:{no.start_mark.line + 1}: YAML inválido: chave não pode ser lista ou mapa") from None


def _converte(no, caminho, linhas, erros, rotulo, construtor):
    linhas[caminho] = no.start_mark.line + 1
    if isinstance(no, yaml.MappingNode):
        resultado = {}
        for no_chave, no_valor in no.value:
            chave = _constroi(no_chave, construtor, rotulo)
            try:
                repetida = chave in resultado
            except TypeError:
                raise _ErroNo(f"{rotulo}:{no_chave.start_mark.line + 1}: YAML inválido: "
                              "chave não pode ser lista ou mapa") from None
            if repetida:
                erros.append(f"{rotulo}:{no_chave.start_mark.line + 1}: chave '{chave}' repetida")
                continue
            resultado[chave] = _converte(no_valor, caminho + (chave,), linhas, erros, rotulo, construtor)
        return resultado
    if isinstance(no, yaml.SequenceNode):
        return [
            _converte(item, caminho + (i,), linhas, erros, rotulo, construtor)
            for i, item in enumerate(no.value)
        ]
    return _constroi(no, construtor, rotulo)


def linha_de(linhas, caminho):
    """Linha do valor em 'caminho' ou, se ele não existe, do objeto mais próximo."""
    caminho = tuple(caminho)
    while caminho and caminho not in linhas:
        caminho = caminho[:-1]
    return linhas.get(caminho, 1)


def erro_em(rotulo, linhas, caminho, mensagem):
    return f"{rotulo}:{linha_de(linhas, caminho)}: {formata_caminho(caminho)}: {mensagem}"
````

- [ ] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 90 tests` e `OK`.

- [ ] **Passo 5: commit.**

````bash
git add tools/yaml_linhas.py tests/test_dicas_yaml.py
git commit -m "Acrescenta dicas em português aos erros de sintaxe YAML" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 3: mensagens com termos aceitos, sugestões e formato legível

**Arquivos:**
- Modificar (substituir por inteiro): `tools/esquema.py`, `data/schemas/catalogo.schema.json`
- Modificar: `tools/catalogo_io.py`, `tests/test_esquema.py`, `tests/test_catalogo_io.py`
- Teste: `tests/test_mensagens.py`

**Interfaces:**
- Consome: `valida` (`esquema.py`), `carrega_catalogo` (`catalogo_io.py`).
- Produz: `enum` com `valor 'X' fora da lista permitida: A, B`; `pattern` com `x-mensagem` vira `valor 'X': <x-mensagem>`; `fora_da_taxonomia(eixo, termo, aceitos) -> str` em `catalogo_io.py`.

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_mensagens.py`:**

````python
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import ALFA, BETA, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402
from esquema import valida  # noqa: E402

TIPOS_FONTE = ("academico, api, defensoria, dork, estadual, federal, indefinido, internacional, "
               "judiciario, legislativo, ministerio_publico, municipal, ong, privado")


def carrega(arquivos):
    with tempfile.TemporaryDirectory() as tmp:
        return carrega_catalogo(cria_repo(tmp, arquivos))[1]


class TestMensagensDoEsquema(unittest.TestCase):
    def test_enum_lista_os_valores_aceitos(self):
        erros = valida("XX", {"enum": ["SP", "RJ"]})
        self.assertEqual(erros, [((), "valor 'XX' fora da lista permitida: SP, RJ")])

    def test_padrao_com_mensagem_propria(self):
        esquema = {"type": "string", "pattern": "^https?://", "x-mensagem": "a URL precisa começar com https://"}
        self.assertEqual(valida("ftp://a", esquema), [((), "valor 'ftp://a': a URL precisa começar com https://")])

    def test_padrao_sem_mensagem_propria_mostra_a_expressao(self):
        erros = valida("ftp://a", {"type": "string", "pattern": "^https?://"})
        self.assertEqual(erros, [((), "valor 'ftp://a' não segue o padrão ^https?://")])


class TestMensagensDoCatalogo(unittest.TestCase):
    def test_termo_parecido_ganha_sugestao(self):
        erros = carrega({"catalogo/beta.yml": BETA.replace("input: [nenhum]", "input: [placas]")})
        self.assertEqual(erros, ["catalogo/beta.yml:7: fontes[0].input[0]: input 'placas' fora da taxonomia "
                                 "(data/taxonomy.json); você quis dizer 'placa'?"])

    def test_eixo_curto_sem_termo_parecido_lista_os_termos(self):
        erros = carrega({"catalogo/beta.yml": BETA.replace("tipo_fonte: ong", "tipo_fonte: igreja")})
        self.assertEqual(erros, ["catalogo/beta.yml:9: fontes[0].tipo_fonte: tipo_fonte 'igreja' fora da taxonomia "
                                 f"(data/taxonomy.json); termos aceitos: {TIPOS_FONTE}"])

    def test_eixo_longo_sem_termo_parecido_aponta_a_taxonomia(self):
        erros = carrega({"catalogo/beta.yml": BETA.replace("output: [dataset]", "output: [telefone]")})
        self.assertEqual(erros, ["catalogo/beta.yml:8: fontes[0].output[0]: output 'telefone' fora da taxonomia "
                                 "(data/taxonomy.json); veja os termos aceitos na seção output de data/taxonomy.json"])

    def test_uf_invalida_lista_as_siglas(self):
        erros = carrega({"catalogo/alfa.yml": ALFA.replace("uf: SP", "uf: Sp")})
        self.assertEqual(len(erros), 1, erros)
        self.assertIn("fontes[1].links[0].uf: valor 'Sp' fora da lista permitida: AC, AL, AP, AM,", erros[0])

    def test_url_e_id_invalidos_explicam_o_formato(self):
        texto = ALFA.replace("https://primeira.gov.br/", "primeira.gov.br").replace("alfa/primeira-fonte", "alfa/Primeira Fonte")
        self.assertEqual(carrega({"catalogo/alfa.yml": texto}), [
            "catalogo/alfa.yml:2: fontes[0].id: valor 'alfa/Primeira Fonte': o id tem o formato categoria/nome-da-fonte, "
            "só com letras minúsculas sem acento, números e hífens",
            "catalogo/alfa.yml:6: fontes[0].links[0].url: valor 'primeira.gov.br': a URL precisa começar com "
            "http:// ou https:// e não pode ter espaços",
        ])


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_mensagens.py
````

Esperado: `FAILED (failures=7)` (só `test_padrao_sem_mensagem_propria_mostra_a_expressao` já passa).

- [ ] **Passo 3: implementar. Substituir o conteúdo de `tools/esquema.py`:**

````python
"""Validador mínimo de JSON Schema, só com a biblioteca padrão.

Cobre o subconjunto usado em data/schemas/catalogo.schema.json e
data/schemas/categorias.schema.json: type, properties, required,
additionalProperties (booleano), items, enum, pattern, minLength,
minItems e uniqueItems. Palavras-chave fora dessa lista são ignoradas, exceto
"x-mensagem": quando presente ao lado de "pattern", substitui a expressão
regular na mensagem de erro por um texto para quem edita o catálogo.

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
        aceitos = ", ".join(str(v) for v in esquema["enum"])
        erros.append((caminho, f"valor {valor!r} fora da lista permitida: {aceitos}"))

    if isinstance(valor, str):
        if len(valor) < esquema.get("minLength", 0):
            erros.append((caminho, "texto vazio"))
        padrao = esquema.get("pattern")
        if padrao and not re.search(padrao, valor):
            if "x-mensagem" in esquema:
                erros.append((caminho, f"valor {valor!r}: {esquema['x-mensagem']}"))
            else:
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

- [ ] **Passo 4: implementar. Substituir o conteúdo de `data/schemas/catalogo.schema.json`:**

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
            "pattern": "^[a-z0-9]+(-[a-z0-9]+)*/[a-z0-9]+(-[a-z0-9]+)*$",
            "x-mensagem": "o id tem o formato categoria/nome-da-fonte, só com letras minúsculas sem acento, números e hífens"
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
                "url": {"type": "string", "pattern": "^https?://\\S+$", "x-mensagem": "a URL precisa começar com http:// ou https:// e não pode ter espaços"},
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

- [ ] **Passo 5: implementar. Em `tools/catalogo_io.py`, trocar:**

````python
import json
import re
````

por:

````python
import difflib
import json
import re
````

- [ ] **Passo 6: implementar. Em `tools/catalogo_io.py`, trocar:**

````python
def carrega_catalogo(raiz=RAIZ):
````

por:

````python
def fora_da_taxonomia(eixo, termo, aceitos):
    """Mensagem de termo fora da taxonomia, com sugestão ou com os termos aceitos."""
    mensagem = f"{eixo} '{termo}' fora da taxonomia (data/taxonomy.json)"
    parecidos = difflib.get_close_matches(termo, sorted(aceitos), n=3, cutoff=0.6)
    if parecidos:
        return mensagem + "; você quis dizer " + " ou ".join(f"'{p}'" for p in parecidos) + "?"
    if len(aceitos) <= 15:
        return mensagem + "; termos aceitos: " + ", ".join(sorted(aceitos))
    return mensagem + f"; veja os termos aceitos na seção {eixo} de data/taxonomy.json"


def carrega_catalogo(raiz=RAIZ):
````

- [ ] **Passo 7: implementar. Em `tools/catalogo_io.py`, trocar:**

````python
                    if termo not in termos[eixo]:
                        erros.append(erro_em(rotulo, linhas, base + (eixo, k),
                                             f"{eixo} '{termo}' fora da taxonomia (data/taxonomy.json)"))
            for eixo in ("tipo_fonte", "classificacao"):
                if fonte[eixo] not in termos[eixo]:
                    erros.append(erro_em(rotulo, linhas, base + (eixo,),
                                         f"{eixo} '{fonte[eixo]}' fora da taxonomia (data/taxonomy.json)"))
````

por:

````python
                    if termo not in termos[eixo]:
                        erros.append(erro_em(rotulo, linhas, base + (eixo, k),
                                             fora_da_taxonomia(eixo, termo, termos[eixo])))
            for eixo in ("tipo_fonte", "classificacao"):
                if fonte[eixo] not in termos[eixo]:
                    erros.append(erro_em(rotulo, linhas, base + (eixo,),
                                         fora_da_taxonomia(eixo, fonte[eixo], termos[eixo])))
````

- [ ] **Passo 8: ajustar testes antigos às mensagens novas. Em `tests/test_esquema.py`, trocar:**

````python
            (("uf",), "valor 'XX' fora da lista permitida"),
````

por:

````python
            (("uf",), "valor 'XX' fora da lista permitida: SP, RJ, None"),
````

- [ ] **Passo 9: Em `tests/test_catalogo_io.py`, trocar:**

````python
        self.assertEqual(erros, ["catalogo/beta.yml:7: fontes[0].input[1]: input 'cpff' fora da taxonomia (data/taxonomy.json)"])
````

por:

````python
        self.assertEqual(erros, ["catalogo/beta.yml:7: fontes[0].input[1]: input 'cpff' fora da taxonomia (data/taxonomy.json); você quis dizer 'cpf'?"])
````

- [ ] **Passo 10: Em `tests/test_catalogo_io.py`, trocar:**

````python
        self.assertEqual(erros, ["catalogo/beta.yml:9: fontes[0].tipo_fonte: tipo_fonte 'igreja' fora da taxonomia (data/taxonomy.json)"])
````

por:

````python
        self.assertEqual(erros, ["catalogo/beta.yml:9: fontes[0].tipo_fonte: tipo_fonte 'igreja' fora da taxonomia (data/taxonomy.json); termos aceitos: "
                                 "academico, api, defensoria, dork, estadual, federal, indefinido, internacional, "
                                 "judiciario, legislativo, ministerio_publico, municipal, ong, privado"])
````

- [ ] **Passo 11: Em `tests/test_catalogo_io.py`, trocar:**

````python
            "catalogo/alfa.yml:6: fontes[0].links[0].url: valor 'primeira.gov.br' não segue o padrão ^https?://\\S+$",
````

por:

````python
            "catalogo/alfa.yml:6: fontes[0].links[0].url: valor 'primeira.gov.br': a URL precisa começar com http:// ou https:// e não pode ter espaços",
````

- [ ] **Passo 12: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 98 tests` e `OK`.

- [ ] **Passo 13: commit.**

````bash
git add tools/esquema.py tools/catalogo_io.py data/schemas/catalogo.schema.json tests/test_mensagens.py tests/test_esquema.py tests/test_catalogo_io.py
git commit -m "Mostra termos aceitos, sugestões e formato legível nos erros do catálogo" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 4: todos os erros do catálogo numa rodada

**Arquivos:**
- Modificar (substituir por inteiro): `tools/catalogo_io.py`
- Teste: `tests/test_uma_rodada.py`

**Interfaces:**
- Consome: `valida`, `le_yaml`, `erro_em`, `fora_da_taxonomia` (Tarefa 3).
- Produz: `carrega_catalogo` que valida o arquivo até a lista `fontes` e depois cada fonte; `_verifica_fonte(rotulo, linhas, fonte, base, invalidos, termos, ids_vistos) -> list[str]`, que pula os campos listados em `invalidos`.

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_uma_rodada.py`:**

````python
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import ALFA, BETA, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402


def carrega(arquivos):
    with tempfile.TemporaryDirectory() as tmp:
        return carrega_catalogo(cria_repo(tmp, arquivos))[1]


class TestErrosNumaRodada(unittest.TestCase):
    def test_erro_de_formato_numa_fonte_nao_esconde_taxonomia_de_outra(self):
        texto = (ALFA.replace("    descricao: Descrição da primeira.\n", "    descricao: Descrição da primeira.\n    cor: azul\n")
                 .replace("input: [nome]", "input: [nomes]"))
        self.assertEqual(carrega({"catalogo/alfa.yml": texto}), [
            "catalogo/alfa.yml:5: fontes[0].cor: campo 'cor' não permitido",
            "catalogo/alfa.yml:24: fontes[1].input[0]: input 'nomes' fora da taxonomia (data/taxonomy.json); você quis dizer 'nome' ou 'cnes'?",
        ])

    def test_campo_ausente_e_termo_errado_na_mesma_fonte(self):
        texto = BETA.replace("    nome: Terceira Fonte\n", "").replace("output: [dataset]", "output: [datset]")
        self.assertEqual(carrega({"catalogo/beta.yml": texto}), [
            "catalogo/beta.yml:2: fontes[0]: campo obrigatório 'nome' ausente",
            "catalogo/beta.yml:7: fontes[0].output[0]: output 'datset' fora da taxonomia (data/taxonomy.json); você quis dizer 'dataset'?",
        ])

    def test_url_invalida_e_tipo_fonte_errado_na_mesma_fonte(self):
        texto = BETA.replace("https://terceira.org.br/", "terceira.org.br").replace("tipo_fonte: ong", "tipo_fonte: ongs")
        erros = carrega({"catalogo/beta.yml": texto})
        self.assertEqual(len(erros), 2, erros)
        self.assertTrue(erros[0].startswith("catalogo/beta.yml:6: fontes[0].links[0].url: "), erros[0])
        self.assertTrue(erros[1].startswith("catalogo/beta.yml:9: fontes[0].tipo_fonte: tipo_fonte 'ongs'"), erros[1])

    def test_id_repetido_aparece_junto_com_erro_de_formato(self):
        texto = ALFA.replace("alfa/segunda-fonte", "alfa/primeira-fonte").replace("    nome: Segunda Fonte\n", "")
        self.assertEqual(carrega({"catalogo/alfa.yml": texto}), [
            "catalogo/alfa.yml:11: fontes[1]: campo obrigatório 'nome' ausente",
            "catalogo/alfa.yml:11: fontes[1].id: id 'alfa/primeira-fonte' repetido; já usado em catalogo/alfa.yml:2",
        ])

    def test_arquivo_sem_lista_de_fontes_para_ali(self):
        self.assertEqual(carrega({"catalogo/beta.yml": "fontes: nenhuma\n"}),
                         ["catalogo/beta.yml:1: fontes: tipo string, esperado array"])


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_uma_rodada.py
````

Esperado: `FAILED (failures=4)`; só `test_arquivo_sem_lista_de_fontes_para_ali` passa.

- [ ] **Passo 3: implementar. Substituir o conteúdo de `tools/catalogo_io.py`:**

````python
"""Leitura e validação do catálogo em catalogo/ (fonte de verdade).

catalogo/_categorias.yml   manifesto: ordem e apresentação das categorias
catalogo/<categoria>.yml   fontes de uma categoria, na ordem de exibição

Toda mensagem de erro começa com "arquivo:linha: ", com a linha do YAML
onde está o valor com problema (ou o objeto que o contém).
"""

import difflib
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


def _urls_soltas(rotulo, linhas, fonte, base, urls_links):
    """Erros para URL em campo de texto que só aparece no README, não no dataset."""
    campos = [(base + (campo,), fonte.get(campo, "")) for campo in ("descricao", "resumo", "subsecao", "observacao")]
    campos += [(base + ("links", k, "grupo"), link.get("grupo", "")) for k, link in enumerate(fonte["links"])]
    erros = []
    for caminho, texto in campos:
        for url in sorted(urls_do_markdown(texto) - urls_links):
            erros.append(erro_em(rotulo, linhas, caminho,
                                 f"URL {url} no campo {caminho[-1]} sem link correspondente; coloque a URL em links"))
    return erros


def fora_da_taxonomia(eixo, termo, aceitos):
    """Mensagem de termo fora da taxonomia, com sugestão ou com os termos aceitos."""
    mensagem = f"{eixo} '{termo}' fora da taxonomia (data/taxonomy.json)"
    parecidos = difflib.get_close_matches(termo, sorted(aceitos), n=3, cutoff=0.6)
    if parecidos:
        return mensagem + "; você quis dizer " + " ou ".join(f"'{p}'" for p in parecidos) + "?"
    if len(aceitos) <= 15:
        return mensagem + "; termos aceitos: " + ", ".join(sorted(aceitos))
    return mensagem + f"; veja os termos aceitos na seção {eixo} de data/taxonomy.json"


def _verifica_fonte(rotulo, linhas, fonte, base, invalidos, termos, ids_vistos):
    """Taxonomia, coerência entre links e markdown e id único, nos campos sem erro de formato."""
    def ok(*campos):
        return not invalidos.intersection(campos)

    erros = []
    for eixo in ("input", "output"):
        if ok(eixo):
            for k, termo in enumerate(fonte[eixo]):
                if termo not in termos[eixo]:
                    erros.append(erro_em(rotulo, linhas, base + (eixo, k), fora_da_taxonomia(eixo, termo, termos[eixo])))
    for eixo in ("tipo_fonte", "classificacao"):
        if ok(eixo) and fonte[eixo] not in termos[eixo]:
            erros.append(erro_em(rotulo, linhas, base + (eixo,), fora_da_taxonomia(eixo, fonte[eixo], termos[eixo])))
    if ok("links", "markdown", "descricao", "resumo", "subsecao", "observacao"):
        urls_md = urls_do_markdown(fonte.get("markdown", ""))
        for k, link in enumerate(fonte["links"]):
            if link.get("em_markdown") and link["url"] not in urls_md:
                erros.append(erro_em(rotulo, linhas, base + ("links", k, "em_markdown"),
                                     f"link {link['url']} marcado em_markdown, mas a URL não aparece no campo markdown"))
        urls_links = {link["url"] for link in fonte["links"]}
        for url in sorted(urls_md - urls_links):
            erros.append(erro_em(rotulo, linhas, base + ("markdown",),
                                 f"URL {url} no campo markdown sem link correspondente em links"))
        erros.extend(_urls_soltas(rotulo, linhas, fonte, base, urls_links))
    if ok("id"):
        local = f"{rotulo}:{linha_de(linhas, base + ('id',))}"
        if fonte["id"] in ids_vistos:
            erros.append(erro_em(rotulo, linhas, base + ("id",),
                                 f"id '{fonte['id']}' repetido; já usado em {ids_vistos[fonte['id']]}"))
        else:
            ids_vistos[fonte["id"]] = local
    return erros


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
    esquema_fonte = esquema_categoria["properties"]["fontes"]["items"]
    esquema_arquivo = dict(esquema_categoria, properties={"fontes": dict(esquema_categoria["properties"]["fontes"], items={})})

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

    for i, categoria in enumerate(categorias):
        for url in sorted(urls_do_markdown(categoria.get("introducao", ""))):
            erros.append(erro_em(rotulo_manifesto, linhas_manifesto, ("categorias", i, "introducao"),
                                 f"URL {url} no campo introducao; coloque a URL em links de uma fonte"))

    ids_manifesto = {c["id"] for c in categorias}
    for arquivo in sorted(pasta.iterdir()):
        if arquivo.name == MANIFESTO or arquivo.name.startswith(".") or arquivo.name.endswith("~"):
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
        erros_arquivo = [erro_em(rotulo, linhas, c, m) for c, m in valida(dados, esquema_arquivo)]
        if erros_arquivo:
            erros.extend(erros_arquivo)
            continue
        for j, fonte in enumerate(dados["fontes"]):
            base = ("fontes", j)
            problemas = valida(fonte, esquema_fonte, base)
            erros.extend(erro_em(rotulo, linhas, c, m) for c, m in problemas)
            if not isinstance(fonte, dict):
                continue
            # Campos com erro de formato ficam fora das verificações seguintes; os demais
            # são verificados agora, para o contribuidor ver todos os erros de uma vez.
            invalidos = {c[2] for c, _ in problemas if len(c) > 2}
            invalidos |= {campo for campo in esquema_fonte["required"] if campo not in fonte}
            erros.extend(_verifica_fonte(rotulo, linhas, fonte, base, invalidos, termos, ids_vistos))
        fontes[categoria["id"]] = dados["fontes"]

    if erros:
        return None, erros
    return {"categorias": categorias, "fontes": fontes}, []
````

- [ ] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 103 tests` e `OK`.

- [ ] **Passo 5: commit.**

````bash
git add tools/catalogo_io.py tests/test_uma_rodada.py
git commit -m "Valida cada fonte à parte para mostrar todos os erros de uma vez" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 5: prefixo do id, override sem lista vazia e classificação na taxonomia

**Arquivos:**
- Modificar: `tools/catalogo_io.py`, `tests/test_catalogo_io.py`
- Modificar (substituir por inteiro): `data/taxonomy.json`
- Teste: `tests/test_regras_de_conteudo.py`

**Interfaces:**
- Consome: `_verifica_fonte` (Tarefa 4).
- Produz: `_verifica_fonte(..., categoria_id)` com as regras de R12 e R13; `data/taxonomy.json` com `classificacao` = `heuristica`, `override`.

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_regras_de_conteudo.py`:**

````python
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import ALFA, BETA, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402


def carrega(arquivos):
    with tempfile.TemporaryDirectory() as tmp:
        return carrega_catalogo(cria_repo(tmp, arquivos))[1]


class TestRegrasDeConteudo(unittest.TestCase):
    def test_prefixo_do_id_precisa_ser_a_categoria_do_arquivo(self):
        self.assertEqual(carrega({"catalogo/beta.yml": BETA.replace("beta/terceira-fonte", "alfa/terceira-fonte")}), [
            "catalogo/beta.yml:2: fontes[0].id: o id precisa começar com 'beta/', o nome do arquivo da categoria",
        ])

    def test_fonte_override_precisa_de_input_e_output(self):
        texto = ALFA.replace("input: [nome]", "input: []").replace("output: [processo]", "output: []")
        self.assertEqual(carrega({"catalogo/alfa.yml": texto}), [
            "catalogo/alfa.yml:23: fontes[1].input: lista vazia em fonte com classificacao override; "
            "declare ao menos um termo (use [nenhum] quando a fonte não pede identificador)",
            "catalogo/alfa.yml:24: fontes[1].output: lista vazia em fonte com classificacao override; declare ao menos um termo",
        ])

    def test_fonte_heuristica_herdada_pode_ter_lista_vazia(self):
        self.assertEqual(carrega({"catalogo/beta.yml": BETA.replace("input: [nenhum]", "input: []")}), [])


class TestTaxonomiaDaClassificacao(unittest.TestCase):
    def setUp(self):
        self.taxonomia = json.loads((RAIZ / "data" / "taxonomy.json").read_text(encoding="utf-8"))
        self.esquema = json.loads((RAIZ / "data" / "schemas" / "catalogo.schema.json").read_text(encoding="utf-8"))

    def test_taxonomia_e_schema_aceitam_os_mesmos_termos(self):
        enum = self.esquema["properties"]["fontes"]["items"]["properties"]["classificacao"]["enum"]
        self.assertEqual(sorted(self.taxonomia["classificacao"]["termos"]), sorted(enum))
        self.assertEqual(sorted(enum), ["heuristica", "override"])

    def test_termos_explicam_o_uso_em_fonte_nova(self):
        termos = self.taxonomia["classificacao"]["termos"]
        self.assertIn("anterior à spec 001", termos["heuristica"])
        self.assertIn("fonte nova", termos["override"])

    def test_textos_da_taxonomia_nao_citam_arquivos_que_nao_existem(self):
        texto = (RAIZ / "data" / "taxonomy.json").read_text(encoding="utf-8")
        for proibido in ("CLAUDE.md", "sources.json", "parser", "overrides"):
            self.assertNotIn(proibido, texto)


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_regras_de_conteudo.py
````

Esperado: `FAILED (failures=5)`.

- [ ] **Passo 3: implementar. Em `tools/catalogo_io.py`, trocar:**

````python
def _verifica_fonte(rotulo, linhas, fonte, base, invalidos, termos, ids_vistos):
    """Taxonomia, coerência entre links e markdown e id único, nos campos sem erro de formato."""
````

por:

````python
def _verifica_fonte(rotulo, linhas, fonte, base, invalidos, termos, ids_vistos, categoria_id):
    """Taxonomia, coerência entre links e markdown e id, nos campos sem erro de formato."""
````

- [ ] **Passo 4: implementar. Em `tools/catalogo_io.py`, trocar:**

````python
    for eixo in ("tipo_fonte", "classificacao"):
        if ok(eixo) and fonte[eixo] not in termos[eixo]:
            erros.append(erro_em(rotulo, linhas, base + (eixo,), fora_da_taxonomia(eixo, fonte[eixo], termos[eixo])))
````

por:

````python
    for eixo in ("tipo_fonte", "classificacao"):
        if ok(eixo) and fonte[eixo] not in termos[eixo]:
            erros.append(erro_em(rotulo, linhas, base + (eixo,), fora_da_taxonomia(eixo, fonte[eixo], termos[eixo])))
    # Fontes heuristica herdadas da migração podem ter lista vazia; fonte nova ou revisada (override), não.
    for eixo, dica in (("input", " (use [nenhum] quando a fonte não pede identificador)"), ("output", "")):
        if ok(eixo, "classificacao") and fonte["classificacao"] == "override" and not fonte[eixo]:
            erros.append(erro_em(rotulo, linhas, base + (eixo,),
                                 f"lista vazia em fonte com classificacao override; declare ao menos um termo{dica}"))
````

- [ ] **Passo 5: implementar. Em `tools/catalogo_io.py`, trocar:**

````python
    if ok("id"):
        local = f"{rotulo}:{linha_de(linhas, base + ('id',))}"
````

por:

````python
    if ok("id"):
        if fonte["id"].split("/")[0] != categoria_id:
            erros.append(erro_em(rotulo, linhas, base + ("id",),
                                 f"o id precisa começar com '{categoria_id}/', o nome do arquivo da categoria"))
        local = f"{rotulo}:{linha_de(linhas, base + ('id',))}"
````

- [ ] **Passo 6: implementar. Em `tools/catalogo_io.py`, trocar:**

````python
            erros.extend(_verifica_fonte(rotulo, linhas, fonte, base, invalidos, termos, ids_vistos))
````

por:

````python
            erros.extend(_verifica_fonte(rotulo, linhas, fonte, base, invalidos, termos, ids_vistos, categoria["id"]))
````

- [ ] **Passo 7: implementar. Substituir o conteúdo de `data/taxonomy.json`:**

````json
{
  "_sobre": "Vocabulário controlado do catálogo OSINT Brazuca. O build valida cada fonte de catalogo/ contra estas listas e falha se encontrar termo fora delas. Arquivo editado à mão: acrescente o termo aqui antes de usá-lo em catalogo/<categoria>.yml (e nos modelos de issue em .github/ISSUE_TEMPLATE/).",
  "input": {
    "_sobre": "O que o analista precisa ter em mãos para consultar a fonte. 'nenhum' é o valor correto para fontes que se navega (datasets, mapas, câmeras), não se consulta.",
    "termos": {
      "nenhum": "Não requer identificador; a fonte é navegada ou baixada por inteiro",
      "cpf": "Cadastro de Pessoa Física",
      "cnpj": "Cadastro Nacional da Pessoa Jurídica",
      "nome": "Nome de pessoa física",
      "razao_social": "Razão social ou nome fantasia de empresa",
      "titulo_eleitor": "Número do título de eleitor",
      "numero_processo": "Número de processo judicial ou administrativo",
      "oab": "Número de inscrição na Ordem dos Advogados do Brasil",
      "registro_profissional": "Registro em conselho profissional (CRM, CFP, CAU, CFF, CREA...)",
      "placa": "Placa de veículo",
      "chassi": "Número de chassi de veículo",
      "renavam": "Código Renavam de veículo",
      "imei": "IMEI de aparelho celular",
      "telefone": "Número de telefone fixo ou celular",
      "email": "Endereço de e-mail",
      "dominio": "Nome de domínio",
      "ip": "Endereço IP",
      "asn": "Número de sistema autônomo (ASN)",
      "cep": "Código de Endereçamento Postal",
      "endereco": "Logradouro ou endereço completo",
      "municipio": "Nome ou código de município",
      "uf": "Sigla de unidade federativa",
      "coordenadas": "Latitude e longitude",
      "matricula_imovel": "Matrícula de imóvel em cartório de registro",
      "car": "Cadastro Ambiental Rural",
      "inscricao_estadual": "Inscrição estadual ou NIRE",
      "prefixo_aeronave": "Marca de matrícula de aeronave (prefixo)",
      "embarcacao": "Nome ou registro de embarcação",
      "cnes": "Cadastro Nacional de Estabelecimentos de Saúde",
      "codigo_ibge": "Código de município ou região do IBGE",
      "cns": "Cartão Nacional de Saúde de profissional ou Código Nacional de Serventia de cartório"
    }
  },
  "output": {
    "_sobre": "Que tipo de dado a fonte devolve.",
    "termos": {
      "dados_cadastrais": "Dados de identificação de pessoa ou empresa",
      "situacao_cadastral": "Status de regularidade de um cadastro",
      "socios": "Quadro societário",
      "cnae": "Classificação de atividade econômica",
      "endereco": "Endereço ou localização",
      "processo": "Processo judicial ou administrativo",
      "partes": "Partes envolvidas em processo",
      "movimentacao": "Andamento e movimentações processuais",
      "certidao": "Certidão emitida pela fonte",
      "antecedentes": "Antecedentes criminais",
      "mandado_prisao": "Mandado de prisão ou situação de procurado",
      "beneficio": "Benefício social ou previdenciário",
      "remuneracao": "Remuneração de agente público",
      "contrato_publico": "Contrato, convênio ou repasse público",
      "licitacao": "Processo licitatório ou compra pública",
      "sancao": "Sanção, impedimento ou inidoneidade",
      "veiculo": "Dados de veículo",
      "multa": "Multa ou infração",
      "debito": "Débito ou pendência financeira",
      "imovel": "Dados de imóvel urbano ou rural",
      "area_rural": "Perímetro ou dados de área rural",
      "licenca_ambiental": "Licença ou autorização ambiental",
      "auto_infracao": "Auto de infração ou embargo",
      "operadora": "Operadora e situação de linha telefônica",
      "erb": "Estação rádio base",
      "radiofrequencia": "Radiofrequência ou indicativo",
      "outorga": "Outorga de radiodifusão ou telecomunicações",
      "dataset": "Conjunto de dados para download em massa",
      "diario_oficial": "Publicação em diário oficial",
      "api_json": "Resposta estruturada de API",
      "mapa": "Mapa ou camada georreferenciada",
      "imagem_satelite": "Imagem de satélite ou sensoriamento remoto",
      "video_ao_vivo": "Transmissão de vídeo ao vivo",
      "curriculo": "Currículo acadêmico ou profissional",
      "publicacao_academica": "Tese, dissertação ou artigo",
      "perfil_social": "Perfil ou conteúdo de rede social",
      "dork": "Consulta pronta para motor de busca",
      "estatistica": "Estatística, indicador ou painel agregado",
      "vinculo_profissional": "Vínculo de trabalho, registro ou certificação profissional",
      "financiamento": "Operação de crédito, incentivo ou patrocínio",
      "cartorio": "Serventia extrajudicial e seu responsável",
      "acervo_historico": "Acervo histórico, arquivo de imprensa ou documento digitalizado",
      "checagem": "Checagem de fatos ou verificação de conteúdo publicado"
    }
  },
  "tipo_fonte": {
    "_sobre": "Natureza institucional de quem mantém a fonte.",
    "termos": {
      "federal": "Órgão do governo federal",
      "estadual": "Órgão de governo estadual",
      "municipal": "Órgão de governo municipal",
      "judiciario": "Tribunal ou órgão do Poder Judiciário",
      "ministerio_publico": "Ministério Público",
      "legislativo": "Câmara, Senado ou assembleia",
      "defensoria": "Defensoria Pública",
      "ong": "Organização sem fins lucrativos",
      "privado": "Empresa ou serviço privado",
      "academico": "Instituição de ensino ou pesquisa",
      "internacional": "Fonte fora do Brasil",
      "dork": "Consulta preparada para motor de busca",
      "api": "API pública documentada",
      "indefinido": "Sem URL ou domínio não classificável"
    }
  },
  "classificacao": {
    "_sobre": "Procedência da classificação (input, output e tipo_fonte) de cada fonte.",
    "termos": {
      "heuristica": "Herdada da regra automática anterior à spec 001 e ainda não revisada por uma pessoa; não use em fonte nova",
      "override": "Definida ou revisada por uma pessoa; use em toda fonte nova e ao revisar a classificação de uma fonte heuristica"
    }
  }
}
````

- [ ] **Passo 8: ajustar o teste de id repetido, que agora também acusa o prefixo. Em `tests/test_catalogo_io.py`, trocar:**

````python
        self.assertEqual(erros, ["catalogo/beta.yml:2: fontes[0].id: id 'alfa/primeira-fonte' repetido; já usado em catalogo/alfa.yml:2"])
````

por:

````python
        self.assertEqual(erros, [
            "catalogo/beta.yml:2: fontes[0].id: o id precisa começar com 'beta/', o nome do arquivo da categoria",
            "catalogo/beta.yml:2: fontes[0].id: id 'alfa/primeira-fonte' repetido; já usado em catalogo/alfa.yml:2",
        ])
````

- [ ] **Passo 9: rodar e ver passar; o catálogo real continua válido.**

````bash
python3 -m unittest discover -s tests
python3 tools/build_dataset.py --check
````

Esperado: `Ran 109 tests`, `OK` e `OK: catálogo válido e arquivos gerados atualizados.`

- [ ] **Passo 10: commit.**

````bash
git add tools/catalogo_io.py data/taxonomy.json tests/test_regras_de_conteudo.py tests/test_catalogo_io.py
git commit -m "Confere prefixo do id e classificação de fonte nova, e tira indefinido da classificação" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 6: modo de PR no build (`--alterados`)

**Arquivos:**
- Modificar (substituir por inteiro): `tools/build_dataset.py`
- Teste: `tests/test_alterados.py`

**Interfaces:**
- Consome: `carrega_catalogo`, `gera_saidas`, `grava` (Tarefa 1).
- Produz: `--check --alterados LISTA` (arquivo ou `-`); `le_alterados(origem) -> set[str]`; `confere(raiz, saidas, alterados) -> int`. Gerado na lista e diferente: erro `arquivo:linha: difere do gerado a partir de catalogo/`. Gerado fora da lista e diferente: `AVISO: desatualizados, regenerados no main depois do merge: ...` e `OK: catálogo válido e nenhum arquivo gerado editado à mão.`

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_alterados.py`:**

````python
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import BETA, cria_repo  # noqa: E402
from build_dataset import main  # noqa: E402


def roda(raiz, *args, entrada=""):
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro), \
            mock.patch("sys.stdin", io.StringIO(entrada)):
        codigo = main(list(args), raiz=raiz)
    return codigo, saida.getvalue(), erro.getvalue()


class TestAlterados(unittest.TestCase):
    """--check --alterados: o PR pode deixar os gerados desatualizados, mas não editá-los à mão."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = cria_repo(self._tmp.name)
        roda(self.raiz)
        self.beta = self.raiz / "catalogo" / "beta.yml"
        self.readme = self.raiz / "README.md"

    def tearDown(self):
        self._tmp.cleanup()

    def test_pr_so_com_catalogo_passa_e_avisa_que_gerados_serao_regenerados(self):
        self.beta.write_text(BETA.replace("Descrição da terceira.", "Nova descrição."), encoding="utf-8")
        codigo, saida, erro = roda(self.raiz, "--check", "--alterados", "-", entrada="catalogo/beta.yml\n")
        self.assertEqual((codigo, erro), (0, ""))
        self.assertIn("AVISO: desatualizados, regenerados no main depois do merge: README.md, data/sources.json, data/index.json", saida)
        self.assertIn("OK: catálogo válido e nenhum arquivo gerado editado à mão.", saida)

    def test_readme_editado_a_mao_no_pr_falha(self):
        self.readme.write_text(self.readme.read_text(encoding="utf-8").replace("Descrição da terceira.", "Editado."), encoding="utf-8")
        codigo, _, erro = roda(self.raiz, "--check", "--alterados", "-", entrada="README.md\n")
        self.assertEqual(codigo, 1)
        self.assertRegex(erro, r"README\.md:\d+: difere do gerado a partir de catalogo/")
        self.assertIn("não precisa incluir README.md nem data/*.json", erro)

    def test_gerado_alterado_e_identico_ao_gerado_passa(self):
        self.beta.write_text(BETA.replace("Descrição da terceira.", "Nova descrição."), encoding="utf-8")
        roda(self.raiz)
        lista = "catalogo/beta.yml\nREADME.md\ndata/sources.json\ndata/index.json\n"
        codigo, saida, _ = roda(self.raiz, "--check", "--alterados", "-", entrada=lista)
        self.assertEqual(codigo, 0)
        self.assertIn("OK: catálogo válido e arquivos gerados atualizados.", saida)

    def test_lista_lida_de_arquivo(self):
        self.readme.write_text("editado\n", encoding="utf-8")
        lista = Path(self._tmp.name) / "alterados.txt"
        lista.write_text("README.md\n", encoding="utf-8")
        codigo, _, erro = roda(self.raiz, "--check", "--alterados", str(lista))
        self.assertEqual(codigo, 1)
        self.assertIn("README.md:1: difere", erro)

    def test_catalogo_invalido_falha_mesmo_sem_gerados_na_lista(self):
        self.beta.write_text(BETA.replace("output: [dataset]", "output: [datset]"), encoding="utf-8")
        codigo, _, erro = roda(self.raiz, "--check", "--alterados", "-", entrada="catalogo/beta.yml\n")
        self.assertEqual(codigo, 1)
        self.assertIn("output 'datset' fora da taxonomia", erro)

    def test_alterados_sem_check_e_erro_de_uso(self):
        with self.assertRaises(SystemExit) as saida, contextlib.redirect_stderr(io.StringIO()):
            main(["--alterados", "-"], raiz=self.raiz)
        self.assertEqual(saida.exception.code, 2)

    def test_check_estrito_continua_igual_sem_alterados(self):
        self.beta.write_text(BETA.replace("Descrição da terceira.", "Nova descrição."), encoding="utf-8")
        codigo, _, erro = roda(self.raiz, "--check")
        self.assertEqual(codigo, 1)
        self.assertRegex(erro, r"README\.md:\d+: difere")

    def test_report_e_check_juntos(self):
        codigo, saida, _ = roda(self.raiz, "--report", "--check")
        self.assertEqual(codigo, 0)
        self.assertIn("fontes .............. 3", saida)
        self.assertIn("OK: catálogo válido e arquivos gerados atualizados.", saida)


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_alterados.py
````

Esperado: `FAILED (errors=5)`, com `error: unrecognized arguments: --alterados -`.

- [ ] **Passo 3: implementar. Substituir o conteúdo de `tools/build_dataset.py`:**

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

    git diff --name-only HEAD^1 HEAD | python3 tools/build_dataset.py --check --alterados -
        modo de PR: valida o catálogo e falha só se um arquivo gerado da lista
        foi editado à mão; gerado fora da lista pode estar desatualizado,
        porque o mantenedor o regenera no main depois do merge (ADR 0002)

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


def le_alterados(origem):
    """Caminhos alterados, um por linha, lidos de um arquivo ou da entrada padrão ('-')."""
    texto = sys.stdin.read() if origem == "-" else Path(origem).read_text(encoding="utf-8")
    return {linha.strip() for linha in texto.splitlines() if linha.strip()}


def relatorio(saidas):
    fontes = json.loads(saidas["data/sources.json"])["sources"]
    links = json.loads(saidas["data/index.json"])["links"]
    classes = Counter(f["classificacao"] for f in fontes)
    print(f"categorias .......... {len({f['categoria_id'] for f in fontes})}")
    print(f"fontes .............. {len(fontes)}")
    print(f"links ............... {len(links)}")
    print(f"classificação: heurística {classes['heuristica']} | override {classes['override']}")


def confere(raiz, saidas, alterados):
    """--check: 0 se os gerados estão em dia (ou, com alterados, se nenhum foi editado à mão)."""
    desatualizados, pendentes = [], []
    for relativo, conteudo in saidas.items():
        caminho = raiz / relativo
        atual = caminho.read_text(encoding="utf-8") if caminho.exists() else ""
        if atual == conteudo:
            continue
        if alterados is None or relativo in alterados:
            desatualizados.append(f"{relativo}:{primeira_diferenca(atual, conteudo)}: difere do gerado a partir de catalogo/")
        else:
            pendentes.append(relativo)
    if desatualizados:
        print("ERRO: arquivos gerados desatualizados ou editados à mão:", file=sys.stderr)
        for linha in desatualizados:
            print(f"  {linha}", file=sys.stderr)
        print("Edite catalogo/<categoria>.yml (nunca o README.md) e rode: python3 tools/build_dataset.py",
              file=sys.stderr)
        if alterados is not None:
            print("Ou desfaça a mudança nesses arquivos: o PR não precisa incluir README.md nem data/*.json, "
                  "que são regenerados no main depois do merge.", file=sys.stderr)
        return 1
    if pendentes:
        print(f"AVISO: desatualizados, regenerados no main depois do merge: {', '.join(pendentes)}")
        print("OK: catálogo válido e nenhum arquivo gerado editado à mão.")
    else:
        print("OK: catálogo válido e arquivos gerados atualizados.")
    return 0


def main(argv=None, raiz=RAIZ):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="falha se o catálogo for inválido ou os arquivos gerados estiverem desatualizados")
    ap.add_argument("--alterados", metavar="LISTA",
                    help="com --check: arquivo com os caminhos alterados no PR, um por linha ('-' lê da entrada "
                         "padrão); só os arquivos gerados dessa lista precisam estar em dia")
    ap.add_argument("--report", action="store_true", help="imprime estatísticas do catálogo")
    args = ap.parse_args(argv)
    if args.alterados and not args.check:
        ap.error("--alterados só vale junto com --check")
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
        return confere(raiz, saidas, le_alterados(args.alterados) if args.alterados else None)

    if not args.report:
        for relativo, conteudo in saidas.items():
            grava(raiz / relativo, conteudo)
            print(f"escrito {relativo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [ ] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
echo catalogo/saude.yml | python3 tools/build_dataset.py --check --alterados -
````

Esperado: `Ran 117 tests`, `OK` e `OK: catálogo válido e arquivos gerados atualizados.`

- [ ] **Passo 5: commit.**

````bash
git add tools/build_dataset.py tests/test_alterados.py
git commit -m "Adiciona ao build o modo de PR, que só recusa arquivo gerado editado à mão" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 7: hook de pre-commit confere o índice

**Arquivos:**
- Modificar (substituir por inteiro): `tools/hooks/pre-commit` (continua `100755`), `tests/test_ci.py`
- Teste: `tests/test_hook.py`

**Interfaces:**
- Consome: `build_dataset.py --check --alterados` (Tarefa 6), `validar_docs.py --avisos`.
- Produz: hook que copia o índice para uma pasta temporária, roda as duas verificações ali e falha no fim se alguma falhou. O teste do hook sai de `tests/test_ci.py` e vai para `tests/test_hook.py`.

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_hook.py`:**

````python
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from validar_docs import DOCS  # noqa: E402

HOOK = RAIZ / "tools" / "hooks" / "pre-commit"
TRAVESSAO = "\u2014"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


class TestHookPreCommit(unittest.TestCase):
    """O hook confere o índice do git (o que vai entrar no commit), num repositório descartável sem commits."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.modelo = Path(cls._tmp.name) / "modelo"
        cls.modelo.mkdir()
        for nome in DOCS:
            shutil.copy(RAIZ / nome, cls.modelo / nome)
        for pasta in ("catalogo", "data", "tools"):
            shutil.copytree(RAIZ / pasta, cls.modelo / pasta, ignore=shutil.ignore_patterns("__pycache__"))
        subprocess.run([sys.executable, "tools/build_dataset.py"], cwd=cls.modelo, capture_output=True, check=True)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.repo = Path(self._dir.name) / "repo"
        shutil.copytree(self.modelo, self.repo)
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")

    def tearDown(self):
        self._dir.cleanup()

    def hook(self):
        ambiente = dict(os.environ, PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ["PATH"])
        return subprocess.run(["sh", "tools/hooks/pre-commit"], cwd=self.repo, capture_output=True, text=True, env=ambiente)

    def edita(self, relativo, antes, depois):
        caminho = self.repo / relativo
        texto = caminho.read_text(encoding="utf-8")
        self.assertIn(antes, texto)
        caminho.write_text(texto.replace(antes, depois, 1), encoding="utf-8")

    def test_indice_consistente_passa(self):
        resultado = self.hook()
        self.assertEqual(resultado.returncode, 0, resultado.stderr)

    def test_readme_editado_so_na_arvore_de_trabalho_nao_bloqueia(self):
        self.edita("README.md", "## ", "## Editado ")
        self.assertEqual(self.hook().returncode, 0)

    def test_readme_editado_e_adicionado_bloqueia(self):
        self.edita("README.md", "## ", "## Editado ")
        git(self.repo, "add", "README.md")
        resultado = self.hook()
        self.assertEqual(resultado.returncode, 1)
        self.assertRegex(resultado.stderr, r"README\.md:\d+: difere do gerado a partir de catalogo/")

    def test_confere_o_indice_e_nao_a_arvore_de_trabalho(self):
        original = (self.repo / "catalogo" / "saude.yml").read_text(encoding="utf-8")
        self.edita("catalogo/saude.yml", "tipo_fonte: federal", "tipo_fonte: federall")
        git(self.repo, "add", "catalogo/saude.yml")
        (self.repo / "catalogo" / "saude.yml").write_text(original, encoding="utf-8")
        resultado = self.hook()
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("tipo_fonte 'federall' fora da taxonomia", resultado.stderr)

    def test_erros_de_documento_e_de_catalogo_aparecem_juntos(self):
        self.edita("CONTRIBUICAO.md", "Obrigado", f"Obrigado {TRAVESSAO}")
        self.edita("catalogo/saude.yml", "tipo_fonte: federal", "tipo_fonte: federall")
        git(self.repo, "add", "-A")
        resultado = self.hook()
        self.assertEqual(resultado.returncode, 1)
        self.assertIn("CONTRIBUICAO.md", resultado.stderr)
        self.assertIn("travessão", resultado.stderr)
        self.assertIn("tipo_fonte 'federall' fora da taxonomia", resultado.stderr)

    def test_hook_executavel_no_git_e_sem_overrides(self):
        texto = HOOK.read_text(encoding="utf-8")
        self.assertIn("git checkout-index --all --prefix=", texto)
        self.assertIn("python3 tools/build_dataset.py --check --alterados", texto)
        self.assertNotIn("overrides.json", texto)
        self.assertTrue(os.access(HOOK, os.X_OK))
        modo = git(RAIZ, "ls-files", "-s", "tools/hooks/pre-commit").stdout.split()[0]
        self.assertEqual(modo, "100755")


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_hook.py
````

Esperado: `FAILED (failures=4)`: o hook atual barra o `README.md` editado só na árvore, aprova o índice com erro, para no primeiro erro e não tem `checkout-index`.

- [ ] **Passo 3: implementar. Substituir o conteúdo de `tools/hooks/pre-commit`:**

````sh
#!/bin/sh
# Valida o que vai entrar no commit (o índice do git, não a árvore de trabalho):
# formatação dos documentos, catálogo e arquivos gerados. Roda todas as
# verificações antes de falhar, para mostrar todos os erros de uma vez.
# Ativar com:
#   git config core.hooksPath tools/hooks
# Requer PyYAML: python3 -m pip install -r requirements.txt
set -e
cd "$(git rev-parse --show-toplevel)"

if git diff --cached --quiet -- '*.md' catalogo data tools requirements.txt; then
  exit 0
fi

# Cópia do índice numa pasta temporária, apagada ao sair.
copia="$(mktemp -d)"
trap 'rm -rf "$copia"' EXIT
git checkout-index --all --prefix="$copia/"
git diff --cached --name-only > "$copia/.alterados"

cd "$copia"
falhou=0
# 1. Regras de formatação (travessão, menu, âncoras) e avisos de curadoria
python3 tools/validar_docs.py --avisos || falhou=1
# 2. Catálogo (schema, taxonomia, ids, links) e arquivos gerados não editados à mão
python3 tools/build_dataset.py --check --alterados .alterados || falhou=1
exit "$falhou"
````

- [ ] **Passo 4: tirar de `tests/test_ci.py` o teste antigo do hook. Substituir o conteúdo de `tests/test_ci.py`:**

````python
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOW = RAIZ / ".github" / "workflows" / "validar-dataset.yml"


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

    def test_requirements_fixa_so_o_pyyaml(self):
        linhas = [l for l in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
        self.assertEqual(linhas, ["PyYAML==6.0.3"])


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 5: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
git ls-files -s tools/hooks/pre-commit | cut -c1-6
````

Esperado: `Ran 122 tests`, `OK` e `100755`.

- [ ] **Passo 6: commit.**

````bash
git add tools/hooks/pre-commit tests/test_hook.py tests/test_ci.py
git commit -m "Faz o hook de pre-commit conferir o índice e mostrar todos os erros" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 8: CI de PR sem gerados e aviso de gerados atrasados no main

**Arquivos:**
- Modificar (substituir por inteiro): `.github/workflows/validar-dataset.yml`, `tests/test_ci.py`

**Interfaces:**
- Consome: `build_dataset.py --check --alterados -` (Tarefa 6) e `build_dataset.py --check` estrito.
- Produz: job `validar` (PR e push) e job `gerados-em-dia`, de nome "Arquivos gerados em dia no main" (só push), ambos com `contents: read` e sem commit. A seção "Para mantenedores" que a anotação de erro aponta (`CONTRIBUICAO.md#mantenedores`) é escrita na Tarefa 10.

- [ ] **Passo 1: escrever o teste que falha. Substituir o conteúdo de `tests/test_ci.py`:**

````python
import unittest
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOW = RAIZ / ".github" / "workflows" / "validar-dataset.yml"
CAMINHOS = ["*.md", "catalogo/**", "data/**", "tools/**", "tests/**", "requirements.txt",
            ".gitattributes", ".github/**"]


def carrega_workflow():
    dados = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    dados["on"] = dados.pop(True, dados.get("on"))  # o YAML 1.1 lê a chave on como True
    return dados


def comandos(job):
    return [passo.get("run", "") for passo in job["steps"]]


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.wf = carrega_workflow()

    def test_dispara_em_pr_e_em_push_no_main_com_os_mesmos_caminhos(self):
        self.assertEqual(set(self.wf["on"]), {"push", "pull_request"})
        self.assertEqual(self.wf["on"]["push"]["branches"], ["main"])
        self.assertEqual(self.wf["on"]["push"]["paths"], CAMINHOS)
        self.assertEqual(self.wf["on"]["pull_request"]["paths"], CAMINHOS)

    def test_nenhum_job_grava_no_repositorio(self):
        self.assertEqual(self.wf["permissions"], {"contents": "read"})
        for nome, job in self.wf["jobs"].items():
            self.assertNotIn("permissions", job, nome)
        texto = WORKFLOW.read_text(encoding="utf-8")
        for proibido in ("git push", "git commit", "graphql", "contents: write"):
            self.assertNotIn(proibido, texto)

    def test_validar_confere_edicao_a_mao_regenera_e_roda_tudo(self):
        job = self.wf["jobs"]["validar"]
        self.assertEqual(job["steps"][0]["with"]["fetch-depth"], 2)
        self.assertEqual(comandos(job)[2:], [
            "python3 -m pip install -r requirements.txt",
            "git diff --name-only HEAD^1 HEAD | python3 tools/build_dataset.py --check --alterados -",
            "python3 tools/build_dataset.py",
            "python3 -m unittest discover -s tests -v",
            "python3 tools/validar_docs.py",
        ])
        for passo in job["steps"][4:]:
            self.assertEqual(passo.get("if"), "success() || failure()", passo["name"])

    def test_gerados_em_dia_so_no_push_com_aviso_ao_mantenedor(self):
        job = self.wf["jobs"]["gerados-em-dia"]
        self.assertEqual(job["name"], "Arquivos gerados em dia no main")
        self.assertEqual(job["if"], "github.event_name == 'push'")
        script = comandos(job)[-1]
        self.assertIn("python3 tools/build_dataset.py --check", script)
        self.assertNotIn("--alterados", script)
        self.assertIn("::error title=Arquivos gerados desatualizados::", script)
        self.assertIn("CONTRIBUICAO.md#mantenedores", script)


class TestDependencias(unittest.TestCase):
    def test_requirements_fixa_so_o_pyyaml(self):
        linhas = [l for l in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
        self.assertEqual(linhas, ["PyYAML==6.0.3"])


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_ci.py
````

Esperado: `FAILED (failures=1, errors=3)`: o workflow da spec 001 não tem `permissions`, `fetch-depth` nem o job `gerados-em-dia` (`KeyError`), e os caminhos ainda não incluem `.gitattributes` e `.github/**`.

- [ ] **Passo 3: implementar. Substituir o conteúdo de `.github/workflows/validar-dataset.yml`:**

````yaml
name: Validar catálogo e dataset

# PR: valida o catálogo e recusa arquivo gerado editado à mão; o PR não precisa
# trazer README.md nem data/*.json. Push no main: valida de novo e, num job à
# parte, mostra se os gerados ficaram desatualizados; o mantenedor os regenera
# num commit dele (ADR 0002). Nenhum job grava no repositório.
on:
  push:
    branches: [main]
    paths: ["*.md", "catalogo/**", "data/**", "tools/**", "tests/**", "requirements.txt", ".gitattributes", ".github/**"]
  pull_request:
    paths: ["*.md", "catalogo/**", "data/**", "tools/**", "tests/**", "requirements.txt", ".gitattributes", ".github/**"]

permissions:
  contents: read

jobs:
  validar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Dependências (versão fixada)
        run: python3 -m pip install -r requirements.txt

      - name: Catálogo válido e nenhum arquivo gerado editado à mão
        run: git diff --name-only HEAD^1 HEAD | python3 tools/build_dataset.py --check --alterados -

      - name: Regenerar README e dataset nesta execução
        if: success() || failure()
        run: python3 tools/build_dataset.py

      - name: Testes das ferramentas
        if: success() || failure()
        run: python3 -m unittest discover -s tests -v

      - name: Regras de formatação dos documentos
        if: success() || failure()
        run: python3 tools/validar_docs.py

  gerados-em-dia:
    name: Arquivos gerados em dia no main
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Dependências (versão fixada)
        run: python3 -m pip install -r requirements.txt

      - name: README.md e data/*.json iguais ao gerado a partir de catalogo/
        run: |
          if ! python3 tools/build_dataset.py --check; then
            echo "::error title=Arquivos gerados desatualizados::Mantenedor: rode python3 tools/build_dataset.py e faça um commit assinado com README.md e data/*.json (CONTRIBUICAO.md#mantenedores)."
            exit 1
          fi
````

- [ ] **Passo 4: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
command -v actionlint >/dev/null && actionlint .github/workflows/validar-dataset.yml && echo actionlint-ok
````

Esperado: `Ran 125 tests`, `OK` e, com `actionlint` instalado, `actionlint-ok`.

- [ ] **Passo 5: commit.**

````bash
git add .github/workflows/validar-dataset.yml tests/test_ci.py
git commit -m "Valida PR sem arquivos gerados e mostra no main quando os gerados atrasam" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 9: formulários de issue e modelo de pull request

**Arquivos:**
- Criar: `.github/ISSUE_TEMPLATE/nova-fonte.yml`, `.github/ISSUE_TEMPLATE/link-quebrado.yml`, `.github/ISSUE_TEMPLATE/correcao.yml`, `.github/ISSUE_TEMPLATE/config.yml`, `.github/PULL_REQUEST_TEMPLATE.md`
- Teste: `tests/test_modelos.py`

**Interfaces:**
- Consome: `catalogo/_categorias.yml` (títulos e ids, na ordem), `data/taxonomy.json` (termos e descrições, Tarefa 5).
- Produz: formulários com ids `nome`, `descricao`, `links`, `categoria`, `input`, `output`, `tipo_fonte`, `confirmacoes` (nova fonte), `fonte`, `url`, `erro`, `data_teste`, `alternativa`, `confirmacoes` (link quebrado), `fonte`, `o_que`, `correcao`, `referencia` (correção).

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_modelos.py`:**

````python
import json
import re
import unittest
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
MODELOS = RAIZ / ".github" / "ISSUE_TEMPLATE"
FORMULARIOS = ("nova-fonte.yml", "link-quebrado.yml", "correcao.yml")
TIPOS_DE_CAMPO = {"markdown", "input", "textarea", "dropdown", "checkboxes"}


def formulario(nome):
    return yaml.safe_load((MODELOS / nome).read_text(encoding="utf-8"))


def campo(form, ident):
    return next(c for c in form["body"] if c.get("id") == ident)


class TestFormulariosDeIssue(unittest.TestCase):
    def test_formularios_seguem_a_estrutura_do_github(self):
        for nome in FORMULARIOS:
            with self.subTest(nome=nome):
                form = formulario(nome)
                self.assertTrue({"name", "description", "title", "labels", "body"} <= set(form))
                ids = [c["id"] for c in form["body"] if "id" in c]
                self.assertEqual(len(ids), len(set(ids)))
                for item in form["body"]:
                    self.assertIn(item["type"], TIPOS_DE_CAMPO)
                    self.assertIn("label" if item["type"] != "markdown" else "value", item["attributes"])
                    if item["type"] != "markdown":
                        self.assertRegex(item["id"], r"^[a-z_]+$")

    def test_titulos_e_rotulos(self):
        esperado = {"nova-fonte.yml": ("[NOVA FONTE] ", ["nova fonte"]),
                    "link-quebrado.yml": ("[LINK QUEBRADO] ", ["link quebrado"]),
                    "correcao.yml": ("[CORREÇÃO] ", ["correção"])}
        for nome, (titulo, rotulos) in esperado.items():
            form = formulario(nome)
            self.assertEqual((form["title"], form["labels"]), (titulo, rotulos))

    def test_categorias_da_nova_fonte_seguem_o_manifesto(self):
        manifesto = yaml.safe_load((RAIZ / "catalogo" / "_categorias.yml").read_text(encoding="utf-8"))
        opcoes = campo(formulario("nova-fonte.yml"), "categoria")["attributes"]["options"]
        self.assertEqual(opcoes, [f"{c['titulo']} ({c['id']})" for c in manifesto["categorias"]],
                         "atualize .github/ISSUE_TEMPLATE/nova-fonte.yml junto com catalogo/_categorias.yml")

    def test_termos_da_nova_fonte_seguem_a_taxonomia(self):
        taxonomia = json.loads((RAIZ / "data" / "taxonomy.json").read_text(encoding="utf-8"))
        form = formulario("nova-fonte.yml")
        for eixo in ("input", "output", "tipo_fonte"):
            with self.subTest(eixo=eixo):
                opcoes = campo(form, eixo)["attributes"]["options"]
                termos = taxonomia[eixo]["termos"]
                self.assertEqual(opcoes, [f"{t}: {d}" for t, d in termos.items()],
                                 "atualize .github/ISSUE_TEMPLATE/nova-fonte.yml junto com data/taxonomy.json")
        self.assertTrue(campo(form, "input")["attributes"]["multiple"])
        self.assertTrue(campo(form, "output")["attributes"]["multiple"])

    def test_campos_obrigatorios(self):
        obrigatorios = {"nova-fonte.yml": {"nome", "descricao", "links", "categoria", "confirmacoes"},
                        "link-quebrado.yml": {"fonte", "url", "erro", "confirmacoes"},
                        "correcao.yml": {"fonte", "o_que", "correcao"}}
        for nome, esperados in obrigatorios.items():
            form = formulario(nome)
            marcados = {c["id"] for c in form["body"]
                        if c.get("validations", {}).get("required")
                        or any(isinstance(o, dict) and o.get("required") for o in c["attributes"].get("options", []))}
            self.assertEqual(marcados, esperados, nome)

    def test_issue_em_branco_desligada_e_guia_ligado(self):
        config = yaml.safe_load((MODELOS / "config.yml").read_text(encoding="utf-8"))
        self.assertIs(config["blank_issues_enabled"], False)
        self.assertTrue(any("CONTRIBUICAO.md" in link["url"] for link in config["contact_links"]))

    def test_sem_travessao(self):
        arquivos = [MODELOS / n for n in FORMULARIOS + ("config.yml",)] + [RAIZ / ".github" / "PULL_REQUEST_TEMPLATE.md"]
        for caminho in arquivos:
            self.assertNotIn("\u2014", caminho.read_text(encoding="utf-8"), caminho.name)


class TestModeloDePullRequest(unittest.TestCase):
    def test_modelo_orienta_editar_so_o_catalogo(self):
        texto = (RAIZ / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn("catalogo/", texto)
        self.assertIn("Não editei `README.md`, `data/sources.json` nem `data/index.json` à mão", texto)
        self.assertIn("classificacao: override", texto)
        self.assertIn("CONTRIBUICAO.md", texto)
        self.assertEqual(len(re.findall(r"^- \[ \] ", texto, re.M)) >= 6, True)


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_modelos.py
````

Esperado: `FAILED (errors=10)`, com `FileNotFoundError` para os arquivos de `.github/`.

- [ ] **Passo 3: implementar. Criar `.github/ISSUE_TEMPLATE/nova-fonte.yml`:**

````yaml
name: Sugerir nova fonte
description: Indique uma fonte pública brasileira que ainda não está no catálogo.
title: "[NOVA FONTE] "
labels: ["nova fonte"]
body:
  - type: markdown
    attributes:
      value: |
        Obrigado pela sugestão! Antes de enviar, procure a URL em `catalogo/` (tecla `t` no GitHub, ou a busca do repositório) para conferir se a fonte já existe.
        Prefere mandar a fonte pronta num pull request? Veja o [guia de contribuição](https://github.com/webminas/osint-brazuca/blob/main/CONTRIBUICAO.md).
  - type: input
    id: nome
    attributes:
      label: Nome da fonte
      description: Como a fonte aparece no catálogo. Separe órgão e serviço com hífen simples.
      placeholder: "IBAMA - Consulta de Autuações Ambientais"
    validations:
      required: true
  - type: textarea
    id: descricao
    attributes:
      label: Descrição
      description: O que a fonte permite consultar. Diga se é gratuita e se exige cadastro.
    validations:
      required: true
  - type: textarea
    id: links
    attributes:
      label: Links
      description: "Uma URL por linha. Se o link for de um estado, acrescente a sigla da UF depois de um espaço."
      placeholder: |
        https://servicos.ibama.gov.br/ctf/publico/areasembargadas/
        https://www.sema.mt.gov.br/consulta MT
      render: text
    validations:
      required: true
  - type: dropdown
    id: categoria
    attributes:
      label: Categoria
      description: "Seção do catálogo em que a fonte entra (arquivo catalogo/<id>.yml)."
      options:
        - "Benefícios sociais (Políticas Públicas) (beneficios-sociais-politicas-publicas)"
        - "Pessoas Desaparecidas (pessoas-desaparecidas)"
        - "Pessoas Procuradas pela Justiça no Brasil (pessoas-procuradas-pela-justica-no-brasil)"
        - "Consulta de Processos (consulta-de-processos)"
        - "Busca de Informações via CPF/CNPJ/CRM/CNA (busca-de-informacoes-via-cpf-cnpj-crm-cna)"
        - "Estatísticas Segurança Pública (estatisticas-seguranca-publica)"
        - "Registros Eleitorais e Políticos (registros-eleitorais-e-politicos)"
        - "Registros de Imóveis e Propriedades (registros-de-imoveis-e-propriedades)"
        - "Registros Ambientais (registros-ambientais)"
        - "Comércio Exterior (comercio-exterior)"
        - "Registros de Marcas e Patentes (registros-de-marcas-e-patentes)"
        - "Transparência Pública e Defesa do Consumidor (transparencia-publica-e-defesa-do-consumidor)"
        - "Diários Oficiais (diarios-oficiais)"
        - "Cultura e Audiovisual (cultura-e-audiovisual)"
        - "Telecom (telecom)"
        - "Estação Rádio Base / ERBs (estacao-radio-base-erbs)"
        - "Informações Acadêmicas (informacoes-academicas)"
        - "Mapas e Georreferenciamento (mapas-e-georreferenciamento)"
        - "Território, Meio Ambiente & Fiscalização (territorio-meio-ambiente-fiscalizacao)"
        - "Saúde (saude)"
        - "Motores de Busca Contexto Brasil (motores-de-busca-contexto-brasil)"
        - "Rede Social (rede-social)"
        - "Indexadores de Serviço de Mensagens Instantâneas (indexadores-de-servico-de-mensagens-instantaneas)"
        - "Datasets / Dados Abertos (datasets-dados-abertos)"
        - "Dados de remuneração do Judiciário (dados-de-remuneracao-do-judiciario)"
        - "Consulta de Transporte Terrestre (consulta-de-transporte-terrestre)"
        - "Tracking de Viagens de Ônibus (tracking-de-viagens-de-onibus)"
        - "Consulta de Transporte Aquaviário (consulta-de-transporte-aquaviario)"
        - "Consulta de Transporte Aéreo (consulta-de-transporte-aereo)"
        - "Câmeras Online (cameras-online)"
        - "Ministérios Públicos e Defensorias Públicas (ministerios-publicos-e-defensorias-publicas)"
        - "Segurança Cibernética (seguranca-cibernetica)"
        - "Outras Buscas (outras-buscas)"
        - "APIs Públicas Brasileiras (apis-publicas-brasileiras)"
        - "Blockchain e Criptomoedas (blockchain-e-criptomoedas)"
        - "Defesa Civil e Emergências (defesa-civil-e-emergencias)"
        - "Energia e Infraestrutura (energia-e-infraestrutura)"
        - "Serviços Públicos Estaduais e Conselhos Profissionais (servicos-publicos-estaduais-e-conselhos-profissionais)"
        - "Categorias de Domínios .br (categorias-de-dominios-br)"
        - "Fontes Internacionais com Cobertura do Brasil (fontes-internacionais-com-cobertura-do-brasil)"
    validations:
      required: true
  - type: dropdown
    id: input
    attributes:
      label: O que a consulta pede (input)
      description: Opcional. Escolha "nenhum" quando a fonte é navegada ou baixada por inteiro.
      multiple: true
      options:
        - "nenhum: Não requer identificador; a fonte é navegada ou baixada por inteiro"
        - "cpf: Cadastro de Pessoa Física"
        - "cnpj: Cadastro Nacional da Pessoa Jurídica"
        - "nome: Nome de pessoa física"
        - "razao_social: Razão social ou nome fantasia de empresa"
        - "titulo_eleitor: Número do título de eleitor"
        - "numero_processo: Número de processo judicial ou administrativo"
        - "oab: Número de inscrição na Ordem dos Advogados do Brasil"
        - "registro_profissional: Registro em conselho profissional (CRM, CFP, CAU, CFF, CREA...)"
        - "placa: Placa de veículo"
        - "chassi: Número de chassi de veículo"
        - "renavam: Código Renavam de veículo"
        - "imei: IMEI de aparelho celular"
        - "telefone: Número de telefone fixo ou celular"
        - "email: Endereço de e-mail"
        - "dominio: Nome de domínio"
        - "ip: Endereço IP"
        - "asn: Número de sistema autônomo (ASN)"
        - "cep: Código de Endereçamento Postal"
        - "endereco: Logradouro ou endereço completo"
        - "municipio: Nome ou código de município"
        - "uf: Sigla de unidade federativa"
        - "coordenadas: Latitude e longitude"
        - "matricula_imovel: Matrícula de imóvel em cartório de registro"
        - "car: Cadastro Ambiental Rural"
        - "inscricao_estadual: Inscrição estadual ou NIRE"
        - "prefixo_aeronave: Marca de matrícula de aeronave (prefixo)"
        - "embarcacao: Nome ou registro de embarcação"
        - "cnes: Cadastro Nacional de Estabelecimentos de Saúde"
        - "codigo_ibge: Código de município ou região do IBGE"
        - "cns: Cartão Nacional de Saúde de profissional ou Código Nacional de Serventia de cartório"
  - type: dropdown
    id: output
    attributes:
      label: O que a fonte devolve (output)
      description: Opcional.
      multiple: true
      options:
        - "dados_cadastrais: Dados de identificação de pessoa ou empresa"
        - "situacao_cadastral: Status de regularidade de um cadastro"
        - "socios: Quadro societário"
        - "cnae: Classificação de atividade econômica"
        - "endereco: Endereço ou localização"
        - "processo: Processo judicial ou administrativo"
        - "partes: Partes envolvidas em processo"
        - "movimentacao: Andamento e movimentações processuais"
        - "certidao: Certidão emitida pela fonte"
        - "antecedentes: Antecedentes criminais"
        - "mandado_prisao: Mandado de prisão ou situação de procurado"
        - "beneficio: Benefício social ou previdenciário"
        - "remuneracao: Remuneração de agente público"
        - "contrato_publico: Contrato, convênio ou repasse público"
        - "licitacao: Processo licitatório ou compra pública"
        - "sancao: Sanção, impedimento ou inidoneidade"
        - "veiculo: Dados de veículo"
        - "multa: Multa ou infração"
        - "debito: Débito ou pendência financeira"
        - "imovel: Dados de imóvel urbano ou rural"
        - "area_rural: Perímetro ou dados de área rural"
        - "licenca_ambiental: Licença ou autorização ambiental"
        - "auto_infracao: Auto de infração ou embargo"
        - "operadora: Operadora e situação de linha telefônica"
        - "erb: Estação rádio base"
        - "radiofrequencia: Radiofrequência ou indicativo"
        - "outorga: Outorga de radiodifusão ou telecomunicações"
        - "dataset: Conjunto de dados para download em massa"
        - "diario_oficial: Publicação em diário oficial"
        - "api_json: Resposta estruturada de API"
        - "mapa: Mapa ou camada georreferenciada"
        - "imagem_satelite: Imagem de satélite ou sensoriamento remoto"
        - "video_ao_vivo: Transmissão de vídeo ao vivo"
        - "curriculo: Currículo acadêmico ou profissional"
        - "publicacao_academica: Tese, dissertação ou artigo"
        - "perfil_social: Perfil ou conteúdo de rede social"
        - "dork: Consulta pronta para motor de busca"
        - "estatistica: Estatística, indicador ou painel agregado"
        - "vinculo_profissional: Vínculo de trabalho, registro ou certificação profissional"
        - "financiamento: Operação de crédito, incentivo ou patrocínio"
        - "cartorio: Serventia extrajudicial e seu responsável"
        - "acervo_historico: Acervo histórico, arquivo de imprensa ou documento digitalizado"
        - "checagem: Checagem de fatos ou verificação de conteúdo publicado"
  - type: dropdown
    id: tipo_fonte
    attributes:
      label: Quem mantém a fonte (tipo_fonte)
      description: Opcional.
      options:
        - "federal: Órgão do governo federal"
        - "estadual: Órgão de governo estadual"
        - "municipal: Órgão de governo municipal"
        - "judiciario: Tribunal ou órgão do Poder Judiciário"
        - "ministerio_publico: Ministério Público"
        - "legislativo: Câmara, Senado ou assembleia"
        - "defensoria: Defensoria Pública"
        - "ong: Organização sem fins lucrativos"
        - "privado: Empresa ou serviço privado"
        - "academico: Instituição de ensino ou pesquisa"
        - "internacional: Fonte fora do Brasil"
        - "dork: Consulta preparada para motor de busca"
        - "api: API pública documentada"
        - "indefinido: Sem URL ou domínio não classificável"
  - type: checkboxes
    id: confirmacoes
    attributes:
      label: Confirmações
      options:
        - label: A fonte é pública, legal e relevante para o contexto brasileiro.
          required: true
        - label: Testei os links no navegador e eles funcionam.
          required: true
        - label: Procurei a URL em catalogo/ e a fonte ainda não está no catálogo.
          required: true
````

- [ ] **Passo 4: implementar. Criar `.github/ISSUE_TEMPLATE/link-quebrado.yml`:**

````yaml
name: Reportar link quebrado
description: Um link do catálogo não abre, mudou de endereço ou leva a outra página.
title: "[LINK QUEBRADO] "
labels: ["link quebrado"]
body:
  - type: markdown
    attributes:
      value: |
        Sites `.gov.br` costumam bloquear robôs e verificadores automáticos. Confira o link no navegador antes de reportar.
  - type: input
    id: fonte
    attributes:
      label: Fonte
      description: Nome da fonte no README ou o id dela (categoria/nome-da-fonte).
      placeholder: "consulta-de-processos/exemplo-consulta-publica"
    validations:
      required: true
  - type: input
    id: url
    attributes:
      label: URL quebrada
      placeholder: "https://exemplo.gov.br/consulta"
    validations:
      required: true
  - type: dropdown
    id: erro
    attributes:
      label: O que acontece
      options:
        - "Página não encontrada (404)"
        - "Site fora do ar ou sem resposta"
        - "Redireciona para outra página"
        - "Certificado inválido"
        - "Acesso bloqueado (401, 403 ou 429)"
        - "Outro"
    validations:
      required: true
  - type: input
    id: data_teste
    attributes:
      label: Data do teste
      placeholder: "12/10/2026"
  - type: input
    id: alternativa
    attributes:
      label: Endereço novo ou alternativa
      description: Opcional. Se a fonte mudou de lugar, informe a URL nova.
  - type: checkboxes
    id: confirmacoes
    attributes:
      label: Confirmações
      options:
        - label: Testei no navegador, não só com ferramenta automática.
          required: true
````

- [ ] **Passo 5: implementar. Criar `.github/ISSUE_TEMPLATE/correcao.yml`:**

````yaml
name: Corrigir uma fonte
description: Nome, descrição, classificação, categoria ou UF de uma fonte estão errados, ou a fonte está repetida.
title: "[CORREÇÃO] "
labels: ["correção"]
body:
  - type: input
    id: fonte
    attributes:
      label: Fonte
      description: Nome da fonte no README ou o id dela (categoria/nome-da-fonte).
    validations:
      required: true
  - type: dropdown
    id: o_que
    attributes:
      label: O que está errado
      multiple: true
      options:
        - "Nome"
        - "Descrição"
        - "Classificação (input, output ou tipo_fonte)"
        - "Categoria"
        - "UF de um link"
        - "Fonte repetida"
        - "Outro"
    validations:
      required: true
  - type: textarea
    id: correcao
    attributes:
      label: Correção proposta
      description: Como deveria ficar. Para classificação, use os termos de data/taxonomy.json.
    validations:
      required: true
  - type: input
    id: referencia
    attributes:
      label: Onde conferir
      description: Opcional. Página oficial ou documento que comprova a correção.
````

- [ ] **Passo 6: implementar. Criar `.github/ISSUE_TEMPLATE/config.yml`:**

````yaml
blank_issues_enabled: false
contact_links:
  - name: Guia de contribuição
    url: https://github.com/webminas/osint-brazuca/blob/main/CONTRIBUICAO.md
    about: Como editar o catálogo em catalogo/ e abrir um pull request, inclusive pelo navegador.
````

- [ ] **Passo 7: implementar. Criar `.github/PULL_REQUEST_TEMPLATE.md`:**

````markdown
<!-- Guia completo: CONTRIBUICAO.md. Edite só catalogo/<categoria>.yml: README.md e data/*.json são regenerados no main depois do merge. -->

## Tipo de mudança

- [ ] Nova fonte
- [ ] Correção de link
- [ ] Correção de fonte (nome, descrição, classificação, categoria, UF)
- [ ] Documentação
- [ ] Ferramentas (`tools/`, `tests/`, CI)

## Descrição

<!-- O que muda e por quê. Cite os ids das fontes (categoria/nome-da-fonte) e a issue, se houver: "Fecha #12". -->

## Checklist

- [ ] Editei só arquivos de `catalogo/` (ou documentação e ferramentas, se for o caso).
- [ ] Não editei `README.md`, `data/sources.json` nem `data/index.json` à mão.
- [ ] Testei no navegador todos os links novos ou alterados.
- [ ] Procurei a URL em `catalogo/` e a fonte não está repetida.
- [ ] Fonte nova ou classificação revisada usa `classificacao: override`.
- [ ] A fonte é pública, legal, relevante para o Brasil e respeita a LGPD.
- [ ] Li o [guia de contribuição](https://github.com/webminas/osint-brazuca/blob/main/CONTRIBUICAO.md).
````

- [ ] **Passo 8: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 133 tests` e `OK`.

- [ ] **Passo 9: commit.**

````bash
git add .github/ISSUE_TEMPLATE .github/PULL_REQUEST_TEMPLATE.md tests/test_modelos.py
git commit -m "Adiciona formulários de issue e modelo de pull request para o catálogo em YAML" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 10: guia de contribuição, README.en.md e rodapé do README

**Arquivos:**
- Modificar (substituir por inteiro): `CONTRIBUICAO.md`, `tests/test_documentacao.py`
- Modificar: `README.en.md`, `tools/readme/rodape.md`
- Regenerar: `README.md`

**Interfaces:**
- Consome: mensagens das Tarefas 2 a 6, formulários da Tarefa 9, `carrega_catalogo`.
- Produz: guia com âncoras `abrir-issue`, `editar-navegador`, `formato-fonte`, `erros-comuns`, `trabalhar-localmente`, `depois-do-merge`, `mantenedores` e `dataset-json`; a seção "Para mantenedores" traz os comandos de regeneração e commit no `main` (ADR 0002).

- [ ] **Passo 1: escrever o teste que falha. Substituir o conteúdo de `tests/test_documentacao.py`:**

````python
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(RAIZ / "tools"))

from apoio import cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402
from esquema import valida  # noqa: E402
from yaml_linhas import le_yaml  # noqa: E402


def le(relativo):
    return (RAIZ / relativo).read_text(encoding="utf-8")


class TestContribuicao(unittest.TestCase):
    def setUp(self):
        self.texto = le("CONTRIBUICAO.md")

    def test_fontes_ficam_em_catalogo_e_gerados_nao_entram_no_pr(self):
        self.assertIn("As fontes do catálogo ficam em `catalogo/<categoria>.yml`", self.texto)
        self.assertIn("são gerados a partir desses arquivos: não os edite à mão e não os inclua no pull request", self.texto)
        self.assertIn("os arquivos gerados são regenerados no `main` depois do merge", self.texto)
        self.assertIn("Depois do merge, o mantenedor os regenera no `main`.", self.texto)
        self.assertIn('git commit -m "Regenera README.md e dataset a partir de catalogo/"', self.texto)
        self.assertIn("Arquivos gerados em dia no main", self.texto)
        for antigo in ("Inclua esses arquivos no commit", "incluí os arquivos gerados", "overrides", "assinado pelo GitHub",
                       "Discussion", "git add .", "### Nome da", "<summary>Links de pesquisa</summary>"):
            self.assertNotIn(antigo, self.texto)

    def test_secoes_com_ancoras_estaveis(self):
        for ancora in ("abrir-issue", "editar-navegador", "formato-fonte", "erros-comuns",
                       "trabalhar-localmente", "depois-do-merge", "mantenedores", "dataset-json"):
            self.assertIn(f'<a name="{ancora}"></a>', self.texto)

    def test_aponta_os_tres_formularios(self):
        for nome in ("nova-fonte.yml", "link-quebrado.yml", "correcao.yml"):
            self.assertIn(f"issues/new?template={nome}", self.texto)
            self.assertTrue((RAIZ / ".github" / "ISSUE_TEMPLATE" / nome).exists())

    def test_tabela_de_campos_cobre_o_schema(self):
        esquema = json.loads(le("data/schemas/catalogo.schema.json"))
        campos = esquema["properties"]["fontes"]["items"]["properties"]
        for campo in campos:
            self.assertIn(f"| `{campo}` |", self.texto)

    def test_exemplo_de_fonte_e_valido_no_catalogo(self):
        bloco = re.search(r"```yaml\n(.*?)```", self.texto, re.S).group(1)
        dados, _, erros = le_yaml("fontes:\n" + bloco, "CONTRIBUICAO.md")
        self.assertEqual(erros, [])
        esquema = json.loads(le("data/schemas/catalogo.schema.json"))
        self.assertEqual(valida(dados, esquema), [])
        manifesto = ("categorias:\n  - id: consulta-de-processos\n    titulo: Processos\n"
                     "    ancora: processos\n    sumario: Processos\n")
        with tempfile.TemporaryDirectory() as tmp:
            raiz = cria_repo(tmp, {"catalogo/_categorias.yml": manifesto, "catalogo/alfa.yml": None,
                                   "catalogo/beta.yml": None,
                                   "catalogo/consulta-de-processos.yml": "fontes:\n" + bloco})
            self.assertEqual(carrega_catalogo(raiz)[1], [])

    def test_mensagens_da_tabela_de_erros_existem_nas_ferramentas(self):
        ferramentas = "".join(le(f"tools/{nome}") for nome in ("catalogo_io.py", "esquema.py", "yaml_linhas.py", "build_dataset.py"))
        ferramentas += le("data/schemas/catalogo.schema.json")
        for trecho in ("você quis dizer", "campo obrigatório", "a URL precisa começar com http:// ou https://",
                       "o nome do arquivo da categoria", "lista vazia em fonte com classificacao override",
                       "difere do gerado a partir de catalogo/", "texto com ': ' precisa ficar entre aspas simples",
                       "alinhe a linha com os campos vizinhos"):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, self.texto)
                self.assertTrue(trecho in ferramentas, f"{trecho!r} não aparece nas ferramentas")


class TestOutrosDocumentos(unittest.TestCase):
    def test_readme_gerado_aponta_catalogo_e_o_guia(self):
        readme = le("README.md")
        self.assertTrue(readme.startswith("<!-- ARQUIVO GERADO por tools/build_dataset.py a partir de catalogo/."))
        self.assertNotIn("overrides.json", readme)
        self.assertIn("Correções de classificação vão no arquivo da categoria em `catalogo/`.", readme)
        self.assertIn("veja o [guia de contribuição](CONTRIBUICAO.md)", le("tools/readme/rodape.md"))
        self.assertIn("CONTRIBUICAO.md#dataset-json", le("tools/readme/cabecalho.md"))

    def test_readme_en_descreve_o_fluxo_novo(self):
        texto = le("README.en.md")
        self.assertIn("the maintainers regenerate those files on `main` after the merge", texto)
        self.assertIn("issues/new/choose", texto)
        self.assertNotIn("commit README.md, `data/sources.json` and `data/index.json` together", texto)

    def test_modelos_do_dataset_indicam_catalogo(self):
        for nome in ("sources.schema.json", "index.schema.json"):
            self.assertEqual(json.loads(le(f"data/schemas/{nome}"))["fonte"], "catalogo/")


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_documentacao.py
````

Esperado: `FAILED`, com o guia antigo sem as âncoras novas e com "Inclua esses arquivos no commit".

- [ ] **Passo 3: implementar. Substituir o conteúdo de `CONTRIBUICAO.md`:**

````markdown
# 🤝 Como Contribuir com o OSINT Brazuca

<p align="center">
  <a href="README.md"><img alt="README Principal" src="https://img.shields.io/badge/%F0%9F%8F%A0%20README%20Principal-1E88E5?style=flat-square"></a>
  <a href="README.en.md"><img alt="English" src="https://img.shields.io/badge/%F0%9F%8C%8E%20English-37474F?style=flat-square"></a>
  <a href="EXEMPLOS_PRATICOS.md"><img alt="Exemplos Práticos" src="https://img.shields.io/badge/%F0%9F%93%96%20Exemplos%20Pr%C3%A1ticos-2E7D32?style=flat-square"></a>
  <a href="FLUXOGRAMA.md"><img alt="Fluxogramas" src="https://img.shields.io/badge/%F0%9F%94%80%20Fluxogramas-6A1B9A?style=flat-square"></a>
  <a href="GUIA_RAPIDO.md"><img alt="Guia Rápido" src="https://img.shields.io/badge/%F0%9F%93%8A%20Guia%20R%C3%A1pido-EF6C00?style=flat-square"></a>
  <a href="CONTRIBUICAO.md"><img alt="Contribuir" src="https://img.shields.io/badge/%F0%9F%A4%9D%20Contribuir-00838F?style=flat-square"></a>
  <a href="data/"><img alt="Dataset" src="https://img.shields.io/badge/%F0%9F%97%82%EF%B8%8F%20Dataset-F9A825?style=flat-square"></a>
  <a href="tools/"><img alt="Ferramentas" src="https://img.shields.io/badge/%F0%9F%9B%A0%EF%B8%8F%20Ferramentas-546E7A?style=flat-square"></a>
</p>

Obrigado por considerar contribuir com o OSINT Brazuca! Há três jeitos de ajudar, do mais simples ao mais completo:

1. **[Abrir uma issue](#abrir-issue)** com um formulário: sem git e sem editar arquivo.
2. **[Editar o catálogo pelo navegador](#editar-navegador)**: altere um arquivo de `catalogo/` no GitHub e abra um pull request.
3. **[Trabalhar localmente](#trabalhar-localmente)**: clone o repositório, rode as verificações e mande o pull request.

> [!IMPORTANT]
> As fontes do catálogo ficam em `catalogo/<categoria>.yml`. O `README.md`, o `data/sources.json` e o `data/index.json` são gerados a partir desses arquivos: não os edite à mão e não os inclua no pull request. Depois do merge, o mantenedor os regenera no `main`.

---

## 📝 Abrir uma issue <a name="abrir-issue"></a>

Escolha o formulário em [Issues > New issue](https://github.com/webminas/osint-brazuca/issues/new/choose):

| Formulário | Quando usar |
|---|---|
| [Sugerir nova fonte](https://github.com/webminas/osint-brazuca/issues/new?template=nova-fonte.yml) | Uma fonte pública brasileira que ainda não está no catálogo. |
| [Reportar link quebrado](https://github.com/webminas/osint-brazuca/issues/new?template=link-quebrado.yml) | Um link não abre, mudou de endereço ou leva a outra página. |
| [Corrigir uma fonte](https://github.com/webminas/osint-brazuca/issues/new?template=correcao.yml) | Nome, descrição, classificação, categoria ou UF errados, ou fonte repetida. |

> [!TIP]
> Sites `.gov.br` costumam bloquear robôs. Antes de reportar um link quebrado, confira no navegador.

---

## 🌐 Editar o catálogo pelo navegador <a name="editar-navegador"></a>

Não precisa instalar nada nem rodar nenhum comando.

1. Abra a pasta [`catalogo/`](catalogo/) e o arquivo da categoria. O nome do arquivo é o id da categoria; o manifesto [`catalogo/_categorias.yml`](catalogo/_categorias.yml) lista todas, na ordem do README.
2. Clique no lápis (**Edit this file**). O GitHub cria um fork seu se for preciso.
3. Acrescente ou corrija a fonte seguindo o [formato de uma fonte](#formato-fonte). Uma fonte nova entra no ponto da lista onde deve aparecer no README.
4. Clique em **Commit changes...** e depois em **Propose changes**.
5. Preencha o modelo do pull request. O CI valida o catálogo em cerca de um minuto; se algo falhar, abra o detalhe da verificação e leia a mensagem, que aponta arquivo e linha (veja [Erros comuns](#erros-comuns)).

Você não precisa regenerar o `README.md` nem o dataset: os arquivos gerados são regenerados no `main` depois do merge.

---

## 🧩 Formato de uma fonte <a name="formato-fonte"></a>

Cada fonte é um item da lista `fontes:` do arquivo da categoria. Exemplo de uma fonte em `catalogo/consulta-de-processos.yml`:

```yaml
  - id: consulta-de-processos/exemplo-consulta-publica
    nome: Exemplo - Consulta Pública de Processos
    descricao: Consulta gratuita, sem cadastro, de processos pelo número ou pelo nome da parte.
    links:
      - url: https://exemplo.jus.br/consulta
        label: Portal nacional
      - url: https://sp.exemplo.jus.br/consulta
        label: Portal de São Paulo
        uf: SP
    input: [numero_processo, nome]
    output: [processo, partes]
    tipo_fonte: judiciario
    classificacao: override
```

A indentação conta: o hífen de cada fonte fica a 2 espaços da margem e os campos dela a 4, sempre com espaços (nunca tabulação). O formato completo está em [`data/schemas/catalogo.schema.json`](data/schemas/catalogo.schema.json).

| Campo | Obrigatório | O que é |
|---|---|---|
| `id` | sim | `categoria/nome-da-fonte`, em minúsculas, sem acento, com hífens. O prefixo é o nome do arquivo da categoria. Não muda quando o nome da fonte muda. |
| `nome` | sim | Título exibido no README. Separe órgão e serviço com hífen simples. |
| `descricao` | sim | O que a fonte permite consultar; diga se é gratuita e se exige cadastro. Pode ser `''`. |
| `links` | sim | Lista com ao menos um link. Cada link tem `url` (começa com `http://` ou `https://`) e, se quiser, `label` (rótulo) e `uf` (sigla do estado). |
| `input` | sim | O que a consulta pede, com termos de [`data/taxonomy.json`](data/taxonomy.json). Use `[nenhum]` quando a fonte é navegada ou baixada por inteiro. |
| `output` | sim | O que a fonte devolve, com termos de `data/taxonomy.json`. |
| `tipo_fonte` | sim | Quem mantém a fonte (`federal`, `estadual`, `municipal`, `judiciario`, `privado`...). |
| `classificacao` | sim | `override` em toda fonte nova. `heuristica` só existe em fontes herdadas da migração e ainda não revisadas; ao revisar a classificação de uma delas, troque para `override`. |
| `observacao` | não | Nota da curadoria (limites de uso, autenticação). |
| `resumo` | não | Recolhe os links num `<details>` com este título, como em `resumo: Links de pesquisa`. |
| `subsecao` | não | Abre um subtítulo `####` da categoria antes desta fonte. |
| `markdown` | não | Texto livre (exemplos de código, tabelas) exibido depois dos links. Os links citados nele levam `em_markdown: true` na lista `links`. |

Regras que o CI confere:

- Fonte com `classificacao: override` declara ao menos um termo em `input` e em `output`.
- Todo termo de `input`, `output` e `tipo_fonte` existe em `data/taxonomy.json`. Para criar um termo novo, acrescente-o lá, com a descrição, e no formulário `.github/ISSUE_TEMPLATE/nova-fonte.yml`, no mesmo pull request.
- Toda URL fica em `links`; URL solta em `descricao`, `resumo`, `observacao` ou `grupo` é erro.
- O `id` é único no catálogo inteiro.

### Quando usar aspas

Coloque o texto entre aspas simples quando ele contiver `: ` (dois-pontos seguido de espaço) ou começar com `[`, `{`, `*`, `&`, `!`, `@`, `%` ou crase. Para um apóstrofo dentro de aspas simples, escreva duas aspas:

```text
descricao: 'Consulta: CPF e CNPJ'
descricao: '[Beta] consulta gratuita'
descricao: 'Arquivo d''Ajuda do portal'
```

Um ` #` no meio de um texto sem aspas vira comentário e corta o resto da linha; use aspas nesse caso também.

### Erros comuns <a name="erros-comuns"></a>

Cada erro do CI começa com `arquivo:linha:` e, quando se refere a um campo, com o caminho dele (`fontes[3].links[0].url` é a URL do primeiro link da quarta fonte do arquivo). O CI mostra todos os erros de uma vez.

| Mensagem (trecho) | O que fazer |
|---|---|
| `YAML inválido: mapping values are not allowed ... Dica: texto com ': ' precisa ficar entre aspas simples` | Ponha o texto entre aspas simples ou corrija a indentação da linha. |
| `YAML inválido: did not find expected key ... alinhe a linha com os campos vizinhos` | A linha está mais ou menos indentada que as vizinhas, ou o texto começa com `[`. |
| `input 'cpff' fora da taxonomia (data/taxonomy.json); você quis dizer 'cpf'?` | Use o termo sugerido ou um termo da lista indicada. |
| `campo obrigatório 'nome' ausente` | Falta o campo na fonte apontada. |
| `a URL precisa começar com http:// ou https:// e não pode ter espaços` | Corrija a `url` do link. |
| `o id precisa começar com 'saude/', o nome do arquivo da categoria` | Ajuste o prefixo do `id` ao arquivo em que a fonte está. |
| `lista vazia em fonte com classificacao override` | Declare ao menos um termo em `input` ou `output`. |
| `README.md:120: difere do gerado a partir de catalogo/` | O pull request editou um arquivo gerado. Desfaça essa mudança e edite só `catalogo/`. |

---

## 💻 Trabalhar localmente <a name="trabalhar-localmente"></a>

1. Faça um fork, clone e crie uma branch:
   ```bash
   git clone https://github.com/SEU-USUARIO/osint-brazuca.git
   cd osint-brazuca
   git checkout -b adicionar-fonte-x
   ```
2. Instale a única dependência, com versão fixada, e ative o hook que roda as verificações antes de cada commit:
   ```bash
   python3 -m pip install -r requirements.txt
   git config core.hooksPath tools/hooks
   ```
3. Edite `catalogo/<categoria>.yml` e confira:
   ```bash
   python3 tools/build_dataset.py --check   # valida o catálogo e mostra todos os erros
   python3 tools/build_dataset.py           # opcional: regenera README.md e data/*.json para ver o resultado
   ```
4. Faça o commit só dos arquivos que você editou (`git add catalogo/`). Se regenerou os arquivos gerados para conferir, não precisa incluí-los; se incluir, eles precisam estar idênticos ao que o build gera.
5. Envie a branch e abra o pull request:
   ```bash
   git push origin adicionar-fonte-x
   ```

O hook confere o que está no índice do git (o que vai entrar no commit), não a pasta de trabalho. Mensagens de commit no imperativo: "Adiciona fonte X", "Corrige link de Y".

Para mudar ferramentas (`tools/`), rode também os testes:

```bash
python3 -m unittest discover -s tests
python3 tools/validar_docs.py
```

---

## 🔁 O que acontece depois do merge <a name="depois-do-merge"></a>

No pull request, a verificação "Catálogo válido e nenhum arquivo gerado editado à mão" pode avisar que os gerados estão desatualizados: é esperado e não bloqueia o merge.

Depois do merge, o workflow [`.github/workflows/validar-dataset.yml`](.github/workflows/validar-dataset.yml) valida o catálogo no `main`, e o job "Arquivos gerados em dia no main" fica vermelho enquanto `README.md`, `data/sources.json` e `data/index.json` não forem regenerados. Quem regenera é o mantenedor, como descrito a seguir.

### Para mantenedores <a name="mantenedores"></a>

Depois de mesclar um pull request que mude `catalogo/`, `data/taxonomy.json` ou `tools/readme/`, regenere os arquivos gerados num commit seu, assinado:

```bash
git switch main && git pull
python3 tools/build_dataset.py
git add README.md data/sources.json data/index.json
git commit -m "Regenera README.md e dataset a partir de catalogo/"
git push
```

Vários merges seguidos podem ser regenerados de uma vez. O job "Arquivos gerados em dia no main" volta a ficar verde no push desse commit.

---

## 🗂️ Dataset JSON <a name="dataset-json"></a>

As fontes do catálogo ficam em `catalogo/<categoria>.yml`, um arquivo YAML por categoria, com a classificação (`input`, `output`, `tipo_fonte`) declarada em cada fonte. O `README.md`, o `data/sources.json` e o `data/index.json` são gerados a partir desses arquivos: não os edite à mão.

| Arquivo | O que é |
|---|---|
| `catalogo/<categoria>.yml` | **Fonte de verdade, editada à mão.** Um arquivo por categoria, com as fontes, links e classificação. |
| `catalogo/_categorias.yml` | Manual. Ordem, título, emoji e âncora de cada categoria no README. |
| `data/taxonomy.json` | Manual. Termos permitidos de `input`, `output`, `tipo_fonte` e `classificacao`, com a descrição de cada um. |
| `data/sources.json` | **Gerado.** Uma entrada por fonte, com os links aninhados, identificada pelo `id`. |
| `data/index.json` | **Gerado.** Um registro por link, achatado para busca. |

```bash
python3 tools/build_dataset.py            # valida catalogo/ e regenera README.md e o dataset
python3 tools/build_dataset.py --check    # só verifica, sem gravar
python3 tools/build_dataset.py --report   # mostra estatísticas do catálogo
```

### Corrigindo a classificação de uma fonte

Edite `input`, `output` ou `tipo_fonte` na própria fonte, no arquivo da categoria, e marque `classificacao: override`. Trecho de `catalogo/apis-publicas-brasileiras.yml`:

```text
  - id: apis-publicas-brasileiras/receitaws-api-cnpj
    nome: ReceitaWS - API CNPJ
    input: [cnpj]
    output: [api_json, cnae, dados_cadastrais, endereco, situacao_cadastral, socios]
    tipo_fonte: privado
    classificacao: override
    observacao: Sem autenticação. Rate limit de 3 requisições por minuto.
```

### Ferramentas de curadoria (só local)

```bash
python3 tools/validar_docs.py --avisos   # URLs repetidas em mais de uma fonte e URLs em http://
python3 tools/checar_links.py            # testa todas as URLs do catálogo e resume ok/redirect/bloqueio/offline
python3 tools/checar_links.py --filtro detran --csv links.csv
```

Esses avisos não bloqueiam o commit: URL repetida pode ser legítima (a mesma consulta em duas categorias) e muitos sites só existem em `http://`. Em `checar_links.py`, `bloqueio` (401, 403, 405, 429 ou 503) costuma ser proteção contra robôs; confira no navegador antes de reportar.

---

## 📐 Padrões de Formatação

### Pontuação

Não use travessão em nenhum texto do projeto, nem nos arquivos de `catalogo/`. Prefira vírgula, dois-pontos, ponto final ou parênteses. Em nomes de fonte, separe com hífen simples: `IBAMA - Consulta de Autuações Ambientais`.

### Alertas

Para destaques nos documentos, use os alertas nativos do GitHub em vez de negrito com emoji. Os cinco tipos válidos são `NOTE`, `TIP`, `IMPORTANT`, `WARNING` e `CAUTION`:

```markdown
> [!WARNING]
> Respeite os limites de requisição das APIs públicas.
```

O marcador fica sozinho na primeira linha e todo o conteúdo seguinte é prefixado com `>`. Use com parcimônia.

### Menu de navegação

O menu no topo de cada documento é um bloco de badges centralizado, idêntico em todos os arquivos. Ao alterar um item, replique a mudança em todos os documentos; `tools/validar_docs.py` confere.

### Documentação e ferramentas

Correções de texto, exemplos práticos e ferramentas (scripts de consulta, validação de links) também são bem-vindos. Código precisa de instruções de uso, respeitar os limites das APIs e trazer avisos sobre a LGPD. As ferramentas do repositório usam só a biblioteca padrão do Python e o PyYAML.

---

## ✅ Checklist Antes de Submeter

- [ ] **Contexto brasileiro:** é relevante para o Brasil?
- [ ] **Links testados:** todos abrem no navegador?
- [ ] **Sem duplicata:** procurei a URL em `catalogo/`?
- [ ] **Categoria certa:** a fonte está no arquivo da seção certa e o `id` começa com o nome desse arquivo?
- [ ] **Classificação:** fonte nova com `classificacao: override` e termos da taxonomia?
- [ ] **Só o catálogo:** não editei `README.md` nem `data/*.json`?
- [ ] **Fonte pública:** é de acesso público e legal?

---

## 🚫 O Que NÃO Será Aceito

> [!CAUTION]
> Pull requests com qualquer um dos itens abaixo são recusados sem análise adicional.

- ❌ Links fora do contexto brasileiro
- ❌ Links fora do contexto proposto
- ❌ Links para fóruns de fraude ou exploits
- ❌ Bases vazadas ou dados pessoais expostos
- ❌ Conteúdo discriminatório
- ❌ Links afiliados ou spam
- ❌ Ferramentas pagas sem versão gratuita (exceto se oficial)

---

## 🏆 Reconhecimento

Todos os contribuidores ficam creditados no histórico do Git e na lista de contribuidores do GitHub, exibida na seção de **Contribuições** do README.

---

## 📞 Dúvidas?

1. **Leia a documentação:** README.md e GUIA_RAPIDO.md.
2. **Consulte as issues existentes:** alguém já teve a mesma dúvida?
3. **Abra uma issue:** escolha o formulário mais próximo do seu caso.

---

## 📜 Código de Conduta

Ao contribuir, você concorda em:

- ✅ Ser respeitoso com outros contribuidores
- ✅ Aceitar críticas construtivas
- ✅ Focar no melhor para a comunidade
- ✅ Demonstrar empatia com outros membros
- ✅ Respeitar diferentes pontos de vista

---

## 🎓 Primeiras Contribuições

Novo em contribuições open source? Bons primeiros passos:

- Reportar ou corrigir um link quebrado
- Melhorar a descrição de uma fonte
- Revisar a classificação de uma fonte `heuristica` e marcá-la como `override`
- Corrigir erros de digitação

Issues marcadas com `good first issue` são boas para começar.

---

<p align="center">
  <strong>Obrigado por contribuir com o OSINT Brazuca! 🇧🇷</strong><br>
  <sub>Juntos estamos construindo a maior base de conhecimento OSINT do Brasil</sub>
</p>
````

- [ ] **Passo 4: implementar. Em `README.en.md`, trocar:**

````markdown
The source of truth is `catalogo/<category>.yml`. README.md and `data/*.json` are generated files, never edit them by hand. To regenerate them after editing the catalog (Python 3 and PyYAML, install with `pip install -r requirements.txt`):
````

por:

````markdown
The source of truth is `catalogo/<category>.yml`. README.md and `data/*.json` are generated files: never edit them by hand. The maintainers regenerate them on `main` after each merge; to preview them locally (Python 3 and PyYAML):
````

- [ ] **Passo 5: implementar. Em `README.en.md`, trocar:**

````markdown
1. **Report broken links** by opening an issue titled `[LINK QUEBRADO] Source name` with the URL, the date you tested it and the error.
2. **Add new sources** as an entry in the matching `catalogo/<category>.yml` file (id, name, description, links, input, output, source type and classification; see [CONTRIBUICAO.md](CONTRIBUICAO.md)). Sources must be public, legal and relevant to Brazil.
3. **Regenerate the generated files** with `python3 tools/build_dataset.py` and commit README.md, `data/sources.json` and `data/index.json` together with your change.
4. **Run the checks** with `python3 tools/validar_docs.py`, or enable the pre-commit hook once with `git config core.hooksPath tools/hooks`.
````

por:

````markdown
1. **Open an issue** with one of the [issue forms](https://github.com/webminas/osint-brazuca/issues/new/choose): suggest a new source, report a broken link or correct a source. No git needed.
2. **Edit the catalog in your browser.** Open the matching `catalogo/<category>.yml` file on GitHub, click the pencil icon and add or fix the entry (id, name, description, links, input, output, source type and `classificacao: override`; see [CONTRIBUICAO.md](CONTRIBUICAO.md#formato-fonte)). Then propose the change as a pull request.
3. **Do not touch the generated files.** Leave README.md, `data/sources.json` and `data/index.json` out of your pull request: the CI checks the catalog and points to the file and line of any error, and the maintainers regenerate those files on `main` after the merge.
4. **Working locally?** Install the pinned dependency with `pip install -r requirements.txt`, enable the pre-commit hook once with `git config core.hooksPath tools/hooks` and run `python3 tools/build_dataset.py --check`.
````

- [ ] **Passo 6: implementar. Em `tools/readme/rodape.md`, trocar:**

````markdown
Contribuições de qualquer tipo são bem-vindas!
````

por:

````markdown
Contribuições de qualquer tipo são bem-vindas! Para sugerir uma fonte, reportar um link quebrado ou editar o catálogo pelo navegador, veja o [guia de contribuição](CONTRIBUICAO.md).
````

- [ ] **Passo 7: regenerar o README e rodar tudo.**

````bash
python3 tools/build_dataset.py
python3 -m unittest discover -s tests
python3 tools/build_dataset.py --check
python3 tools/validar_docs.py
````

Esperado: `escrito README.md`, `escrito data/sources.json` e `escrito data/index.json` (no diff, só o rodapé do `README.md` muda), `Ran 136 tests`, `OK`, `OK: catálogo válido e arquivos gerados atualizados.` e `OK: documentos seguem as regras de formatação.`

- [ ] **Passo 8: commit.**

````bash
git add CONTRIBUICAO.md README.en.md tools/readme/rodape.md README.md tests/test_documentacao.py
git commit -m "Reescreve o guia de contribuição para o catálogo em YAML" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 11: aposentar data/overrides.json

**Arquivos:**
- Remover (lista aprovada na spec, R15): `data/overrides.json` (45 KB, curadoria absorvida em `catalogo/` pela spec 001) e `data/schemas/overrides.schema.json` (schema desse arquivo).
- Modificar: `tools/migracao/migrar_readme.py`
- Teste: `tests/test_overrides_aposentado.py`

**Interfaces:**
- Consome: nada.
- Produz: repositório sem os dois arquivos; docstring da migração com o comando para reexecutá-la do commit `a4466fa^`.

- [ ] **Passo 1: escrever o teste que falha. Criar `tests/test_overrides_aposentado.py`:**

````python
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestOverridesAposentado(unittest.TestCase):
    def test_arquivos_de_overrides_sairam_do_repositorio(self):
        self.assertFalse((RAIZ / "data" / "overrides.json").exists())
        self.assertFalse((RAIZ / "data" / "schemas" / "overrides.schema.json").exists())

    def test_nenhum_documento_ou_ferramenta_ativa_cita_overrides(self):
        arquivos = list(RAIZ.glob("*.md")) + list((RAIZ / "data").rglob("*.json"))
        arquivos += list((RAIZ / "tools").glob("*.py")) + list((RAIZ / "tools" / "readme").glob("*.md"))
        arquivos += list((RAIZ / ".github").rglob("*.*"))
        for caminho in arquivos:
            with self.subTest(arquivo=caminho.relative_to(RAIZ).as_posix()):
                self.assertNotIn("overrides.json", caminho.read_text(encoding="utf-8"))

    def test_migracao_explica_como_reexecutar(self):
        texto = (RAIZ / "tools" / "migracao" / "migrar_readme.py").read_text(encoding="utf-8")
        self.assertIn("git worktree add ../antes-da-migracao a4466fa^", texto)


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Passo 2: rodar e ver falhar.**

````bash
python3 -m unittest discover -s tests -p test_overrides_aposentado.py
````

Esperado: `FAILED (failures=3)`.

- [ ] **Passo 3: remover os dois arquivos (só estes, conforme R15).**

````bash
git rm data/overrides.json data/schemas/overrides.schema.json
````

- [ ] **Passo 4: implementar. Em `tools/migracao/migrar_readme.py`, trocar:**

````python
para auditoria; depois da migração não deve ser rodado de novo.
````

por:

````python
para auditoria; depois da migração não deve ser rodado de novo. O
data/overrides.json saiu do repositório na spec 002; para reexecutar a
migração, use um checkout do commit anterior a ela:

    git worktree add ../antes-da-migracao a4466fa^
````

- [ ] **Passo 5: rodar e ver passar.**

````bash
python3 -m unittest discover -s tests
````

Esperado: `Ran 139 tests` e `OK`.

- [ ] **Passo 6: commit.**

````bash
git add tools/migracao/migrar_readme.py tests/test_overrides_aposentado.py
git commit -m "Remove data/overrides.json e seu schema, absorvidos pelo catálogo" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
````

---

## Tarefa 12: rótulos e verificação final dos critérios de aceite

**Arquivos:**
- Nenhum.

**Interfaces:**
- Consome: tudo das tarefas 1 a 11.
- Produz: rótulos no GitHub e a evidência dos critérios de aceite para a descrição do PR.

- [ ] **Passo 1: criar os rótulos usados pelos formulários (R20). Exige `gh` autenticado com permissão de administrador.**

````bash
gh label create "nova fonte" --repo webminas/osint-brazuca --color 2E7D32 --description "Sugestão de fonte para o catálogo"
gh label create "link quebrado" --repo webminas/osint-brazuca --color D73A4A --description "Link do catálogo que não abre ou mudou"
gh label create "correção" --repo webminas/osint-brazuca --color FBCA04 --description "Correção de dados de uma fonte"
gh label list --repo webminas/osint-brazuca | grep -E "^(nova fonte|link quebrado|correção)\s"
````

Esperado: três linhas, uma por rótulo.

- [ ] **Passo 2: suíte completa, `--check` e documentos (CA14).**

````bash
python3 -m unittest discover -s tests
python3 tools/build_dataset.py --check
python3 tools/validar_docs.py
````

Esperado: `Ran 139 tests`, `OK`, `OK: catálogo válido e arquivos gerados atualizados.` e `OK: documentos seguem as regras de formatação.`

- [ ] **Passo 3: totais inalterados (CA14).**

````bash
python3 tools/build_dataset.py --report
````

Esperado: `categorias .......... 40`, `fontes .............. 874`, `links ............... 2313` e `classificação: heurística 667 | override 207`.

- [ ] **Passo 4: gerar duas vezes seguidas não deixa diff (CA14).**

````bash
python3 tools/build_dataset.py >/dev/null
python3 tools/build_dataset.py >/dev/null
test -z "$(git status --porcelain)" && echo git-status-limpo
````

Esperado: `git-status-limpo`.

- [ ] **Passo 5: o modo de PR, de ponta a ponta, sobre o repositório real (CA1, CA2).**

````bash
cp catalogo/saude.yml /tmp/saude.yml.orig
python3 -c "import pathlib; p = pathlib.Path('catalogo/saude.yml'); p.write_text(p.read_text().replace(\"descricao: ''\", 'descricao: Editada pelo navegador.', 1))"
echo catalogo/saude.yml | python3 tools/build_dataset.py --check --alterados -; echo "saída $?"
printf 'catalogo/saude.yml\nREADME.md\n' | python3 tools/build_dataset.py --check --alterados -; echo "saída $?"
cp /tmp/saude.yml.orig catalogo/saude.yml && rm -f /tmp/saude.yml.orig
test -z "$(git status --porcelain)" && echo git-status-limpo
````

Esperado: o aviso `AVISO: desatualizados, regenerados no main depois do merge: README.md, data/sources.json, data/index.json`, `OK: catálogo válido e nenhum arquivo gerado editado à mão.` e `saída 0`; depois `README.md:<linha>: difere do gerado a partir de catalogo/` e `saída 1`; por fim `git-status-limpo`.

- [ ] **Passo 6: depois do merge do PR desta spec (CA15, manual).** Abra um PR de teste pelo navegador que mude só a descrição de uma fonte em `catalogo/`, confira que o CI do PR passa com o aviso e faça o merge. Confira que o job "Arquivos gerados em dia no main" fica vermelho; então regenere como mantenedor, conforme `CONTRIBUICAO.md#mantenedores`, e confira que ele volta a passar:

````bash
git switch main && git pull webminas main
python3 tools/build_dataset.py
git add README.md data/sources.json data/index.json
git commit -m "Regenera README.md e dataset a partir de catalogo/" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git push webminas main
gh run list --repo webminas/osint-brazuca --workflow validar-dataset.yml --limit 2
````

Esperado: a execução do merge com o job "Arquivos gerados em dia no main" em falha (anotação "Arquivos gerados desatualizados") e a execução do commit de regeneração com `success`. O commit de regeneração tem autor e committer Matheus Breguêz, assinado.
