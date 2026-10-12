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
from readme_gerado import AVISO, VOLTAR  # noqa: E402

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

    def test_segunda_execucao_recusa_e_nao_escreve(self):
        raiz = cria(README)
        try:
            self.assertEqual(roda(raiz)[0], 0)
            antes = {c: c.read_bytes() for c in raiz.rglob("*") if c.is_file()}
            codigo, _, erro = roda(raiz)
            depois = {c: c.read_bytes() for c in raiz.rglob("*") if c.is_file()}
            self.assertEqual(codigo, 1)
            self.assertIn("ERRO: catalogo/_categorias.yml já existe", erro)
            self.assertIn("--forcar", erro)
            self.assertEqual(antes, depois)
        finally:
            shutil.rmtree(raiz)

    def test_readme_gerado_e_recusado(self):
        raiz = cria(AVISO + "\n" + README)
        try:
            codigo, _, erro = roda(raiz)
        finally:
            shutil.rmtree(raiz)
        self.assertEqual(codigo, 1)
        self.assertIn("README.md já é gerado", erro)


if __name__ == "__main__":
    unittest.main()
