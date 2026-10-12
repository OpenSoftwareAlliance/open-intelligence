# Roadmap: reorganizar o catálogo

Iniciativa decomposta em specs filhas. Este arquivo só lista as specs, a ordem e as dependências; requisitos, critérios de aceite e tarefas ficam em cada spec (`docs/specs/<NNN>-<feature>/`). Decisões arquiteturais isoladas ficam em `docs/adr/`.

## Specs filhas, em ordem

| Ordem | Spec | Depende de | Situação |
|-------|------|------------|----------|
| 1 | [001-fonte-de-verdade-estruturada](001-fonte-de-verdade-estruturada/spec.md): fontes passam a viver em arquivos estruturados por categoria, e o README.md é gerado a partir deles | nenhuma | implementada |
| 2 | [002-fluxo-de-contribuicao](002-fluxo-de-contribuicao/spec.md): guia, modelos de issue/PR e validação de PR para o novo formato | 001 | implementada |
| 3 | 003-saude-dos-links: verificação agendada de links no CI com relatório de links mortos, no lugar de issues manuais | 001 | prevista |
| 4 | 004-saneamento-do-catalogo: seções duplicadas, links mortos, fontes repetidas e consistência da taxonomia | 001, 003 | prevista |
| 5 | 005-catalogo-bilingue: campos em inglês por fonte e README.en.md gerado | 001, 004 | prevista |
| 6 | 006-site-de-busca: site estático pesquisável gerado a partir de `data/index.json` | 001; 005 recomendada | prevista |

## Decisões registradas

- [ADR 0001: arquivos YAML por categoria como fonte de verdade do catálogo](../adr/0001-yaml-por-categoria-como-fonte-de-verdade.md) (spec 001)
- [ADR 0002: arquivos gerados fora dos pull requests, regenerados pelo mantenedor no main](../adr/0002-arquivos-gerados-regenerados-no-main.md) (spec 002)
- [ADR 0003: novo nome do projeto, Open Intelligence](../adr/0003-nome-open-intelligence.md)
