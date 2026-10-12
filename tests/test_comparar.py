import copy
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools" / "migracao"))

from comparar import compara, ordem_esperada  # noqa: E402


def fonte(ident, categoria, url, classificacao="heuristica"):
    return {"id": ident, "categoria_id": categoria, "classificacao": classificacao,
            "links": [{"label": "", "uf": None, "url": url}]}


def link(ident, categoria, url):
    return {"fonte_id": ident, "categoria_id": categoria, "url": url}


# "outras" aparece em duas seções no README antigo: a fonte o/2 vem depois de b/1.
FONTES = [fonte("o/1", "outras", "https://o1.gov.br/"), fonte("b/1", "beta", "https://b1.gov.br/", "override"),
          fonte("o/2", "outras", "https://o2.gov.br/")]
LINKS = [link("o/1", "outras", "https://o1.gov.br/"), link("b/1", "beta", "https://b1.gov.br/"),
         link("o/2", "outras", "https://o2.gov.br/")]
README_ANTES = ('## Outras <a name="outras"></a>\n- https://o1.gov.br/\n## Beta <a name="beta"></a>\n'
                '- https://b1.gov.br/\n## Outras <a name="outras"></a>\n- https://o2.gov.br/\n')
README_DEPOIS = ('## Outras <a name="outras"></a>\n- https://o1.gov.br/\n- https://o2.gov.br/\n'
                 '## Beta <a name="beta"></a>\n- https://b1.gov.br/\n')


def estado(fontes, links, readme, sobre="x", outros=None):
    base = {
        "README.md": readme,
        "data/sources.json": json.dumps({"_sobre": sobre, "fonte": sobre, "total": len(fontes), "sources": fontes}),
        "data/index.json": json.dumps({"_sobre": sobre, "fonte": sobre, "total": len(links), "links": links}),
    }
    base.update(outros or {})
    return base


DEPOIS_OK = estado([FONTES[0], FONTES[2], FONTES[1]], [LINKS[0], LINKS[2], LINKS[1]], README_DEPOIS, sobre="novo")


class TestCompara(unittest.TestCase):
    def test_ordem_esperada_agrupa_na_primeira_secao(self):
        self.assertEqual([f["id"] for f in ordem_esperada(FONTES, "categoria_id")], ["o/1", "o/2", "b/1"])

    def test_migracao_fiel_passa(self):
        erros, resumo = compara(estado(FONTES, LINKS, README_ANTES), DEPOIS_OK, ["beta", "outras"])
        self.assertEqual(erros, [])
        self.assertIn("CA3 fontes: 3 | links: 3 | heuristica: 2 | override: 1 | ids iguais: True", resumo)

    def test_descricao_reduzida_ao_inicio_passa_mas_texto_diferente_falha(self):
        antes_fontes = copy.deepcopy(FONTES)
        antes_fontes[0]["descricao"] = "Preencha assim: 1. um; 2. dois"
        depois_fontes = copy.deepcopy([FONTES[0], FONTES[2], FONTES[1]])
        depois_fontes[0]["descricao"] = "Preencha assim:"
        depois_links = [LINKS[0], LINKS[2], LINKS[1]]
        antes = estado(antes_fontes, LINKS, README_ANTES)
        erros, _ = compara(antes, estado(depois_fontes, depois_links, README_DEPOIS), ["outras", "beta"])
        self.assertEqual(erros, [])
        depois_fontes[0]["descricao"] = "Outro texto"
        erros, _ = compara(antes, estado(depois_fontes, depois_links, README_DEPOIS), ["outras", "beta"])
        self.assertTrue(any("CA2" in e for e in erros))

    def test_link_alterado_falha_ca2_e_ca4(self):
        depois = copy.deepcopy(DEPOIS_OK)
        depois["README.md"] = depois["README.md"].replace("o2.gov.br", "o3.gov.br")
        fontes = json.loads(depois["data/sources.json"])
        fontes["sources"][1]["links"][0]["url"] = "https://o3.gov.br/"
        depois["data/sources.json"] = json.dumps(fontes)
        erros, _ = compara(estado(FONTES, LINKS, README_ANTES), depois, ["beta", "outras"])
        self.assertTrue(any(e.startswith("CA2 sources.json: sources[1] difere: o/2") for e in erros), erros)
        self.assertTrue(any(e.startswith("CA4:") for e in erros), erros)

    def test_categoria_sem_arquivo_falha_ca1(self):
        erros, _ = compara(estado(FONTES, LINKS, README_ANTES), DEPOIS_OK, ["beta"])
        self.assertEqual(erros, ["CA1: arquivos de categoria ['outras'] não batem com categoria_id"])

    def test_ancora_perdida_e_link_externo_quebrado_falham_ca5(self):
        outros = {"GUIA_RAPIDO.md": "[Beta](README.md#beta) e [Velho](README.md#nao-existia)"}
        depois = dict(DEPOIS_OK)
        depois["README.md"] = README_DEPOIS.replace('## Beta <a name="beta"></a>', "## Bravo")
        erros, resumo = compara(estado(FONTES, LINKS, README_ANTES, outros=outros), depois, ["beta", "outras"])
        self.assertIn("CA5: âncoras <a name> sumiram: ['beta']", erros)
        self.assertIn("CA5: GUIA_RAPIDO.md -> README.md#beta deixou de resolver", erros)
        self.assertTrue(resumo[-1].endswith("links de outros documentos já quebrados antes: 1"), resumo[-1])


if __name__ == "__main__":
    unittest.main()
