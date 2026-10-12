import os
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOW = RAIZ / ".github" / "workflows" / "validar-dataset.yml"
HOOK = RAIZ / "tools" / "hooks" / "pre-commit"


class TestCI(unittest.TestCase):
    def test_workflow_instala_dependencia_fixada_e_roda_verificacoes(self):
        texto = WORKFLOW.read_text(encoding="utf-8")
        for passo in ("python3 -m pip install -r requirements.txt",
                      "python3 -m unittest discover -s tests -v",
                      "python3 tools/build_dataset.py --check",
                      "python3 tools/validar_docs.py"):
            self.assertIn(f"run: {passo}", texto)
        self.assertEqual(texto.count('"catalogo/**"'), 2)
        self.assertEqual(texto.count('"requirements.txt"'), 2)
        self.assertNotIn("--report", texto)

    def test_hook_valida_catalogo_e_e_executavel(self):
        texto = HOOK.read_text(encoding="utf-8")
        self.assertIn("python3 tools/build_dataset.py --check", texto)
        self.assertIn("git diff --cached --quiet -- catalogo README.md data tools requirements.txt", texto)
        self.assertNotIn("overrides.json", texto)
        self.assertTrue(os.access(HOOK, os.X_OK))
        modo = subprocess.run(["git", "ls-files", "-s", "tools/hooks/pre-commit"], cwd=RAIZ,
                              capture_output=True, text=True, check=True).stdout.split()[0]
        self.assertEqual(modo, "100755")

    def test_requirements_fixa_so_o_pyyaml(self):
        linhas = [l for l in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
        self.assertEqual(linhas, ["PyYAML==6.0.3"])


if __name__ == "__main__":
    unittest.main()
