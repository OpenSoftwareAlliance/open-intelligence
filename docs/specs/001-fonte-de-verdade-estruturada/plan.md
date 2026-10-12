# Plano da spec 001: fonte de verdade estruturada

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development ou superpowers:executing-plans para executar [`tasks.md`](tasks.md) tarefa por tarefa.

## Objetivo

Inverter o fluxo do catálogo: as 874 fontes passam a ser declaradas em `catalogo/<categoria_id>.yml` (40 arquivos) mais o manifesto `catalogo/_categorias.yml`, e o `README.md`, o `data/sources.json` e o `data/index.json` passam a ser gerados a partir deles por `tools/build_dataset.py`, sem mudar fontes, links, ids nem classificação.

## Arquitetura

```
catalogo/_categorias.yml ─┐
catalogo/<categoria>.yml ─┼─> yaml_linhas.le_yaml ─> catalogo_io.carrega_catalogo ─> dataset.gera_saidas ─┬─> README.md
data/taxonomy.json ───────┤        (linha de cada valor)    (schema, taxonomia, ids,       │                 ├─> data/sources.json
data/schemas/*.schema.json┘                                  links, manifesto)             │                 └─> data/index.json
                                                                                           └─ readme_gerado.gera_readme
tools/readme/cabecalho.md + rodape.md (trechos fixos) ─────────────────────────────────────────┘
```

- `tools/esquema.py`: validador de JSON Schema mínimo, só com a biblioteca padrão.
- `tools/yaml_linhas.py`: lê YAML guardando a linha de cada valor; base das mensagens `arquivo:linha`.
- `tools/catalogo_io.py`: carrega e valida o catálogo (schema, taxonomia, ids únicos, links presentes, categorias do manifesto, coerência entre `links` e `markdown`).
- `tools/readme_gerado.py`: monta o README (aviso de arquivo gerado, cabeçalho, sumário, categorias, rodapé).
- `tools/dataset.py`: monta `sources.json` e `index.json` no esquema atual e reúne as três saídas.
- `tools/build_dataset.py`: CLI (`--check`, `--report`); não lê `data/overrides.json` nem roda heurística.
- `tools/migracao/`: código de uso único e auditoria. `readme_legado.py` é a cópia literal do build anterior (parser e classificação), `migrar_readme.py` converte README e overrides em `catalogo/` e confere o resultado, `comparar.py` demonstra CA1 a CA5 contra o commit anterior à migração.

Layout de cada fonte no README gerado: `### nome`, a descrição num parágrafo, os links como `- rótulo: url` (dentro de `<details>` quando a fonte tem `resumo`, com o `grupo` de cada link antes dele e `#### subsecao` antes da fonte que a abre) e, por fim, o campo `markdown` sem alteração. Fontes cujo corpo tem bloco de código ou tabela, ou que perderiam texto nesse layout, guardam o corpo original em `markdown` e marcam os links com `em_markdown: true`; o validador exige que essas URLs apareçam no `markdown` e que toda URL do `markdown` fora de bloco de código esteja em `links`.

## Stack

- Python 3 (testado em 3.9 e 3.13), biblioteca padrão mais PyYAML 6.0.3 fixado em `requirements.txt`.
- Testes com `unittest` da biblioteca padrão: `python3 -m unittest discover -s tests`.
- CI: GitHub Actions (`.github/workflows/validar-dataset.yml`); hook local `tools/hooks/pre-commit`.

## Spec

[`spec.md`](spec.md) (vinculante) e [ADR 0001](../../adr/0001-yaml-por-categoria-como-fonte-de-verdade.md) (Aceito).

## Restrições globais

Valores copiados da spec:

