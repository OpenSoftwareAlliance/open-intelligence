# Spec 001: fonte de verdade estruturada

- **Status:** Implementada e mesclada (PR #2, 2026-10-12)
- **Roadmap:** [reorganizar o catálogo](../ROADMAP.md), posição 1
- **Decisão relacionada:** [ADR 0001](../../adr/0001-yaml-por-categoria-como-fonte-de-verdade.md)

## Contexto

Hoje o `README.md` (cerca de 8.800 linhas) é a fonte de verdade do catálogo: 874 fontes e 2.313 links em 40 categorias. O `tools/build_dataset.py` interpreta o Markdown com heurísticas e gera `data/sources.json` e `data/index.json`; a classificação (`input`, `output`, `tipo_fonte`) vem de heurística (667 fontes) ou de `data/overrides.json` (207 fontes).

Esse arranjo tem custos concretos:

- Um único arquivo enorme gera conflitos de merge entre PRs que mexem em categorias diferentes, e diffs difíceis de revisar.
- A estrutura de uma fonte (nome, descrição, links, UF de cada link) é inferida por expressões regulares sobre Markdown livre; qualquer variação de formatação pode quebrar ou distorcer a extração.
- A classificação fica separada da fonte (`overrides.json`, indexado por um id derivado do título), então renomear uma fonte quebra o vínculo silenciosamente.
- Verificação de links, tradução e um site de busca (specs 003, 005 e 006) precisam anotar dados por fonte e por link, o que não cabe no Markdown.

Este repositório é um fork independente: aceita-se divergir do original (osintbrazuca/osint-brazuca), e mudanças de lá são portadas à mão para `catalogo/` quando valerem.

## Objetivo

Inverter a direção do fluxo: as fontes passam a ser declaradas em arquivos estruturados, um por categoria, e o `README.md`, o `data/sources.json` e o `data/index.json` passam a ser gerados a partir deles. A migração não altera o conteúdo do catálogo: mesmas fontes, mesmos links, mesmos ids, mesma classificação.

## Requisitos

### Formato

- **R1.** O catálogo fica no diretório `catalogo/`, com um arquivo YAML por categoria (`catalogo/<categoria_id>.yml`), conforme o ADR 0001.
- **R2.** Um arquivo de manifesto (`catalogo/_categorias.yml`) define a ordem das categorias no README, o título exibido, o emoji, a âncora HTML (`<a name="...">`) e o texto introdutório de cada categoria.
- **R3.** Cada fonte declara explicitamente: `id`, `nome`, `descricao`, `links` (cada link com `url` e, quando houver, `label` e `uf`), `input`, `output`, `tipo_fonte` e `classificacao` (`heuristica` ou `override`, preservando a procedência atual).
- **R4.** Conteúdo que não é lista de links (exemplos de código das APIs, tabelas, observações) fica num campo opcional de Markdown livre por fonte, reproduzido no README sem alteração.
- **R5.** Existe um JSON Schema para os arquivos do catálogo em `data/schemas/`, e os termos de `input`, `output` e `tipo_fonte` são validados contra `data/taxonomy.json`.

### Geração

- **R6.** Um gerador produz `README.md` a partir de `catalogo/` e de trechos fixos versionados (cabeçalho, menu de badges, avisos legais, seção do dataset, contribuições e créditos).
- **R7.** O `README.md` gerado começa com um comentário HTML avisando que é gerado e indicando o comando que o regenera.
- **R8.** `tools/build_dataset.py` passa a ler `catalogo/` em vez do `README.md` e continua gerando `data/sources.json` e `data/index.json` no mesmo esquema atual (campo `fonte` passa a indicar `catalogo/`).
- **R9.** A geração é determinística: rodar duas vezes seguidas não produz diff.
- **R10.** O modo `--check` falha se `README.md`, `data/sources.json` ou `data/index.json` estiverem desatualizados em relação a `catalogo/`.

### Migração

- **R11.** Um script de migração de uso único converte o `README.md` atual e o `data/overrides.json` em `catalogo/`, reaproveitando o parser existente. Ele fica versionado para auditoria da migração.
- **R12.** A classificação é congelada nos arquivos YAML na migração. Depois dela, `data/overrides.json` e a heurística de classificação por palavra-chave saem do build: nenhum dos dois é lido ou executado, e a classificação de cada fonte só muda por edição do arquivo da categoria.
- **R13.** As duas seções "Outras Buscas", que o parser atual já funde numa única categoria (`outras-buscas`, 54 fontes), viram uma única seção no README gerado. O restante da forma do README segue o layout por fonte decidido em `plan.md` (tabela de decisões), e nenhuma fonte ou link é removido ou alterado.

### Validação e documentação

- **R14.** O CI (`.github/workflows/validar-dataset.yml`) e o hook `tools/hooks/pre-commit` validam o schema, a taxonomia, ids únicos, URLs presentes em toda fonte e a atualização dos arquivos gerados, apontando `arquivo:linha` em cada erro.
- **R15.** `tools/validar_docs.py` continua passando e passa a verificar também os arquivos de `catalogo/` quanto ao travessão.
- **R16.** O `CONTRIBUICAO.md` recebe uma nota curta dizendo que fontes são editadas em `catalogo/` e que o `README.md` é gerado. O fluxo completo de contribuição é a spec 002.

## Critérios de aceite

- **CA1.** `catalogo/` contém exatamente 40 arquivos de categoria mais o manifesto, e os ids de categoria coincidem com os `categoria_id` do `data/sources.json` anterior à migração.
- **CA2.** O `data/sources.json` gerado a partir de `catalogo/` é idêntico ao anterior à migração, exceto pelos campos de metadados `_sobre` e `fonte`. O mesmo vale para `data/index.json`. Um script de comparação versionado demonstra isso no PR da migração.
- **CA3.** Totais preservados: 874 fontes, 2.313 links, 667 fontes `heuristica` e 207 `override`, todos os ids iguais aos anteriores.
- **CA4.** O conjunto de URLs do `README.md` gerado é igual ao conjunto de URLs do `README.md` anterior (comparação por script, não por inspeção).
- **CA5.** Toda âncora `<a name="...">` do README anterior existe no README gerado, e os links internos dos demais documentos (`README.en.md`, `GUIA_RAPIDO.md`, `EXEMPLOS_PRATICOS.md`, `FLUXOGRAMA.md`, `CONTRIBUICAO.md`) continuam resolvendo.
- **CA6.** `python3 tools/build_dataset.py --check` e `python3 tools/validar_docs.py` passam no CI na branch da migração.
- **CA7.** Rodar o gerador duas vezes seguidas deixa `git status` limpo.
- **CA8.** Casos negativos, cada um com teste automatizado: termo fora da taxonomia, id de fonte duplicado, fonte sem link, campo obrigatório ausente, categoria fora do manifesto e README editado à mão fazem o `--check` falhar com mensagem que cita o arquivo e a linha.
- **CA9.** Editar a descrição de uma fonte num arquivo de categoria e regenerar altera apenas essa fonte no `README.md`, no `data/sources.json` e no `data/index.json`.
- **CA10.** O build completo roda em menos de 10 segundos numa máquina de desenvolvimento comum.
- **CA11.** A única dependência fora da biblioteca padrão do Python é o PyYAML, com versão fixada num arquivo de requisitos usado pelo CI e pelo hook de pre-commit.
- **CA12.** Após a migração, nenhum código do build lê `data/overrides.json` nem executa a heurística de classificação por palavra-chave.

## Fora de escopo

- Corrigir, remover ou adicionar fontes e links, inclusive links mortos conhecidos (spec 004).
- Mudar a taxonomia, renomear categorias ou alterar ids.
- Verificação de links no CI (spec 003).
- Traduzir o catálogo ou gerar o `README.en.md` (spec 005); ele continua escrito à mão nesta spec.
- Site de busca (spec 006).
- Modelos de issue e PR e o guia completo de contribuição (spec 002).
- Alterar `EXEMPLOS_PRATICOS.md`, `FLUXOGRAMA.md` e `GUIA_RAPIDO.md` além do necessário para manter links válidos.
- Renomear o repositório.

## Riscos

- **PRs abertos contra o README.md** ficam obsoletos com a migração. Mitigação: anunciar uma janela de congelamento e reaplicar as mudanças pendentes no novo formato.
- **Divergência do original** é aceita: o original continua editando o README, e suas mudanças são portadas à mão para `catalogo/` quando valerem, sem sincronização automática.
