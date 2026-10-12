# 0003. Novo nome do projeto: Open Intelligence

- **Status:** Aceito (2026-10-12)
- **Data:** 2026-10-12

## Contexto

Este repositório nasceu como hard fork de [osintbrazuca/osint-brazuca](https://github.com/osintbrazuca/osint-brazuca) (ADR 0001) e passou a divergir dele: catálogo em YAML, dataset estruturado, fluxo de contribuição próprio. Mantê-lo com o nome do projeto original confunde quem chega: badges, links e formulários de issue ainda apontavam para o repositório de origem, e não para este.

Hoje o repositório foi transferido da conta pessoal `webminas` para a organização `OpenSoftwareAlliance` e renomeado. O GitHub redireciona as URLs antigas, mas os badges do shields.io e os links do README precisam apontar para o endereço atual.

## Decisão

O projeto se chama **Open Intelligence** e vive em [OpenSoftwareAlliance/open-intelligence](https://github.com/OpenSoftwareAlliance/open-intelligence). A branch principal é `main`.

O original continua sendo citado como origem do catálogo. O crédito ao OSINT Brazuca (osintbrazuca/osint-brazuca) e aos seus colaboradores permanece no README, nos autores e na licença MIT, cujo aviso de copyright é mantido.

## Consequências

- O título, o subtítulo e o texto de apresentação dos READMEs passam a usar "Open Intelligence".
- Os badges (licença, contribuidores, issues, forks, estrelas) e a imagem de contribuidores medem este repositório.
- O badge de Discussões é removido, porque o recurso está desativado.
- Os links de issue, de pull request e do guia de contribuição, os formulários de issue e o modelo de PR apontam para o novo endereço.
- Referências históricas ao projeto original (ADR 0001, specs) continuam apontando para osintbrazuca/osint-brazuca.
- O endereço antigo na conta `webminas` deixa de aparecer no repositório.
- Quem tem clone ou fork antigo continua funcionando pelos redirecionamentos do GitHub, e deve atualizar o remote.