- Catálogo atual: 874 fontes e 2.313 links em 40 categorias; classificação de 667 fontes `heuristica` e 207 `override`.
- Um arquivo YAML por categoria em `catalogo/<categoria_id>.yml`, mais o manifesto `catalogo/_categorias.yml`; `catalogo/` contém exatamente 40 arquivos de categoria mais o manifesto.
- Cada fonte declara `id`, `nome`, `descricao`, `links` (`url` e, quando houver, `label` e `uf`), `input`, `output`, `tipo_fonte` e `classificacao` (`heuristica` ou `override`).
- JSON Schema do catálogo em `data/schemas/`; termos de `input`, `output` e `tipo_fonte` validados contra `data/taxonomy.json`.
- O `README.md` gerado começa com um comentário HTML avisando que é gerado e indicando o comando que o regenera.
- `data/sources.json` e `data/index.json` no mesmo esquema atual; só `_sobre` e `fonte` mudam (`fonte` passa a indicar `catalogo/`).
- Geração determinística; `--check` falha se `README.md`, `data/sources.json` ou `data/index.json` estiverem desatualizados.
- Depois da migração, nenhum código do build lê `data/overrides.json` nem executa a heurística de classificação por palavra-chave.
- As duas seções "Outras Buscas" (`outras-buscas`, 54 fontes) viram uma única seção; nenhuma fonte ou link é removido ou alterado.
- Erros do CI e do hook apontam `arquivo:linha`.
- Build completo em menos de 10 segundos.
- Única dependência fora da biblioteca padrão: PyYAML, versão fixada num arquivo de requisitos usado pelo CI e pelo hook.
- Fora de escopo: corrigir, remover ou adicionar fontes e links; mudar taxonomia, categorias ou ids; gerar o `README.en.md`; guia completo de contribuição (spec 002).
- Regras do projeto: português com acentos corretos, nenhum travessão em `.md` nem em `catalogo/*.yml`, menu de navegação idêntico entre os documentos.

## Decisões de implementação

| Decisão | Motivo |
|---|---|
| README em layout por fonte (`### nome`, descrição, `- rótulo: url`), com `resumo`, `grupo` e `subsecao` para preservar `<details>`, cabeçalhos de grupo e subtítulos `####` | Reproduzir byte a byte cada formatação manual exigiria guardar o Markdown com as URLs duplicadas. A spec mede a fidelidade por script (CA4, CA5); a migração mediu perda zero de palavras fora as tags `<details>`/`<summary>` e o título repetido de "Outras Buscas". |
| Corpo literal em `markdown` com `em_markdown: true` nos links, em 54 fontes (bloco de código, tabela, dork entre crases, texto depois da URL, URL com vírgula) | R4 manda reproduzir exemplos de código e tabelas sem alteração; nesses casos o layout por fonte perderia texto ou truncaria URL visível. O validador mantém `links` e `markdown` em sincronia. |
| `subsecao`, `resumo`, `grupo`, `em_markdown` e `markdown` são só de apresentação e não entram no JSON | R3 lista os campos do dataset; o esquema de `sources.json` e `index.json` não muda (R8). |
| Validador próprio de JSON Schema (`tools/esquema.py`), subconjunto usado pelos dois schemas | CA11 admite só o PyYAML; o pacote `jsonschema` seria uma segunda dependência. |
| Ordem das fontes no JSON segue o manifesto: as 16 fontes da segunda seção "Outras Buscas" sobem para junto das 38 da primeira | Consequência direta de R13. `comparar.py` aceita só essa reordenação (`ordem_esperada`) e exige igualdade de todo o resto (CA2). |
| Sumário gerado do manifesto (campo `sumario`, texto atual de cada item) | Evita um terceiro trecho fixo. Efeito: "Outras Buscas" aparece na posição da primeira seção e "APIs Públicas Brasileiras", que faltava no sumário, passa a aparecer. |
| Trechos fixos do README em `tools/readme/cabecalho.md` e `tools/readme/rodape.md` | CA1 exige que `catalogo/` tenha só os 40 arquivos e o manifesto. |
| Migração reaproveita o build antigo como `tools/migracao/readme_legado.py` (cópia literal) e, antes de terminar, relê `catalogo/` e exige o mesmo dataset que o parser antigo produz | R11 (reaproveitar o parser, ficar versionado para auditoria); falha cedo se algum id, link ou classificação mudar. |
| Fonte implícita de "Estação Rádio Base / ERBs" (links direto sob o `##`) vira `### Estação Rádio Base / ERBs` | O id e os dados não mudam; só ganha título próprio. |
| Emoji em título de fonte (2 fontes) não é preservado | O `nome` no dataset já não tinha emoji; nenhum documento aponta para a âncora desses títulos. |
| URLs exibidas no layout por fonte saem normalizadas como no dataset (sem `#` final nem pontuação grudada) | Mesmo valor de `url` do JSON; CA4 compara com a normalização do parser antigo. |
| `data/overrides.json` continua no repositório, sem leitura pelo build | R12 exige tirá-lo do build, não apagá-lo; `README.en.md` e a seção de curadoria do `CONTRIBUICAO.md` ainda o citam e são reescritos na spec 002. A nota da R16 avisa que ele não é mais usado. |
| Testes com `unittest` | Sem dependência nova (CA11). |
| `tools/hooks/pre-commit` passa a ter modo `100755` no git | Hoje o arquivo é `100644` e o git ignora hook sem permissão de execução, então R14 não valeria no hook. |
| `--report` só imprime estatísticas | O `--report` antigo também regravava os arquivos; separar evita escrita acidental. |
| CA5 verificada como "não piora": o link `GUIA_RAPIDO.md` -> `README.md#avisos-legais` já estava quebrado antes e segue igual | Corrigir links está fora do escopo (spec 004); `comparar.py` informa a contagem de links já quebrados. |

