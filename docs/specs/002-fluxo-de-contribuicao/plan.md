# Plano da spec 002: fluxo de contribuição

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development ou superpowers:executing-plans para executar [`tasks.md`](tasks.md) tarefa por tarefa.

## Objetivo

Fazer o contribuidor editar só `catalogo/`: o PR passa no CI sem os arquivos gerados, o `main` os regenera depois do merge, as mensagens de erro chegam todas de uma vez e em português, e formulários, modelo de PR e guia ensinam o formato YAML.

## Arquitetura

```
PR (fork, token só leitura)                         push no main / workflow_dispatch
──────────────────────────                          ─────────────────────────────────
job validar                                          job validar (igual)
  git diff --name-only HEAD^1 HEAD                     │
    └─> build_dataset.py --check --alterados -         └─> job regenerar (contents: write, fila)
          catalogo_io.carrega_catalogo                       build_dataset.py
          (schema por fonte, taxonomia com                   git diff --name-only
           sugestão, prefixo do id, override)                commit_gerados.py ─> gh api graphql
          gerado na lista e diferente => erro                 createCommitOnBranch (verificado,
          gerado fora da lista => aviso                       expectedHeadOid = GITHUB_SHA)
  build_dataset.py (regenera na execução)
  unittest + validar_docs.py   (if: success() || failure())

hook pre-commit: git checkout-index --all --prefix=<tmp>/  +  git diff --cached --name-only
                 -> validar_docs.py --avisos  e  build_dataset.py --check --alterados  (falha no fim)
```

- `tools/yaml_linhas.py`: tabela `DICAS` (trecho da mensagem do PyYAML -> dica em português) e `dica(problema)`; aspas sem fechar usam a linha de abertura (`context_mark`).
- `tools/esquema.py`: `enum` lista os valores aceitos; `pattern` usa a palavra-chave `x-mensagem` quando o schema a define.
- `tools/catalogo_io.py`: valida o arquivo só até a lista `fontes`; depois valida cada fonte e roda `_verifica_fonte` nos campos sem erro de formato (taxonomia com `fora_da_taxonomia`, `override` sem lista vazia, links e `markdown`, prefixo e unicidade do id).
- `tools/build_dataset.py`: `grava` (bytes UTF-8 com LF), `--alterados LISTA` (arquivo ou `-`) e `confere`, que separa gerado editado à mão (erro) de gerado só desatualizado (aviso).
- `tools/commit_gerados.py`: monta o corpo de `createCommitOnBranch` com os gerados alterados em base64 e recusa qualquer outro caminho.
- `tools/hooks/pre-commit`: copia o índice para uma pasta temporária e roda as duas verificações ali.
- `.github/ISSUE_TEMPLATE/*.yml`, `.github/PULL_REQUEST_TEMPLATE.md`: formulários e modelo; `tests/test_modelos.py` amarra as opções ao manifesto e à taxonomia.

## Stack

- Python 3.9+ (testado em 3.9.6), biblioteca padrão mais PyYAML 6.0.3 (`requirements.txt`, sem mudança).
- Testes com `unittest`: `python3 -m unittest discover -s tests`. Os testes do hook usam `git` num repositório descartável, sem commits.
- CI: GitHub Actions; `actionlint` para conferir o workflow, se estiver instalado.
- `gh` autenticado com permissão de administrador em `webminas/osint-brazuca` só para criar os rótulos (Tarefa 12).

## Spec

[`spec.md`](spec.md) (vinculante) e [ADR 0002](../../adr/0002-arquivos-gerados-regenerados-no-main.md) (Proposto; aprovar antes de implementar a Tarefa 8).

## Restrições globais

Valores copiados da spec:

