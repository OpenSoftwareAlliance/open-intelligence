import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import CABECALHO, RODAPE, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402
from readme_gerado import AVISO, VOLTAR, gera_readme, renderiza_fonte, renderiza_link  # noqa: E402

ESPERADO = f"""{AVISO}
# Cabeçalho de teste

---
# Sumário

- [Alfa](#alfa)
- [Beta](#beta)
- [Autores](#autores)
- [Contribuições](#contribuicoes)
- [Créditos](#creditos)

---

## Alfa 🅰️ <a name="alfa"></a>

Introdução da categoria alfa.

### Primeira Fonte

Descrição da primeira.

- https://primeira.gov.br/

#### Subgrupo

### Segunda Fonte

<details>
<summary>Links de pesquisa</summary>

- Portal: https://segunda.sp.gov.br/

**Rio de Janeiro (RJ)**
- https://segunda.rj.gov.br/

</details>

```bash
curl https://segunda.sp.gov.br/api
```

{VOLTAR}

---

## Beta (Teste) <a name="beta"></a>

### Terceira Fonte

Descrição da terceira.

- https://terceira.org.br/

{VOLTAR}

---

## Créditos <a name="creditos"></a>

Obrigado.
"""


class TestGeraReadme(unittest.TestCase):
    def test_readme_completo_do_catalogo_de_teste(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalogo, erros = carrega_catalogo(cria_repo(tmp))
        self.assertEqual(erros, [])
        self.maxDiff = None
        self.assertEqual(gera_readme(catalogo, CABECALHO, RODAPE), ESPERADO)

    def test_readme_comeca_com_aviso_de_arquivo_gerado(self):
        self.assertTrue(AVISO.startswith("<!-- ARQUIVO GERADO por tools/build_dataset.py"))
        self.assertIn("python3 tools/build_dataset.py -->", AVISO)

    def test_links_em_markdown_nao_se_repetem_na_lista(self):
        fonte = {
            "nome": "Dorks",
            "descricao": "Buscas prontas.",
            "resumo": "Links de pesquisa",
            "links": [{"url": "https://www.google.com/search?q=site%3Agov.br", "label": "site:gov.br", "em_markdown": True}],
            "markdown": "- `site:gov.br`\n  - https://www.google.com/search?q=site%3Agov.br",
        }
        self.assertEqual(renderiza_fonte(fonte), [
            "### Dorks", "", "Buscas prontas.", "",
            "- `site:gov.br`", "  - https://www.google.com/search?q=site%3Agov.br", "",
        ])

    def test_link_com_e_sem_label(self):
        self.assertEqual(renderiza_link({"url": "https://a.gov.br/"}), "- https://a.gov.br/")
        self.assertEqual(renderiza_link({"url": "https://a.gov.br/", "label": "Portal"}), "- Portal: https://a.gov.br/")


if __name__ == "__main__":
    unittest.main()
