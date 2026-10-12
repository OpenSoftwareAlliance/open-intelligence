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
