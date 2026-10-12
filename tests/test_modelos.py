import json
import re
import unittest
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
MODELOS = RAIZ / ".github" / "ISSUE_TEMPLATE"
FORMULARIOS = ("nova-fonte.yml", "link-quebrado.yml", "correcao.yml")
TIPOS_DE_CAMPO = {"markdown", "input", "textarea", "dropdown", "checkboxes"}


def formulario(nome):
    return yaml.safe_load((MODELOS / nome).read_text(encoding="utf-8"))


def campo(form, ident):
    return next(c for c in form["body"] if c.get("id") == ident)


class TestFormulariosDeIssue(unittest.TestCase):
    def test_formularios_seguem_a_estrutura_do_github(self):
        for nome in FORMULARIOS:
            with self.subTest(nome=nome):
                form = formulario(nome)
                self.assertTrue({"name", "description", "title", "labels", "body"} <= set(form))
                ids = [c["id"] for c in form["body"] if "id" in c]
                self.assertEqual(len(ids), len(set(ids)))
                for item in form["body"]:
                    self.assertIn(item["type"], TIPOS_DE_CAMPO)
                    self.assertIn("label" if item["type"] != "markdown" else "value", item["attributes"])
                    if item["type"] != "markdown":
                        self.assertRegex(item["id"], r"^[a-z_]+$")

    def test_titulos_e_rotulos(self):
        esperado = {"nova-fonte.yml": ("[NOVA FONTE] ", ["nova fonte"]),
                    "link-quebrado.yml": ("[LINK QUEBRADO] ", ["link quebrado"]),
                    "correcao.yml": ("[CORREÇÃO] ", ["correção"])}
        for nome, (titulo, rotulos) in esperado.items():
            form = formulario(nome)
            self.assertEqual((form["title"], form["labels"]), (titulo, rotulos))

    def test_categorias_da_nova_fonte_seguem_o_manifesto(self):
        manifesto = yaml.safe_load((RAIZ / "catalogo" / "_categorias.yml").read_text(encoding="utf-8"))
        opcoes = campo(formulario("nova-fonte.yml"), "categoria")["attributes"]["options"]
        self.assertEqual(opcoes, [f"{c['titulo']} ({c['id']})" for c in manifesto["categorias"]],
                         "atualize .github/ISSUE_TEMPLATE/nova-fonte.yml junto com catalogo/_categorias.yml")

    def test_termos_da_nova_fonte_seguem_a_taxonomia(self):
        taxonomia = json.loads((RAIZ / "data" / "taxonomy.json").read_text(encoding="utf-8"))
        form = formulario("nova-fonte.yml")
        for eixo in ("input", "output", "tipo_fonte"):
            with self.subTest(eixo=eixo):
                opcoes = campo(form, eixo)["attributes"]["options"]
                termos = taxonomia[eixo]["termos"]
                self.assertEqual(opcoes, [f"{t}: {d}" for t, d in termos.items()],
                                 "atualize .github/ISSUE_TEMPLATE/nova-fonte.yml junto com data/taxonomy.json")
        self.assertTrue(campo(form, "input")["attributes"]["multiple"])
        self.assertTrue(campo(form, "output")["attributes"]["multiple"])

    def test_campos_obrigatorios(self):
        obrigatorios = {"nova-fonte.yml": {"nome", "descricao", "links", "categoria", "confirmacoes"},
                        "link-quebrado.yml": {"fonte", "url", "erro", "confirmacoes"},
                        "correcao.yml": {"fonte", "o_que", "correcao"}}
        for nome, esperados in obrigatorios.items():
            form = formulario(nome)
            marcados = {c["id"] for c in form["body"]
                        if c.get("validations", {}).get("required")
                        or any(isinstance(o, dict) and o.get("required") for o in c["attributes"].get("options", []))}
            self.assertEqual(marcados, esperados, nome)

    def test_issue_em_branco_desligada_e_guia_ligado(self):
        config = yaml.safe_load((MODELOS / "config.yml").read_text(encoding="utf-8"))
        self.assertIs(config["blank_issues_enabled"], False)
        self.assertTrue(any("CONTRIBUICAO.md" in link["url"] for link in config["contact_links"]))

    def test_sem_travessao(self):
        arquivos = [MODELOS / n for n in FORMULARIOS + ("config.yml",)] + [RAIZ / ".github" / "PULL_REQUEST_TEMPLATE.md"]
        for caminho in arquivos:
            self.assertNotIn("—", caminho.read_text(encoding="utf-8"), caminho.name)


class TestModeloDePullRequest(unittest.TestCase):
    def test_modelo_orienta_editar_so_o_catalogo(self):
        texto = (RAIZ / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn("catalogo/", texto)
        self.assertIn("Não editei `README.md`, `data/sources.json` nem `data/index.json` à mão", texto)
        self.assertIn("classificacao: override", texto)
        self.assertIn("CONTRIBUICAO.md", texto)
        self.assertEqual(len(re.findall(r"^- \[ \] ", texto, re.M)) >= 6, True)


if __name__ == "__main__":
    unittest.main()
