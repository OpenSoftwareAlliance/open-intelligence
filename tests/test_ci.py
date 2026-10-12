import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOW = RAIZ / ".github" / "workflows" / "validar-dataset.yml"


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

    def test_requirements_fixa_so_o_pyyaml(self):
        linhas = [l for l in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
        self.assertEqual(linhas, ["PyYAML==6.0.3"])


if __name__ == "__main__":
    unittest.main()