## Foco de revisão

1. **README editado à mão e sobrescrito sem aviso.** Quem ainda editar o `README.md` perde o trabalho no próximo build. Teste: `test_check_falha_com_readme_editado` (Tarefa 8), que exige `README.md:<linha>: difere do gerado a partir de catalogo/` no `--check`.
2. **Migração que muda classificação ou link sem perceber.** Um override perdido ou um rótulo trocado passaria despercebido no YAML. Testes: `test_override_congelado_subsecao_rotulo_e_markdown` (Tarefa 6), `test_link_alterado_falha_ca2_e_ca4` (Tarefa 7) e o passo 6 da Tarefa 8 (`comparar.py` com CA2 e CA4).
3. **Erro de indentação no YAML sem localização.** Contribuidores que editam pelo navegador precisam de `arquivo:linha`. Testes: `test_erro_de_sintaxe_yaml_aponta_linha` (Tarefa 2) e `test_yaml_quebrado_aponta_linha` (Tarefa 3).
4. **Fonte em corpo literal dessincronizada.** Editar a URL em `links` e esquecer o `markdown` (ou o contrário) mostraria um link no README e outro no dataset. Testes: `test_link_em_markdown_precisa_aparecer_no_markdown` e `test_url_no_markdown_precisa_estar_em_links` (Tarefa 3).
5. **id repetido ao copiar ou mover fonte entre categorias.** Dois registros com o mesmo id quebram consumidores do dataset. Teste: `test_id_duplicado_entre_arquivos` (Tarefa 3), que cita o arquivo e a linha das duas ocorrências.

## Arquivos

| Arquivo | Responsabilidade | Tarefa |
|---|---|---|
| `requirements.txt` | PyYAML fixado em 6.0.3 | 1 |
| `tools/esquema.py` | Validador mínimo de JSON Schema | 1 |
| `tools/yaml_linhas.py` | YAML com linha de origem e formato `arquivo:linha` | 2 |
| `data/schemas/catalogo.schema.json` | JSON Schema dos arquivos de categoria | 3 |
| `data/schemas/categorias.schema.json` | JSON Schema do manifesto | 3 |
| `tools/catalogo_io.py` | Carga e validação do catálogo | 3 |
| `tests/apoio.py` | Catálogo mínimo de teste em pasta temporária | 3 |
| `tools/readme_gerado.py` | Renderização do README | 4 |
| `tools/dataset.py` | `sources.json`, `index.json` e reunião das saídas | 5 |
| `tools/migracao/readme_legado.py` | Cópia literal do build anterior, só para a migração | 6 |
| `tools/migracao/migrar_readme.py` | Migração de uso único README + overrides -> `catalogo/` | 6 |
| `tools/migracao/comparar.py` | Comparação antes e depois (CA1 a CA5) | 7 |
| `tools/build_dataset.py` | CLI do build a partir de `catalogo/` | 8 |
| `catalogo/_categorias.yml`, `catalogo/*.yml` | Fonte de verdade (gerada uma vez pela migração) | 8 |
| `tools/readme/cabecalho.md`, `tools/readme/rodape.md` | Trechos fixos do README | 8, 11 |
| `README.md`, `data/sources.json`, `data/index.json` | Arquivos gerados | 8, 11 |
| `.github/workflows/validar-dataset.yml` | CI: dependência, testes, `--check`, documentos | 9 |
| `tools/hooks/pre-commit` | Hook local com as mesmas verificações, executável | 9 |
| `tools/validar_docs.py` | Travessão também em `catalogo/*.yml` | 10 |
| `CONTRIBUICAO.md` | Nota sobre `catalogo/` e README gerado | 11 |
| `data/schemas/sources.schema.json`, `data/schemas/index.schema.json` | Modelos com `"fonte": "catalogo/"` | 11 |
| `tests/test_*.py` | Um arquivo de teste por módulo ou tarefa | 1 a 11 |

