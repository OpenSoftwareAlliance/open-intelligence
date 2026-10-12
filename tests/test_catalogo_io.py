import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import ALFA, BETA, MANIFESTO, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402


class TestCarregaCatalogo(unittest.TestCase):
    def carrega(self, arquivos=None):
        with tempfile.TemporaryDirectory() as tmp:
            return carrega_catalogo(cria_repo(tmp, arquivos))

    def test_catalogo_valido(self):
        catalogo, erros = self.carrega()
        self.assertEqual(erros, [])
        self.assertEqual([c["id"] for c in catalogo["categorias"]], ["alfa", "beta"])
        self.assertEqual([f["id"] for f in catalogo["fontes"]["alfa"]], ["alfa/primeira-fonte", "alfa/segunda-fonte"])

    def test_termo_fora_da_taxonomia(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("input: [nenhum]", "input: [nenhum, cpff]")})
        self.assertEqual(erros, ["catalogo/beta.yml:7: fontes[0].input[1]: input 'cpff' fora da taxonomia (data/taxonomy.json)"])

    def test_tipo_fonte_fora_da_taxonomia(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("tipo_fonte: ong", "tipo_fonte: igreja")})
        self.assertEqual(erros, ["catalogo/beta.yml:9: fontes[0].tipo_fonte: tipo_fonte 'igreja' fora da taxonomia (data/taxonomy.json)"])

    def test_id_duplicado_entre_arquivos(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("beta/terceira-fonte", "alfa/primeira-fonte")})
        self.assertEqual(erros, ["catalogo/beta.yml:2: fontes[0].id: id 'alfa/primeira-fonte' repetido; já usado em catalogo/alfa.yml:2"])

    def test_fonte_sem_link(self):
        sem_link = BETA.replace("    links:\n      - url: https://terceira.org.br/\n", "    links: []\n")
        _, erros = self.carrega({"catalogo/beta.yml": sem_link})
        self.assertEqual(erros, ["catalogo/beta.yml:5: fontes[0].links: lista com 0 itens, mínimo 1"])

    def test_campo_obrigatorio_ausente(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("    nome: Terceira Fonte\n", "")})
        self.assertEqual(erros, ["catalogo/beta.yml:2: fontes[0]: campo obrigatório 'nome' ausente"])

    def test_categoria_fora_do_manifesto(self):
        _, erros = self.carrega({"catalogo/gama.yml": BETA.replace("beta/", "gama/")})
        self.assertEqual(erros, ["catalogo/gama.yml:1: categoria 'gama' fora do manifesto catalogo/_categorias.yml"])

    def test_categoria_do_manifesto_sem_arquivo(self):
        _, erros = self.carrega({"catalogo/beta.yml": None})
        self.assertEqual(erros, ["catalogo/_categorias.yml:9: categorias[1]: categoria 'beta' sem arquivo catalogo/beta.yml"])

    def test_ancora_repetida_no_manifesto(self):
        _, erros = self.carrega({"catalogo/_categorias.yml": MANIFESTO.replace("ancora: beta", "ancora: alfa")})
        self.assertEqual(erros, ["catalogo/_categorias.yml:11: categorias[1].ancora: ancora 'alfa' repetido; já usado na linha 5"])

    def test_arquivo_com_outra_extensao(self):
        _, erros = self.carrega({"catalogo/beta.yaml": BETA})
        self.assertEqual(erros, ["catalogo/beta.yaml:1: arquivo inesperado; o catálogo só aceita arquivos .yml"])

    def test_url_invalida_e_campo_desconhecido(self):
        texto = ALFA.replace("https://primeira.gov.br/", "primeira.gov.br").replace("        label: Portal\n", "        rotulo: Portal\n")
        _, erros = self.carrega({"catalogo/alfa.yml": texto})
        self.assertEqual(erros, [
            "catalogo/alfa.yml:6: fontes[0].links[0].url: valor 'primeira.gov.br' não segue o padrão ^https?://\\S+$",
            "catalogo/alfa.yml:18: fontes[1].links[0].rotulo: campo 'rotulo' não permitido",
        ])

    def test_link_em_markdown_precisa_aparecer_no_markdown(self):
        _, erros = self.carrega({"catalogo/alfa.yml": ALFA.replace("        uf: RJ\n", "        uf: RJ\n        em_markdown: true\n")})
        self.assertEqual(erros, ["catalogo/alfa.yml:23: fontes[1].links[1].em_markdown: link https://segunda.rj.gov.br/ "
                                 "marcado em_markdown, mas a URL não aparece no campo markdown"])

    def test_url_no_markdown_precisa_estar_em_links(self):
        _, erros = self.carrega({"catalogo/alfa.yml": ALFA.replace("      ```\n", "      ```\n\n      Veja https://outra.gov.br/\n")})
        self.assertEqual(erros, ["catalogo/alfa.yml:28: fontes[1].markdown: URL https://outra.gov.br/ no campo markdown "
                                 "sem link correspondente em links"])

    def test_yaml_quebrado_aponta_linha(self):
        _, erros = self.carrega({"catalogo/beta.yml": BETA.replace("    nome: Terceira", "   nome: Terceira")})
        self.assertEqual(len(erros), 1)
        self.assertTrue(erros[0].startswith("catalogo/beta.yml:3: YAML inválido"), erros[0])


if __name__ == "__main__":
    unittest.main()
