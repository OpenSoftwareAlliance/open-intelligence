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
