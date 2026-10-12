# Spec 002: fluxo de contribuição

- **Status:** Aprovada com ajustes do dono (2026-10-12)
- **Roadmap:** [reorganizar o catálogo](../ROADMAP.md), posição 2
- **Depende de:** [spec 001](../001-fonte-de-verdade-estruturada/spec.md)
- **Decisão relacionada:** [ADR 0002](../../adr/0002-arquivos-gerados-regenerados-no-main.md)

## Contexto

A spec 001 moveu o catálogo para `catalogo/<categoria>.yml` e passou a gerar `README.md`, `data/sources.json` e `data/index.json`. O fluxo de contribuição ainda não acompanhou a mudança:

- **O CI exige os arquivos gerados no PR.** `build_dataset.py --check` falha se o README estiver desatualizado. Quem edita pelo navegador do GitHub, público que o ADR 0001 quis preservar, não tem como regenerar e não passa no CI. Quem regenera localmente traz o `README.md` inteiro no diff, e dois PRs de categorias diferentes voltam a conflitar.
- **As mensagens de erro são feitas para quem escreveu o validador.** Erro de sintaxe vem em inglês do PyYAML; termo fora da taxonomia não sugere o termo certo; URL inválida mostra a expressão regular; erros de formato escondem os de taxonomia até a rodada seguinte.
- **Não há modelos de issue nem de PR.** Sugestões chegam em texto livre, sem os campos que a fonte precisa.
- **O guia `CONTRIBUICAO.md` só recebeu remendos na spec 001.** Ele ainda pede para incluir os gerados no commit e não explica o caminho pelo navegador.
- **Restam pontas da migração:** `data/overrides.json` e seu schema seguem no repositório sem uso; a taxonomia aceita `classificacao: indefinido`, que o schema rejeita; não está escrito o que `heuristica` significa para uma fonte nova.

A issue #1 reúne pendências menores das revisões da spec 001. Esta spec resolve as que tocam o contribuidor e adia as demais, conforme a tabela [Itens da issue #1](#itens-da-issue-1).

## Objetivo

Nenhuma contribuição externa volta a editar o `README.md` gerado. Um contribuidor consegue sugerir uma fonte por formulário, ou editá-la pelo navegador e abrir um PR que passa no CI sem instalar nada, e recebe de uma vez só, em português, cada erro com arquivo, linha e o que fazer.

## Requisitos

### Pull request e arquivos gerados

- **R1.** Um PR que altera só `catalogo/` passa no CI sem incluir `README.md`, `data/sources.json` nem `data/index.json`.
- **R2.** O CI de PR falha se o PR altera um desses três arquivos e o conteúdo difere do gerado a partir do `catalogo/` do próprio PR. A mensagem cita `arquivo:linha` e diz que o PR não precisa incluir os gerados.
- **R3.** Nenhum job do CI grava no repositório: o workflow tem `permissions: contents: read`, não usa `pull_request_target` nem cria commits (ADR 0002). Depois do merge, o mantenedor regenera os três arquivos no `main` num commit dele, assinado. Em push no `main`, um job chamado "Arquivos gerados em dia no main" roda o `--check` estrito e falha, com uma anotação que diz ao mantenedor o que rodar, enquanto os gerados estiverem atrasados.
- **R4.** No PR, o CI regenera os arquivos na própria execução antes de rodar os testes e `tools/validar_docs.py`, para validar o README que existirá depois da regeneração.
- **R5.** No CI e no hook, cada verificação roda mesmo quando a anterior falhou, para o contribuidor ver todos os erros numa rodada.
- **R6.** O hook `tools/hooks/pre-commit` confere o conteúdo do índice do git (o que vai entrar no commit), não a árvore de trabalho, com a regra de R2.
- **R7.** Um `.gitattributes` fixa fim de linha LF em todo texto versionado e marca os três arquivos gerados como `linguist-generated`. O build grava os gerados com LF em qualquer sistema operacional.