- Arquivos gerados: `README.md`, `data/sources.json`, `data/index.json`. PR que altera só `catalogo/` passa sem eles; gerado alterado no PR precisa ser idêntico ao gerado.
- Publicação no `main` pela mutação `createCommitOnBranch` com o `GITHUB_TOKEN`, `contents: write` só no job `regenerar`, sem `pull_request_target`, sem token pessoal, com `expectedHeadOid`.
- Cada verificação roda mesmo depois de uma falha, no CI e no hook. O hook confere o índice.
- `.gitattributes`: LF em todo texto; `linguist-generated` nos três gerados.
- Dicas em português para texto com `: `, texto que começa com `[`, `{`, `*`, `&`, `!`, `@`, `%` ou crase, indentação, tabulação e aspas sem fechar, nos dois carregadores do PyYAML.
- Taxonomia: até 3 sugestões; sem sugestão, lista os termos se o eixo tem até 15, senão aponta a seção.
- Prefixo do id igual ao id da categoria do arquivo. Fonte `override` com ao menos um termo em `input` e `output`.
- `classificacao` aceita só `heuristica` e `override`; `indefinido` sai da classificação, fica em `tipo_fonte`.
- Saem do repositório exatamente: `data/overrides.json` e `data/schemas/overrides.schema.json`.
- Formulários: nova fonte, link quebrado, correção, com rótulos `nova fonte`, `link quebrado`, `correção`; issue em branco desligada.
- Totais do catálogo inalterados: 874 fontes, 2.313 links, 667 `heuristica`, 207 `override`.
- Fora de escopo: classificar as 4 fontes `heuristica` com lista vazia, verificação de links, tradução, proteção de branch, badges do repositório original.
- Regras do projeto: português com acentos corretos (inglês só no `README.en.md`), nenhum travessão em `.md` nem em `catalogo/*.yml`, menu de navegação idêntico entre os documentos, gerados nunca editados à mão, só biblioteca padrão mais PyYAML.

## Decisões de implementação

| Decisão | Motivo |
|---|---|
| Regra do PR em `build_dataset.py --check --alterados`, com a lista de arquivos vinda de fora (`git diff` no workflow, `git diff --cached` no hook) | O build continua sem chamar `git`; os testes passam a lista por texto, sem montar repositório. |
| No PR, `git diff --name-only HEAD^1 HEAD` com `fetch-depth: 2` | O checkout de `pull_request` é o commit de merge, cujo primeiro pai é o `main`; dá exatamente o que o PR muda. Em push, cobre o commit de merge do PR. |
| Gerado alterado no PR precisa ser idêntico ao gerado, em vez de proibir qualquer alteração | Quem regenera localmente por hábito não é punido; o guia orienta a não incluir. |
| Job `regenerar` separado do `validar`, com `needs` | Só ele recebe `contents: write`; o `validar` roda o código do PR com leitura. |
| `createCommitOnBranch` em vez de `git push` | Commit verificado pelo GitHub sem chave no CI (ADR 0002); `expectedHeadOid` impede gravar sobre um `main` que andou. |
| `workflow_dispatch` no workflow e `regenerar` com `if: github.event_name != 'pull_request'` | Reexecutar o job de um push antigo falha por `expectedHeadOid`; a execução manual regenera o `main` atual. |
| Hook copia o índice com `git checkout-index --all --prefix=` e roda as ferramentas da cópia | Confere exatamente o que entra no commit, inclusive as ferramentas, sem `git stash` (que mexeria no trabalho do contribuidor). |
| Testes do hook num repositório sem commits | `git add` basta para preencher o índice; evita commits (e assinatura) em teste. |
| Validação por fonte com `items: {}` no schema do arquivo e `_verifica_fonte` guiada pelos campos com erro | Mostra todos os erros sem rodar taxonomia sobre valor de tipo errado. |
| `x-mensagem` ao lado de `pattern` no schema | Palavra-chave desconhecida é ignorada por validadores de JSON Schema; o texto fica junto da regra. |
| Dica do YAML por trecho da mensagem do PyYAML, testada com `CSafeLoader` e `SafeLoader` | As mensagens do carregador em C e do puro Python diferem; o CI pode usar qualquer um. |
| Sugestão de termo por `difflib.get_close_matches` (corte 0,6, até 3) | Biblioteca padrão; acerta erros de digitação e plural (`placas` -> `placa`). |
| Prefixo do id preso ao arquivo da categoria | Pega fonte copiada de outro arquivo sem trocar o id; hoje nenhum id diverge. Afrouxar depois é trivial. |
| `override` exige lista não vazia; `heuristica` não | As 4 fontes herdadas com lista vazia ficam para a spec 004; fonte nova entra sempre como `override`. |
| Opções dos formulários escritas no YAML e conferidas por teste, sem gerador | Mais simples que um terceiro artefato gerado; o teste diz qual arquivo atualizar. |
| Categoria no formulário como `Título (id)` e termos como `termo: descrição` | O mantenedor lê o id e o termo direto na issue; o contribuidor lê o texto. |
| Links absolutos para `webminas/osint-brazuca` nos modelos e no guia | Links relativos no corpo de issue e PR resolvem diferente conforme a página; o GitHub redireciona se o repositório for renomeado. |
| `data/overrides.json` removido em vez de arquivado | O histórico do git guarda o arquivo; o script de migração diz como reexecutá-lo do commit `a4466fa^`. |
| `CONTRIBUICAO.md` mantém o menu, a âncora `dataset-json` e o primeiro bloco `yaml` como exemplo de fonte | `validar_docs.py` confere o menu; o cabeçalho do README aponta `CONTRIBUICAO.md#dataset-json`; o teste lê o primeiro bloco `yaml`. |

