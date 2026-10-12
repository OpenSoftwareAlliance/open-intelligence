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
            mock.patch("sys.stdin", io.TextIOWrapper(io.BytesIO(entrada.encode("utf-8")), encoding="utf-8")):
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

    def test_lista_vazia_na_entrada_e_erro(self):
        codigo, _, erro = roda(self.raiz, "--check", "--alterados", "-", entrada="\n  \n")
        self.assertEqual(codigo, 1)
        self.assertIn("ERRO: a lista de arquivos alterados está vazia", erro)

    def test_lista_vazia_em_arquivo_e_erro(self):
        lista = Path(self._tmp.name) / "vazia.txt"
        lista.write_text("", encoding="utf-8")
        codigo, _, erro = roda(self.raiz, "--check", "--alterados", str(lista))
        self.assertEqual(codigo, 1)
        self.assertIn("está vazia", erro)

    def test_alterados_vazio_sem_check_e_erro_de_uso(self):
        with self.assertRaises(SystemExit) as saida, contextlib.redirect_stderr(io.StringIO()):
            main(["--alterados", ""], raiz=self.raiz)
        self.assertEqual(saida.exception.code, 2)

    def test_aviso_cita_so_o_gerado_desatualizado_fora_da_lista(self):
        self.beta.write_text(BETA.replace("Descrição da terceira.", "Nova descrição."), encoding="utf-8")
        roda(self.raiz)
        (self.raiz / "data" / "index.json").write_text("{}\n", encoding="utf-8")
        lista = "catalogo/beta.yml\nREADME.md\n"
        codigo, saida, _ = roda(self.raiz, "--check", "--alterados", "-", entrada=lista)
        self.assertEqual(codigo, 0)
        self.assertIn("regenerados no main depois do merge: data/index.json\n", saida)
        self.assertNotIn("README.md,", saida)


if __name__ == "__main__":
    unittest.main()
