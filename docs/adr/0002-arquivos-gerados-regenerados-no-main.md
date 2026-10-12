# 0002. Arquivos gerados fora dos pull requests, regenerados pelo mantenedor no main

- **Status:** Aceito (2026-10-12)
- **Data:** 2026-10-12
- **Spec:** [002-fluxo-de-contribuicao](../specs/002-fluxo-de-contribuicao/spec.md)

## Contexto

Desde a spec 001, `README.md`, `data/sources.json` e `data/index.json` são gerados a partir de `catalogo/` por `tools/build_dataset.py`, e o CI roda `--check`, que falha se qualquer um deles estiver desatualizado. Na prática, todo pull request que muda o catálogo precisa trazer os três arquivos regenerados.

Isso tem dois custos:

- **Quem edita pelo navegador do GitHub não consegue passar no CI.** Não há como rodar o build sem clonar o repositório, instalar Python e PyYAML. O ADR 0001 escolheu YAML justamente para manter a edição pelo navegador.
- **Os gerados voltam a causar conflito.** Dois PRs em categorias diferentes mexem no mesmo `README.md` e nos mesmos JSON; o segundo a entrar fica em conflito, que o ADR 0001 prometia eliminar.

Restrições que pesam na escolha:

- PRs vêm de forks. No evento `pull_request` de um fork, o `GITHUB_TOKEN` só tem leitura e não há acesso a segredos; o GitHub também não deixa o `GITHUB_TOKEN` gravar no repositório do fork.
- O evento `pull_request_target` roda com token de escrita no contexto do repositório base. Fazer checkout e executar o código do PR nesse evento é a falha clássica de segurança de Actions ("pwn request").
- Regra do dono: todo commit do repositório tem autor e committer Matheus Breguêz, assinado com a chave GPG dele. Commit de bot não é aceito.

Opções avaliadas:

1. **Action que regenera e commita no branch do PR.** Exige `pull_request_target` com checkout do código do PR (inseguro) ou um token pessoal com escrita em forks alheios, e o commit seria de bot. Recusada.
2. **Job no `main` que regenera e publica um commit** (por `git push` ou pela mutação GraphQL `createCommitOnBranch`). Automático, mas o commit sai com autor `github-actions[bot]`, contra a regra do dono, e exige `contents: write` no CI. Recusada pelo dono.
3. **CI do PR valida o catálogo e só recusa gerado editado à mão; o mantenedor regenera no `main` depois do merge, num commit dele; o CI do `main` mostra quando os gerados estão atrasados.** Nenhum job grava no repositório.
4. **Deixar de versionar os gerados.** O `README.md` precisa estar no repositório para o GitHub exibi-lo, e o dataset é consumido por URL raw. Recusada.

## Decisão

Opção 3, no workflow `.github/workflows/validar-dataset.yml`, com `permissions: contents: read` e nenhum job com escrita:

- **Em pull request e em push no `main`**, o job `validar` passa a lista de arquivos alterados (`git diff --name-only HEAD^1 HEAD`; no PR, sobre o commit de merge) para `build_dataset.py --check --alterados -`. O catálogo precisa ser válido; um arquivo gerado só é comparado com o gerado se o commit ou PR o alterou. Gerado intocado e desatualizado vira aviso. Depois o job regenera os arquivos na própria execução e roda testes e `validar_docs.py` sobre o resultado, para validar o README que existirá depois da regeneração.
- **Em push no `main`**, o job "Arquivos gerados em dia no main" roda `build_dataset.py --check` estrito. Se os gerados estiverem atrasados, ele falha com uma anotação de erro que diz ao mantenedor o que rodar. É o sinal visível de que falta regenerar; não bloqueia nada, porque o merge já aconteceu.
- **O mantenedor** (o dono, ou um agente que commita como o dono, com a assinatura GPG dele) roda `python3 tools/build_dataset.py` no `main` depois do merge e commita `README.md`, `data/sources.json` e `data/index.json`. Vários merges podem ser regenerados de uma vez. O passo fica documentado em `CONTRIBUICAO.md`, seção "Para mantenedores".
- O hook `tools/hooks/pre-commit` aplica a regra de `--alterados` sobre o índice do git.
- `pull_request_target` não é usado em nenhum workflow.

## Consequências

Positivas:

- Quem edita pelo navegador abre o PR e passa no CI sem instalar nada.
- PRs de categorias diferentes deixam de conflitar nos arquivos gerados.
- Nenhum código vindo de fork roda com permissão de escrita, e o CI não tem permissão de escrita em lugar nenhum.
- Todo commit do `main` continua sendo do dono, assinado por ele.
- Editar o `README.md` à mão continua sendo erro de CI, com a mesma mensagem `arquivo:linha`.

Negativas e riscos:

- Entre o merge e o commit do mantenedor, o `main` mostra `README.md` e dataset da versão anterior. O job "Arquivos gerados em dia no main" fica vermelho nesse intervalo, o que é esperado.
- O passo depende do mantenedor. Se ele esquecer, o `main` fica atrasado até o próximo commit de regeneração; o job vermelho é o lembrete.
- Um PR que inclua os gerados ainda pode conflitar; o guia orienta a não incluí-los.
- Se um dia o volume de PRs tornar o passo manual pesado, a opção 2 pode ser revista em novo ADR, desde que respeite a regra de autoria.