## Foco de revisão

1. **Contribuidor pelo navegador barrado pelo CI.** Se `--alterados` tratar gerado desatualizado como erro, o caminho principal da spec quebra. Teste: `test_pr_so_com_catalogo_passa_e_avisa_que_gerados_serao_regenerados` (Tarefa 6).
2. **Commit do bot sobrescrevendo um `main` mais novo ou levando arquivo indevido.** Teste: `test_pedido_cria_commit_no_branch_esperado` e `test_recusa_arquivo_que_nao_e_gerado` (Tarefa 8); a verificação manual de CA15 confere o commit real.
3. **Hook aprovando o que não vai no commit.** O contribuidor corrige o arquivo na pasta mas esquece o `git add`. Teste: `test_confere_o_indice_e_nao_a_arvore_de_trabalho` (Tarefa 7).
4. **Dica errada mandando pôr aspas onde o problema é indentação.** Teste: `test_indentacao_errada_ganha_dica_de_alinhamento` e os sete casos de `test_dicas_com_o_carregador_em_c` (Tarefa 2).
5. **Formulário oferecendo categoria ou termo que o build recusa.** Teste: `test_categorias_da_nova_fonte_seguem_o_manifesto` e `test_termos_da_nova_fonte_seguem_a_taxonomia` (Tarefa 9).

## Arquivos