### Mensagens de erro

- **R8.** Erro de sintaxe YAML acrescenta uma dica em português para os casos comuns: texto com `: `, texto que começa com `[`, `{`, `*`, `&`, `!`, `@`, `%` ou crase, indentação desalinhada, tabulação e aspas sem fechar. Aspas sem fechar apontam a linha em que as aspas abrem. A dica vale para o carregador em C e para o puro Python.
- **R9.** Termo fora da taxonomia sugere até três termos parecidos. Sem termo parecido, a mensagem lista os termos aceitos quando o eixo tem até 15 termos, ou aponta a seção de `data/taxonomy.json` quando tem mais.
- **R10.** Valor fora de uma lista fechada (`uf`, `classificacao`) lista os valores aceitos. Erro de formato em `url` e em `id` explica o formato em português, sem mostrar a expressão regular.
- **R11.** Erro de formato numa fonte não esconde os erros de taxonomia, de links ou de id das outras fontes do arquivo, nem dos outros campos da mesma fonte.

### Regras do catálogo

- **R12.** O prefixo do `id` de uma fonte é o id da categoria do arquivo em que ela está.
- **R13.** Fonte com `classificacao: override` declara ao menos um termo em `input` e em `output`. Fonte `heuristica` herdada da migração pode manter lista vazia.
- **R14.** `data/taxonomy.json` e o schema do catálogo aceitam exatamente `heuristica` e `override` em `classificacao`; o termo `indefinido` sai da classificação (continua em `tipo_fonte`). A taxonomia descreve `heuristica` como classificação herdada da regra anterior à spec 001, que não se usa em fonte nova, e `override` como classificação definida ou revisada por uma pessoa, obrigatória em fonte nova. Os textos `_sobre` da taxonomia deixam de citar arquivos e programas que não existem mais.
- **R15.** `data/overrides.json` e `data/schemas/overrides.schema.json` saem do repositório. Nenhum documento, dado ou ferramenta ativa os cita. O script de migração documenta como reexecutá-lo a partir do commit anterior à migração.

### Modelos e guia

- **R16.** Três formulários de issue em `.github/ISSUE_TEMPLATE/`: "Sugerir nova fonte", "Reportar link quebrado" e "Corrigir uma fonte", com título prefixado e rótulo próprio. O de nova fonte pede nome, descrição, links, categoria e, opcionalmente, `input`, `output` e `tipo_fonte`; as opções de categoria e de termos seguem `catalogo/_categorias.yml` e `data/taxonomy.json`, e um teste falha se divergirem. Um `config.yml` desliga a issue em branco na interface web e aponta o guia.
- **R17.** `.github/PULL_REQUEST_TEMPLATE.md` com tipo de mudança, descrição e checklist: só `catalogo/` editado, gerados não editados à mão, links testados, sem duplicata, `classificacao: override` em fonte nova, fonte pública e legal.
- **R18.** `CONTRIBUICAO.md` reescrito para o fluxo em YAML: três caminhos (issue, navegador, local), formato de uma fonte com tabela de todos os campos do schema, quando usar aspas, tabela de erros comuns com as mensagens reais, trabalho local com hook, o que acontece depois do merge, uma seção "Para mantenedores" com os comandos de regeneração e commit no `main`, seção do dataset (mantém a âncora `dataset-json`) e padrões de formatação. O exemplo de fonte do guia é validado por teste contra o catálogo real.
- **R19.** As seções "Contributing" e "Structured dataset" do `README.en.md` descrevem o mesmo fluxo, e o rodapé do `README.md` gerado aponta o guia.
- **R20.** Os rótulos `nova fonte`, `link quebrado` e `correção` existem no repositório `webminas/osint-brazuca`.

## Critérios de aceite

