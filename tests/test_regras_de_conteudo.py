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
