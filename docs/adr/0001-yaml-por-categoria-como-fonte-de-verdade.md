# 0001. Arquivos YAML por categoria como fonte de verdade do catálogo

- **Status:** Aceito (2026-10-11)
- **Data:** 2026-10-11
- **Spec:** [001-fonte-de-verdade-estruturada](../specs/001-fonte-de-verdade-estruturada/spec.md)

## Contexto

O catálogo tem 874 fontes e 2.313 links em 40 categorias, hoje escritos à mão no `README.md` (cerca de 8.800 linhas). O dataset JSON é extraído desse Markdown por heurística, e a curadoria de classificação vive à parte em `data/overrides.json`, ligada às fontes por um id derivado do título.

As próximas etapas do roadmap precisam anotar dados por fonte e por link (estado do link, tradução, metadados para busca), o que o Markdown não comporta. Ao mesmo tempo, o catálogo é mantido por contribuidores que editam pelo navegador do GitHub, então o formato precisa continuar legível e editável sem ferramentas.

Requisitos que pesam na escolha:

- diffs pequenos e conflitos de merge raros entre PRs de categorias diferentes;
- descrições longas e blocos de Markdown (exemplos de código das APIs, tabelas) sem escape doloroso;
- comentários permitidos, para notas de curadoria;
- validação por schema;
- ferramental hoje restrito à biblioteca padrão do Python.

Opções avaliadas:

1. **Manter o README.md como fonte**, só endurecendo o parser. Não resolve conflitos de merge nem dá lugar para dados por link.
2. **JSON por categoria.** Só biblioteca padrão, mas sem comentários e com strings multilinha ilegíveis; ruim para edição manual.
3. **TOML por categoria.** Leitura na biblioteca padrão a partir do Python 3.11, mas a escrita exige biblioteca externa e listas aninhadas de tabelas (fonte, links) ficam verbosas.
4. **Um arquivo Markdown com front matter por fonte** (874 arquivos). Conflitos mínimos, mas o volume de arquivos atrapalha a navegação, a revisão de uma categoria inteira e a ordenação das fontes.
5. **YAML por categoria** (40 arquivos). Legível, aceita comentários e blocos multilinha literais, valida com JSON Schema; exige uma dependência externa.

## Decisão

As fontes passam a ser declaradas em `catalogo/<categoria_id>.yml`, um arquivo por categoria, mais um manifesto `catalogo/_categorias.yml` com a ordem e a apresentação das categorias. A ordem das fontes no arquivo é a ordem de exibição.

Cada fonte carrega `id` explícito e estável (o mesmo id gerado hoje), a classificação (`input`, `output`, `tipo_fonte`) e a procedência dela (`classificacao`). O `data/overrides.json` é absorvido na migração e a heurística deixa de rodar a cada build.

`README.md`, `data/sources.json` e `data/index.json` passam a ser artefatos gerados e verificados pelo CI. Conteúdo livre (código, tabelas) entra num campo de Markdown literal por fonte.

O PyYAML, com versão fixada, é a única dependência externa admitida, aceita como consequência direta da escolha do formato YAML. O schema dos arquivos fica em `data/schemas/`, ao lado dos atuais.

## Consequências

Positivas:

- PRs passam a tocar arquivos pequenos e específicos; conflitos entre categorias desaparecem.
- O id deixa de depender do título: renomear uma fonte não quebra mais a classificação.
- Verificação de links, tradução e site de busca ganham um lugar natural para seus dados.
- O parser de Markdown e suas heurísticas saem do caminho crítico do build.

Negativas e riscos:

- Contribuidores precisam aprender o formato YAML; a spec 002 cobre guia, modelos e mensagens de erro claras.
- Editar o `README.md` direto passa a ser erro de CI, o que exige comunicação aos contribuidores.
- Indentação errada em YAML é um erro comum; o CI precisa apontar arquivo e linha.
- Este repositório é um fork independente e aceita divergir do original (osintbrazuca/osint-brazuca). Mudanças de lá, que seguem editando o README, são portadas à mão para `catalogo/` quando valerem; não há sincronização automática.
- O projeto ganha a primeira dependência fora da biblioteca padrão (PyYAML, versão fixada).
