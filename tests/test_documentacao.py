import json
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def le(relativo):
    return (RAIZ / relativo).read_text(encoding="utf-8")


class TestDocumentacao(unittest.TestCase):
    def test_contribuicao_explica_que_fontes_ficam_em_catalogo(self):
        texto = le("CONTRIBUICAO.md")
        self.assertIn("As fontes do catálogo ficam em `catalogo/<categoria>.yml`", texto)
        self.assertIn("são gerados a partir desses arquivos: não os edite à mão", texto)
        self.assertNotIn("O README é a fonte de verdade do catálogo", texto)
        self.assertNotIn("sem dependências", texto)
        self.assertNotIn('"overrides": {', texto)
        self.assertNotIn("corrija em `data/overrides.json`", texto)
        self.assertNotIn("Verifique se a fonte já não existe no README", texto)
        self.assertNotIn("se mexeu em fontes ou URLs do README", texto)

    def test_contribuicao_lista_o_readme_entre_os_gerados_e_a_validacao_real(self):
        texto = le("CONTRIBUICAO.md")
        self.assertIn("Isso atualiza `README.md`, `data/sources.json` e `data/index.json`. Inclua esses arquivos no commit.", texto)
        self.assertIn("e incluí os arquivos gerados (`README.md` e JSON)", texto)
        self.assertNotIn("(`--report`)", texto)
        self.assertNotIn("incluí os JSON atualizados", texto)
        self.assertIn("(`build_dataset.py --check`)", texto)
        self.assertIn("links obrigatórios", texto)

    def test_readme_gerado_aponta_catalogo_como_fonte(self):
        readme = le("README.md")
        self.assertTrue(readme.startswith("<!-- ARQUIVO GERADO por tools/build_dataset.py a partir de catalogo/."))
        self.assertNotIn("overrides.json", readme)
        self.assertNotIn("a partir deste README", readme)
        self.assertIn("Correções de classificação vão no arquivo da categoria em `catalogo/`.", readme)

    def test_modelos_do_dataset_indicam_catalogo(self):
        for nome in ("sources.schema.json", "index.schema.json"):
            self.assertEqual(json.loads(le(f"data/schemas/{nome}"))["fonte"], "catalogo/")


if __name__ == "__main__":
    unittest.main()
