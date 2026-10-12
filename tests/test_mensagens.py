import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from apoio import ALFA, BETA, cria_repo  # noqa: E402
from catalogo_io import carrega_catalogo  # noqa: E402
from esquema import valida  # noqa: E402

TIPOS_FONTE = ("academico, api, defensoria, dork, estadual, federal, indefinido, internacional, "
               "judiciario, legislativo, ministerio_publico, municipal, ong, privado")


def carrega(arquivos):
    with tempfile.TemporaryDirectory() as tmp:
        return carrega_catalogo(cria_repo(tmp, arquivos))[1]


class TestMensagensDoEsquema(unittest.TestCase):
    def test_enum_lista_os_valores_aceitos(self):
        erros = valida("XX", {"enum": ["SP", "RJ"]})
        self.assertEqual(erros, [((), "valor 'XX' fora da lista permitida: SP, RJ")])

    def test_padrao_com_mensagem_propria(self):
        esquema = {"type": "string", "pattern": "^https?://", "x-mensagem": "a URL precisa começar com https://"}
        self.assertEqual(valida("ftp://a", esquema), [((), "valor 'ftp://a': a URL precisa começar com https://")])

    def test_padrao_sem_mensagem_propria_mostra_a_expressao(self):
        erros = valida("ftp://a", {"type": "string", "pattern": "^https?://"})
        self.assertEqual(erros, [((), "valor 'ftp://a' não segue o padrão ^https?://")])


class TestMensagensDoCatalogo(unittest.TestCase):
    def test_termo_parecido_ganha_sugestao(self):
        erros = carrega({"catalogo/beta.yml": BETA.replace("input: [nenhum]", "input: [placas]")})
        self.assertEqual(erros, ["catalogo/beta.yml:7: fontes[0].input[0]: input 'placas' fora da taxonomia "
                                 "(data/taxonomy.json); você quis dizer 'placa'?"])

    def test_eixo_curto_sem_termo_parecido_lista_os_termos(self):
        erros = carrega({"catalogo/beta.yml": BETA.replace("tipo_fonte: ong", "tipo_fonte: igreja")})
        self.assertEqual(erros, ["catalogo/beta.yml:9: fontes[0].tipo_fonte: tipo_fonte 'igreja' fora da taxonomia "
                                 f"(data/taxonomy.json); termos aceitos: {TIPOS_FONTE}"])

    def test_eixo_longo_sem_termo_parecido_aponta_a_taxonomia(self):
        erros = carrega({"catalogo/beta.yml": BETA.replace("output: [dataset]", "output: [telefone]")})
        self.assertEqual(erros, ["catalogo/beta.yml:8: fontes[0].output[0]: output 'telefone' fora da taxonomia "
                                 "(data/taxonomy.json); veja os termos aceitos na seção output de data/taxonomy.json"])

    def test_uf_invalida_lista_as_siglas(self):
        erros = carrega({"catalogo/alfa.yml": ALFA.replace("uf: SP", "uf: Sp")})
        self.assertEqual(len(erros), 1, erros)
        self.assertIn("fontes[1].links[0].uf: valor 'Sp' fora da lista permitida: AC, AL, AP, AM,", erros[0])

    def test_url_e_id_invalidos_explicam_o_formato(self):
        texto = ALFA.replace("https://primeira.gov.br/", "primeira.gov.br").replace("alfa/primeira-fonte", "alfa/Primeira Fonte")
        self.assertEqual(carrega({"catalogo/alfa.yml": texto}), [
            "catalogo/alfa.yml:2: fontes[0].id: valor 'alfa/Primeira Fonte': o id tem o formato categoria/nome-da-fonte, "
            "só com letras minúsculas sem acento, números e hífens",
            "catalogo/alfa.yml:6: fontes[0].links[0].url: valor 'primeira.gov.br': a URL precisa começar com "
            "http:// ou https:// e não pode ter espaços",
        ])


if __name__ == "__main__":
    unittest.main()
