import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from esquema import formata_caminho, valida  # noqa: E402

ESQUEMA = {
    "type": "object",
    "required": ["nome", "links"],
    "additionalProperties": False,
    "properties": {
        "nome": {"type": "string", "minLength": 1},
        "uf": {"type": ["string", "null"], "enum": ["SP", "RJ", None]},
        "links": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["url"],
                "properties": {"url": {"type": "string", "pattern": "^https?://\\S+$"}},
            },
        },
        "input": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
    },
}


class TestValida(unittest.TestCase):
    def test_documento_valido_nao_tem_erros(self):
        doc = {"nome": "X", "uf": None, "links": [{"url": "https://a.gov.br/"}], "input": ["cpf"]}
        self.assertEqual(valida(doc, ESQUEMA), [])

    def test_campo_obrigatorio_ausente_aponta_o_objeto(self):
        erros = valida({"links": [{"url": "https://a/"}]}, ESQUEMA)
        self.assertEqual(erros, [((), "campo obrigatório 'nome' ausente")])

    def test_campo_extra_e_recusado(self):
        erros = valida({"nome": "X", "links": [{"url": "https://a/"}], "cor": 1}, ESQUEMA)
        self.assertEqual(erros, [(("cor",), "campo 'cor' não permitido")])

    def test_tipo_errado(self):
        erros = valida({"nome": 3, "links": [{"url": "https://a/"}]}, ESQUEMA)
        self.assertEqual(erros, [(("nome",), "tipo integer, esperado string")])

    def test_lista_vazia_abaixo_do_minimo(self):
        erros = valida({"nome": "X", "links": []}, ESQUEMA)
        self.assertEqual(erros, [(("links",), "lista com 0 itens, mínimo 1")])

    def test_padrao_e_caminho_aninhado(self):
        erros = valida({"nome": "X", "links": [{"url": "ftp://a"}]}, ESQUEMA)
        self.assertEqual(len(erros), 1)
        self.assertEqual(erros[0][0], ("links", 0, "url"))
        self.assertIn("não segue o padrão", erros[0][1])

    def test_enum_e_item_repetido(self):
        erros = valida({"nome": "X", "uf": "XX", "links": [{"url": "https://a/"}], "input": ["cpf", "cpf"]}, ESQUEMA)
        self.assertEqual(erros, [
            (("uf",), "valor 'XX' fora da lista permitida: SP, RJ, None"),
            (("input", 1), "item repetido 'cpf'"),
        ])

    def test_texto_vazio(self):
        erros = valida({"nome": "", "links": [{"url": "https://a/"}]}, ESQUEMA)
        self.assertEqual(erros, [(("nome",), "texto vazio")])

    def test_formata_caminho(self):
        self.assertEqual(formata_caminho(("fontes", 3, "links", 0, "url")), "fontes[3].links[0].url")
        self.assertEqual(formata_caminho(()), "(raiz)")


if __name__ == "__main__":
    unittest.main()
