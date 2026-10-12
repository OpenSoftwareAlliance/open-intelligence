import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from validar_docs import DOCS, checa_travessao  # noqa: E402

TRAVESSAO = "—"


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