- **CA1.** Com o catálogo alterado e os gerados intocados, `build_dataset.py --check --alterados` sai com 0, avisa que os três arquivos serão regenerados depois do merge e imprime `OK: catálogo válido e nenhum arquivo gerado editado à mão.` (teste automatizado).
- **CA2.** Com o `README.md` editado à mão e listado como alterado, o mesmo comando sai com 1 e imprime `README.md:<linha>: difere do gerado a partir de catalogo/` e a orientação de não incluir os gerados (teste automatizado). Sem `--alterados`, o `--check` continua estrito como na spec 001.
- **CA3.** O workflow dispara só em PR e em push no `main`, tem `permissions: contents: read` no topo, nenhum job declara permissões próprias, e o texto não contém `git push`, `git commit`, `graphql` nem `contents: write`. No job `validar`, os passos depois do primeiro rodam com `if: success() || failure()`. `actionlint` não aponta erros (testes automatizados).
- **CA4.** O job "Arquivos gerados em dia no main" roda só em push, usa `--check` sem `--alterados` e emite `::error title=Arquivos gerados desatualizados::` apontando `CONTRIBUICAO.md#mantenedores` (teste automatizado).
- **CA5.** Num repositório descartável, o hook passa com o `README.md` editado só na árvore de trabalho, falha quando a edição é adicionada ao índice e falha com um erro de taxonomia adicionado ao índice mesmo que a árvore de trabalho esteja corrigida; erro de documento e erro de catálogo aparecem na mesma execução (testes automatizados).
- **CA6.** Os sete casos de R8 produzem a dica esperada com os dois carregadores do PyYAML, e indentação e tabulação ganham dica (testes automatizados).
- **CA7.** `placas` sugere `placa`; `igreja` em `tipo_fonte` lista os 14 termos; `telefone` em `output` aponta a seção; `uf: Sp` lista as siglas; URL e id inválidos explicam o formato (testes automatizados).
- **CA8.** Um arquivo com erro de formato numa fonte e erro de taxonomia em outra, e uma fonte com campo ausente e termo errado, reportam todos os erros numa chamada (testes automatizados).
- **CA9.** Id com prefixo de outra categoria e fonte `override` com `input: []` falham com `arquivo:linha`; fonte `heuristica` com lista vazia passa (testes automatizados).
- **CA10.** `git check-attr` devolve `eol: lf` para arquivos do catálogo, das ferramentas e dos documentos, e `linguist-generated: true` só para os três gerados; o build grava bytes com LF (testes automatizados).
- **CA11.** Os formulários têm estrutura válida de issue form, ids únicos, os campos obrigatórios de R16 e opções idênticas ao manifesto e à taxonomia (testes automatizados).
- **CA12.** O exemplo de fonte do `CONTRIBUICAO.md` passa na validação do catálogo; cada mensagem citada na tabela de erros comuns existe nas ferramentas; a tabela de campos cobre todos os campos do schema; a seção "Para mantenedores" traz o comando de commit da regeneração (testes automatizados).
- **CA13.** `data/overrides.json` e `data/schemas/overrides.schema.json` não existem; nenhum `.md` da raiz, JSON de `data/`, ferramenta de `tools/` ou arquivo de `.github/` cita `overrides.json` (teste automatizado).
- **CA14.** Na branch da spec, `python3 -m unittest discover -s tests`, `python3 tools/build_dataset.py --check` e `python3 tools/validar_docs.py` passam; `--report` mantém 874 fontes, 2.313 links, 667 `heuristica` e 207 `override`; gerar duas vezes não deixa diff.
- **CA15.** Depois do primeiro merge no `main` que altere `catalogo/` sem trazer os gerados, o job "Arquivos gerados em dia no main" fica vermelho; depois do commit de regeneração do mantenedor, assinado por ele, o job volta a passar (verificação manual, registrada no PR seguinte).

## Itens da issue #1

