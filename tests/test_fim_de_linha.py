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
