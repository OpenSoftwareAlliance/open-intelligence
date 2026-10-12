import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import ALFA, BETA, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402


def carrega(arquivos):
    with tempfile.TemporaryDirectory() as tmp:
        return carrega_catalogo(cria_repo(tmp, arquivos))[1]


class TestErrosNumaRodada(unittest.TestCase):
    def test_erro_de_formato_numa_fonte_nao_esconde_taxonomia_de_outra(self):
        texto = (ALFA.replace("    descricao: Descrição da primeira.\n", "    descricao: Descrição da primeira.\n    cor: azul\n")
                 .replace("input: [nome]", "input: [nomes]"))
        self.assertEqual(carrega({"catalogo/alfa.yml": texto}), [
            "catalogo/alfa.yml:5: fontes[0].cor: campo 'cor' não permitido",
            "catalogo/alfa.yml:24: fontes[1].input[0]: input 'nomes' fora da taxonomia (data/taxonomy.json); você quis dizer 'nome' ou 'cnes'?",
        ])

    def test_campo_ausente_e_termo_errado_na_mesma_fonte(self):
        texto = BETA.replace("    nome: Terceira Fonte\n", "").replace("output: [dataset]", "output: [datset]")
        self.assertEqual(carrega({"catalogo/beta.yml": texto}), [
            "catalogo/beta.yml:2: fontes[0]: campo obrigatório 'nome' ausente",
            "catalogo/beta.yml:7: fontes[0].output[0]: output 'datset' fora da taxonomia (data/taxonomy.json); você quis dizer 'dataset'?",
        ])

    def test_url_invalida_e_tipo_fonte_errado_na_mesma_fonte(self):
        texto = BETA.replace("https://terceira.org.br/", "terceira.org.br").replace("tipo_fonte: ong", "tipo_fonte: ongs")
        erros = carrega({"catalogo/beta.yml": texto})
        self.assertEqual(len(erros), 2, erros)
        self.assertTrue(erros[0].startswith("catalogo/beta.yml:6: fontes[0].links[0].url: "), erros[0])
        self.assertTrue(erros[1].startswith("catalogo/beta.yml:9: fontes[0].tipo_fonte: tipo_fonte 'ongs'"), erros[1])

    def test_id_repetido_aparece_junto_com_erro_de_formato(self):
        texto = ALFA.replace("alfa/segunda-fonte", "alfa/primeira-fonte").replace("    nome: Segunda Fonte\n", "")
        self.assertEqual(carrega({"catalogo/alfa.yml": texto}), [
            "catalogo/alfa.yml:11: fontes[1]: campo obrigatório 'nome' ausente",
            "catalogo/alfa.yml:11: fontes[1].id: id 'alfa/primeira-fonte' repetido; já usado em catalogo/alfa.yml:2",
        ])

    def test_arquivo_sem_lista_de_fontes_para_ali(self):
        self.assertEqual(carrega({"catalogo/beta.yml": "fontes: nenhuma\n"}),
                         ["catalogo/beta.yml:1: fontes: tipo string, esperado array"])


if __name__ == "__main__":
    unittest.main()