| Item da issue #1 | Destino |
|---|---|
| Mensagens do PyYAML em inglês, sem dica de aspas | R8 |
| Prefixo do `id` não conferido com o arquivo da categoria | R12 |
| `build_dataset.py` pode gravar CRLF no Windows | R7 |
| `--report --check` juntos sem teste | Resolvido junto com R2: teste em `tests/test_alterados.py` |
| Hook confere a árvore de trabalho, não o índice | R6 |
| Testes da CI conferem o workflow por substring | R3 (o teste lê o YAML do workflow) |
| `data/overrides.json` e `overrides.schema.json` sem uso | R15 |
| `classificacao: indefinido` na taxonomia e fora do schema (comentário) | R14 |
| `README.en.md:259` cita `data/overrides.json` | Já resolvido no PR #2; R15 impede que volte |
| `esquema.py`: tipo desconhecido, `minLength`, `True == 1`, `pattern` inválido, testes de `null` | Adiado: afeta quem mantém o schema, não o contribuidor. Segue na issue #1. |
| `yaml_linhas.py`: merge keys e docstring de `erro_em` | Adiado: o catálogo não usa merge keys. Segue na issue #1. |
| `catalogo_io.py`: URL do link comparada crua; `FileNotFoundError` de taxonomia, schema ou `catalogo/` ausentes | Adiado: só ocorre com o repositório quebrado, não por edição de fonte. Segue na issue #1. |
| `dataset.py`: `cabecalho.md`/`rodape.md` ausentes | Adiado, pelo mesmo motivo. Segue na issue #1. |
| Teste do modo do hook depende de `.git` | Adiado: o teste continua igual, agora em `tests/test_hook.py`. Segue na issue #1. |
| `migrar_readme.py` e `comparar.py`: robustez | Adiado: ferramentas de uso único, só para auditoria. Segue na issue #1. |
| `readme_gerado`: testes de `grupo` e categoria vazia | Adiado: não muda o fluxo de contribuição. Segue na issue #1. |
| `validar_docs.py`: escape no lugar do travessão literal | Adiado: estilo interno da ferramenta. Segue na issue #1. |

Pontos levantados fora da issue e resolvidos aqui: erros que chegam em rodadas (R5, R11), erro de taxonomia sem termos aceitos (R9), expressão regular crua no erro de `pattern` (R10), `input`/`output` vazios aceitos (R13) e o significado de `heuristica` para fonte nova (R14).

## Fora de escopo

- Classificar as 4 fontes `heuristica` que hoje têm `input` ou `output` vazio (spec 004, saneamento).
- Converter issue de nova fonte em PR automaticamente.
- Verificação de links no CI (spec 003).
- Gerar o `README.en.md` ou traduzir os formulários (spec 005).
- Configurar proteção de branch, aprovação de workflows de forks ou outras opções do repositório além dos rótulos de R20.
- Trocar os badges e links que ainda apontam para `osintbrazuca/osint-brazuca` e renomear o repositório.
- Mudar a taxonomia além da classificação (R14), renomear categorias ou alterar ids.

## Riscos

- **`main` com gerados atrasados.** Entre o merge e o commit do mantenedor, o README e o dataset do `main` mostram a versão anterior. Mitigação: o job "Arquivos gerados em dia no main" fica vermelho até a regeneração, e a seção "Para mantenedores" do guia traz os comandos (ADR 0002).
- **Mantenedor esquece o passo.** Mitigação: o mesmo job vermelho; vários merges podem ser regenerados num commit só.
- **Mudança de mensagens quebra quem as lê por script.** Nenhum consumidor conhecido lê as mensagens; os testes fixam o formato `arquivo:linha: caminho: mensagem`, que não muda.
- **Prefixo do id preso ao arquivo.** Mover uma fonte de categoria passa a exigir id novo, o que quebra quem guardou o id antigo. Hoje nenhum id diverge do arquivo; a spec 004, se mover fontes, decide como tratar ids antigos. Afrouxar a regra depois é trivial; apertá-la depois de divergências aparecerem, não.
