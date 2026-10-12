import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestOverridesAposentado(unittest.TestCase):
    def test_arquivos_de_overrides_sairam_do_repositorio(self):
        self.assertFalse((RAIZ / "data" / "overrides.json").exists())
        self.assertFalse((RAIZ / "data" / "schemas" / "overrides.schema.json").exists())

    def test_nenhum_documento_ou_ferramenta_ativa_cita_overrides(self):
        arquivos = list(RAIZ.glob("*.md")) + list((RAIZ / "data").rglob("*.json"))
        arquivos += list((RAIZ / "tools").glob("*.py")) + list((RAIZ / "tools" / "readme").glob("*.md"))
        arquivos += list((RAIZ / ".github").rglob("*.*"))
        for caminho in arquivos:
            with self.subTest(arquivo=caminho.relative_to(RAIZ).as_posix()):
                self.assertNotIn("overrides.json", caminho.read_text(encoding="utf-8"))

    def test_migracao_explica_como_reexecutar(self):
        texto = (RAIZ / "tools" / "migracao" / "migrar_readme.py").read_text(encoding="utf-8")
        self.assertIn("git worktree add ../antes-da-migracao a4466fa^", texto)


if __name__ == "__main__":
    unittest.main()
