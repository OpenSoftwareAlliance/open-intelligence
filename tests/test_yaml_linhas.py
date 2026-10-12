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

    def test_tag_yaml_no_valor_vira_erro_com_linha(self):
        dados, _, erros = le_yaml("fontes:\n  - id: a/b\n    descricao: !Novo portal\n", "catalogo/a.yml")
        self.assertEqual(len(erros), 1)
        self.assertTrue(erros[0].startswith("catalogo/a.yml:3: YAML inválido:"), erros[0])

    def test_chave_nao_escalar_vira_erro_com_linha(self):
        _, _, erros = le_yaml("fontes:\n  ? [a, b]\n  : 1\n", "catalogo/a.yml")
        self.assertEqual(len(erros), 1)
        self.assertTrue(erros[0].startswith("catalogo/a.yml:2: "), erros[0])

    def test_arquivo_vazio(self):
        self.assertEqual(le_yaml("", "catalogo/a.yml")[2], ["catalogo/a.yml:1: arquivo vazio"])

    def test_erro_em_formata_arquivo_linha_e_caminho(self):
        _, linhas, _ = le_yaml(TEXTO, "catalogo/alfa.yml")
        msg = erro_em("catalogo/alfa.yml", linhas, ("fontes", 0, "links", 1, "uf"), "UF inválida")
        self.assertEqual(msg, "catalogo/alfa.yml:7: fontes[0].links[1].uf: UF inválida")


if __name__ == "__main__":
    unittest.main()
