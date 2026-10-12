import shutil
import subprocess
import unittest
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOW = RAIZ / ".github" / "workflows" / "validar-dataset.yml"
CAMINHOS = ["*.md", "catalogo/**", "data/**", "tools/**", "tests/**", "requirements.txt",
            ".gitattributes", ".github/**"]


def carrega_workflow():
    dados = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    dados["on"] = dados.pop(True, dados.get("on"))  # o YAML 1.1 lê a chave on como True
    return dados


def comandos(job):
    return [passo.get("run", "") for passo in job["steps"]]


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.wf = carrega_workflow()

    def test_dispara_em_pr_e_em_push_no_main_com_os_mesmos_caminhos(self):
        self.assertEqual(set(self.wf["on"]), {"push", "pull_request"})
        self.assertEqual(self.wf["on"]["push"]["branches"], ["main"])
        self.assertEqual(self.wf["on"]["push"]["paths"], CAMINHOS)
        self.assertEqual(self.wf["on"]["pull_request"]["paths"], CAMINHOS)

    def test_nenhum_job_grava_no_repositorio(self):
        self.assertEqual(self.wf["permissions"], {"contents": "read"})
        for nome, job in self.wf["jobs"].items():
            self.assertNotIn("permissions", job, nome)
        texto = WORKFLOW.read_text(encoding="utf-8")
        for proibido in ("git push", "git commit", "graphql", "contents: write"):
            self.assertNotIn(proibido, texto)

    def test_validar_confere_edicao_a_mao_regenera_e_roda_tudo(self):
        job = self.wf["jobs"]["validar"]
        self.assertEqual(job["steps"][0]["with"]["fetch-depth"], 2)
        self.assertEqual(comandos(job)[2:], [
            "python3 -m pip install -r requirements.txt",
            "set -o pipefail\ngit diff --name-only HEAD^1 HEAD | python3 tools/build_dataset.py --check --alterados -\n",
            "python3 tools/build_dataset.py",
            "python3 -m unittest discover -s tests -v",
            "python3 tools/validar_docs.py",
        ])
        for passo in job["steps"][4:]:
            self.assertEqual(passo.get("if"), "success() || failure()", passo["name"])

    def test_gerados_em_dia_so_no_push_com_aviso_ao_mantenedor(self):
        job = self.wf["jobs"]["gerados-em-dia"]
        self.assertEqual(job["name"], "Arquivos gerados em dia no main")
        self.assertEqual(job["if"], "github.event_name == 'push'")
        script = comandos(job)[-1]
        self.assertIn("python3 tools/build_dataset.py --check", script)
        self.assertNotIn("--alterados", script)
        self.assertIn("::error title=Arquivos gerados desatualizados::", script)
        self.assertIn("CONTRIBUICAO.md#mantenedores", script)


class TestDependencias(unittest.TestCase):
    def test_requirements_fixa_so_o_pyyaml(self):
        linhas = [l for l in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
        self.assertEqual(linhas, ["PyYAML==6.0.3"])


if __name__ == "__main__":
    unittest.main()


class TestActionlint(unittest.TestCase):
    @unittest.skipUnless(shutil.which("actionlint"), "actionlint não instalado")
    def test_workflow_passa_no_actionlint(self):
        r = subprocess.run(["actionlint", str(WORKFLOW)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
