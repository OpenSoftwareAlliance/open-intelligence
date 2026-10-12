# Roadmap: reorganizar o catálogo

Iniciativa decomposta em specs filhas. Este arquivo só lista as specs, a ordem e as dependências; requisitos, critérios de aceite e tarefas ficam em cada spec (`docs/specs/<NNN>-<feature>/`). Decisões arquiteturais isoladas ficam em `docs/adr/`.

## Specs filhas, em ordem

| Ordem | Spec | Depende de | Por que nesta posição |
|-------|------|------------|------------------------|
| 1 | [001-fonte-de-verdade-estruturada](001-fonte-de-verdade-estruturada/spec.md): fontes passam a viver em arquivos estruturados por categoria, e o README.md é gerado a partir deles | nenhuma | Todas as outras specs editam, verificam ou publicam fontes; fazê-las sobre o README monolítico seria retrabalho. |
| 2 | [002-fluxo-de-contribuicao](002-fluxo-de-contribuicao/spec.md): guia, modelos de issue/PR e validação de PR para o novo formato | 001 | Logo após a migração, para que nenhuma contribuição externa volte a editar o README gerado. |
| 3 | 003-saude-dos-links: verificação agendada de links no CI com relatório de links mortos, no lugar de issues manuais | 001 | Precisa do formato estruturado para registrar o estado de cada link; produz a lista que a 004 consome. |
| 4 | 004-saneamento-do-catalogo: seções duplicadas, links mortos, fontes repetidas e consistência da taxonomia | 001, 003 | Usa o relatório da 003 como entrada e vem antes da tradução para não traduzir fontes que serão removidas. |
| 5 | 005-catalogo-bilingue: campos em inglês por fonte e README.en.md gerado | 001, 004 | Traduz o catálogo já saneado; substitui o guia em inglês escrito à mão. |
| 6 | 006-site-de-busca: site estático pesquisável gerado a partir de `data/index.json` | 001; 005 recomendada | É o consumidor final do dataset; com a 005 pronta, já nasce bilíngue. |

## Dependências

```
001 ──┬── 002
      ├── 003 ── 004 ── 005 ── 006
      └──────────────────────── 006
```

A 002 e a 003 podem andar em paralelo depois da 001. A 006 só exige a 001; esperar a 005 é recomendado, não obrigatório.

## Decisões registradas

- [ADR 0001: arquivos YAML por categoria como fonte de verdade do catálogo](../adr/0001-yaml-por-categoria-como-fonte-de-verdade.md) (spec 001)
- [ADR 0002: arquivos gerados regenerados no main pelo CI, fora dos pull requests](../adr/0002-arquivos-gerados-regenerados-no-main.md) (spec 002, proposto)
