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
        self.assertIn('git commit -S -m "Regenera README.md e dataset a partir de catalogo/"', self.texto)
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
