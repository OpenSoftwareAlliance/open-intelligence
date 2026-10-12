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
TRAVESSAO = "—"


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
