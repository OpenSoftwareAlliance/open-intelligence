import sys
import unittest
from pathlib import Path
from unittest import mock

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

import yaml_linhas  # noqa: E402
from yaml_linhas import le_yaml  # noqa: E402

FONTE = "fontes:\n  - id: alfa/um\n    nome: Um\n    descricao: {}\n    input: [cpf]\n"

# (valor da descrição, linha esperada, trecho da dica)
CASOS = {
    "dois-pontos": ("Consulta: CPF e CNPJ", 4, "texto com ': ' precisa ficar entre aspas simples"),
    "crase": ("`curl` na linha de comando", 4, "começa com crase, @ ou % precisa ficar entre aspas simples"),
    "arroba": ("@perfil oficial", 4, "começa com crase, @ ou % precisa ficar entre aspas simples"),
    "asterisco": ("*destaque* do texto", 4, "começa com * ou & precisa ficar entre aspas simples"),
    "colchete": ("[Beta] consulta gratuita", 4, "começa com [ ou { precisa ficar entre aspas simples"),
    "exclamacao": ("!importante consulta", 4, "começa com ! precisa ficar entre aspas simples"),
    "aspas-abertas": ("'texto sem fechar", 4, "aspas abertas e não fechadas"),
}


class TestDicasYaml(unittest.TestCase):
    def confere(self, carregador):
        with mock.patch.object(yaml_linhas, "CARREGADOR", carregador):
            for nome, (valor, linha, dica) in CASOS.items():
                with self.subTest(carregador=carregador.__name__, caso=nome):
                    dados, _, erros = le_yaml(FONTE.format(valor), "catalogo/alfa.yml")
                    self.assertIsNone(dados)
                    self.assertEqual(len(erros), 1, erros)
                    self.assertTrue(erros[0].startswith(f"catalogo/alfa.yml:{linha}: YAML inválido: "), erros[0])
                    self.assertIn(". Dica: ", erros[0])
                    self.assertIn(dica, erros[0])

    def test_dicas_com_o_carregador_em_c(self):
        self.confere(yaml_linhas.CARREGADOR)

    def test_dicas_com_o_carregador_em_python(self):
        self.confere(yaml.SafeLoader)

    def test_indentacao_errada_ganha_dica_de_alinhamento(self):
        for texto in ("fontes:\n  - id: alfa/um\n    nome: Um\n   descricao: x\n",
                      "fontes:\n  - id: alfa/um\n    links:\n    - url: https://a.gov.br/\n     label: A\n"):
            with self.subTest(texto=texto):
                _, _, erros = le_yaml(texto, "catalogo/alfa.yml")
                self.assertIn("alinhe a linha com os campos vizinhos", erros[0])

    def test_tabulacao_ganha_dica_nos_dois_carregadores(self):
        textos = ("fontes:\n\t- id: alfa/um\n",
                  "fontes:\n  - id: alfa/um\n\tnome: x\n",
                  "fontes:\n  - id: alfa/um\n  \tnome: x\n")
        carregadores = [("SafeLoader", yaml.SafeLoader)]
        if hasattr(yaml, "CSafeLoader"):
            carregadores.append(("CSafeLoader", yaml.CSafeLoader))
        else:
            self.skipTest("yaml.CSafeLoader indisponível: só o carregador em Python seria testado")
        for nome, carregador in carregadores:
            with mock.patch.object(yaml_linhas, "CARREGADOR", carregador):
                for texto in textos:
                    with self.subTest(carregador=nome, texto=texto):
                        _, _, erros = le_yaml(texto, "catalogo/alfa.yml")
                        self.assertEqual(len(erros), 1, erros)
                        self.assertIn("nunca com tabulação", erros[0])

    def test_erro_sem_dica_conhecida_fica_como_esta(self):
        self.assertEqual(yaml_linhas.dica("problema que ninguém previu"), "")


if __name__ == "__main__":
    unittest.main()