## Cobertura da spec

| Item | Onde |
|---|---|
| R1 (`catalogo/<categoria_id>.yml`) | Tarefas 3 e 8 |
| R2 (manifesto com ordem, título, emoji, âncora, introdução) | Tarefas 3 (schema), 4 (renderização), 6 e 8 (geração) |
| R3 (campos explícitos por fonte) | Tarefa 3 (schema), Tarefa 6 (migração) |
| R4 (Markdown livre por fonte, sem alteração) | Tarefas 3, 4 e 6 (`markdown`, `em_markdown`) |
| R5 (JSON Schema e taxonomia) | Tarefas 1 e 3 |
| R6 (README gerado com trechos fixos) | Tarefas 4, 5 e 8 |
| R7 (comentário de arquivo gerado) | Tarefa 4 (`AVISO`), Tarefa 11 (`test_readme_gerado_aponta_catalogo_como_fonte`) |
| R8 (`build_dataset.py` lê `catalogo/`, mesmo esquema, `fonte` = `catalogo/`) | Tarefas 5 e 8 |
| R9 (determinismo) | Tarefa 5 (`test_geracao_deterministica`), Tarefa 8 (`test_rodar_duas_vezes_nao_muda_nada`) |
| R10 (`--check`) | Tarefa 8 |
| R11 (migração versionada que reaproveita o parser) | Tarefa 6 |
| R12 (classificação congelada; overrides e heurística fora do build) | Tarefas 6 e 8 (`test_build_nao_le_overrides_nem_heuristica`) |
| R13 (uma única seção "Outras Buscas") | Tarefa 6 (`test_manifesto_funde_secoes_repetidas`), Tarefa 7 (`ordem_esperada`) |
| R14 (CI e hook com schema, taxonomia, ids, URLs, atualização, `arquivo:linha`) | Tarefas 2, 3, 8 e 9 |
| R15 (travessão em `catalogo/`) | Tarefa 10 |
| R16 (nota no `CONTRIBUICAO.md`) | Tarefa 11 |
| CA1 (40 arquivos + manifesto, mesmos ids de categoria) | Tarefa 7 (`comparar.py`), Tarefa 8 (`test_catalogo_tem_40_categorias_mais_o_manifesto`), Tarefa 12 |
| CA2 (JSON idêntico exceto `_sobre` e `fonte`; script versionado) | Tarefa 7, passo 6 da Tarefa 8, Tarefa 12 |
| CA3 (874 fontes, 2.313 links, 667/207, mesmos ids) | Passo 6 da Tarefa 8, Tarefa 12 (`--report`) |
| CA4 (mesmo conjunto de URLs no README) | Tarefa 7, passo 6 da Tarefa 8, Tarefa 12 |
| CA5 (âncoras e links dos demais documentos) | Tarefa 7, passo 6 da Tarefa 8, Tarefa 12 |
| CA6 (`--check` e `validar_docs.py` no CI) | Tarefa 9, Tarefa 12 |
| CA7 (gerar duas vezes deixa `git status` limpo) | Tarefa 8, Tarefa 12 (passo 4) |
| CA8 (casos negativos com `arquivo:linha`) | Tarefa 3 (`test_termo_fora_da_taxonomia`, `test_id_duplicado_entre_arquivos`, `test_fonte_sem_link`, `test_campo_obrigatorio_ausente`, `test_categoria_fora_do_manifesto`), Tarefa 8 (`test_check_falha_com_readme_editado`, `test_check_falha_com_catalogo_invalido_citando_arquivo_e_linha`) |
| CA9 (editar descrição altera só essa fonte) | Tarefa 5 (`test_editar_descricao_altera_so_essa_fonte`) |
| CA10 (build em menos de 10 s) | Tarefa 8 (`test_check_do_repositorio_passa_em_menos_de_10_segundos`), Tarefa 12 |
| CA11 (só PyYAML, fixado, usado por CI e hook) | Tarefas 1 e 9 (`test_requirements_fixa_so_o_pyyaml`) |
| CA12 (build sem overrides nem heurística) | Tarefa 8, Tarefa 12 (passo 6) |