| Arquivo | Responsabilidade | Tarefa |
|---|---|---|
| `.gitattributes` | LF em todo texto; gerados marcados | 1 |
| `tools/build_dataset.py` | `grava` com LF; `--alterados` e `confere` | 1, 6 |
| `tools/yaml_linhas.py` | Dicas em português para erros de sintaxe | 2 |
| `tools/esquema.py` | `enum` com valores aceitos; `x-mensagem` | 3 |
| `data/schemas/catalogo.schema.json` | `x-mensagem` em `id` e `url` | 3 |
| `tools/catalogo_io.py` | Sugestão de termo; validação por fonte; prefixo do id; `override` sem lista vazia | 3, 4, 5 |
| `data/taxonomy.json` | `classificacao` sem `indefinido`; textos `_sobre` atualizados | 5 |
| `tools/hooks/pre-commit` | Confere o índice; todas as verificações antes de falhar | 7 |
| `.github/workflows/validar-dataset.yml` | Jobs `validar` e `regenerar` | 8 |
| `tools/commit_gerados.py` | Corpo do `createCommitOnBranch` | 8 |
| `.github/ISSUE_TEMPLATE/*.yml`, `.github/PULL_REQUEST_TEMPLATE.md` | Formulários e modelo de PR | 9 |
| `CONTRIBUICAO.md` | Guia reescrito | 10 |
| `README.en.md`, `tools/readme/rodape.md`, `README.md` (gerado) | Fluxo novo em inglês; rodapé aponta o guia | 10 |
| `data/overrides.json`, `data/schemas/overrides.schema.json` | Removidos | 11 |
| `tools/migracao/migrar_readme.py` | Como reexecutar a migração | 11 |
| `tests/test_fim_de_linha.py`, `test_dicas_yaml.py`, `test_mensagens.py`, `test_uma_rodada.py`, `test_regras_de_conteudo.py`, `test_alterados.py`, `test_hook.py`, `test_modelos.py`, `test_overrides_aposentado.py` | Testes novos | 1 a 11 |
| `tests/test_esquema.py`, `test_catalogo_io.py`, `test_ci.py`, `test_documentacao.py` | Testes ajustados às mensagens e ao fluxo novos | 3, 5, 7, 8, 10 |

## Cobertura da spec

| Item | Onde |
|---|---|
| R1 (PR só com catálogo passa) | Tarefa 6 (`test_pr_so_com_catalogo_passa...`), Tarefa 8 (passo do workflow) |
| R2 (gerado editado à mão no PR falha) | Tarefa 6 (`test_readme_editado_a_mao_no_pr_falha`, `test_gerado_alterado_e_identico_ao_gerado_passa`) |
| R3 (regeneração no `main`, ADR 0002) | Tarefa 8 (`TestWorkflow`, `TestCommitGerados`) |
| R4 (regenera antes de testes e documentos) | Tarefa 8 (`test_validar_confere_edicao_a_mao_regenera_e_roda_tudo`) |
| R5 (todas as verificações numa rodada) | Tarefa 7 (`test_erros_de_documento_e_de_catalogo_aparecem_juntos`), Tarefa 8 (`if: success() \|\| failure()`) |
| R6 (hook confere o índice) | Tarefa 7 |
| R7 (LF e `linguist-generated`) | Tarefa 1 |
| R8 (dicas de YAML) | Tarefa 2 |
| R9 (sugestão de termo) | Tarefa 3 (`TestMensagensDoCatalogo`) |
| R10 (`enum` e `pattern` legíveis) | Tarefa 3 |
| R11 (erros de formato não escondem os demais) | Tarefa 4 |
| R12 (prefixo do id) | Tarefa 5 |
| R13 (`override` sem lista vazia) | Tarefa 5 |
| R14 (classificação na taxonomia) | Tarefa 5 (`TestTaxonomiaDaClassificacao`) |
| R15 (overrides fora do repositório) | Tarefa 11 |
| R16 (formulários de issue) | Tarefa 9 |
| R17 (modelo de PR) | Tarefa 9 (`TestModeloDePullRequest`) |
| R18 (`CONTRIBUICAO.md`) | Tarefa 10 (`TestContribuicao`) |
| R19 (`README.en.md` e rodapé) | Tarefa 10 (`TestOutrosDocumentos`) |
| R20 (rótulos) | Tarefa 12 (passo 1) |
| CA1, CA2 | Tarefa 6 |
| CA3, CA4 | Tarefa 8; Tarefa 12 (`actionlint`) |
| CA5 | Tarefa 7 |
| CA6 | Tarefa 2 |
| CA7 | Tarefa 3 |
| CA8 | Tarefa 4 |
| CA9 | Tarefa 5 |
| CA10 | Tarefa 1 |
| CA11 | Tarefa 9 |
| CA12 | Tarefa 10 |
| CA13 | Tarefa 11 |
| CA14 | Tarefa 12 (passos 2 a 5) |
| CA15 | Tarefa 12 (passo 6, depois do merge) |
