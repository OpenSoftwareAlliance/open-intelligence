# 0002. Arquivos gerados regenerados no main pelo CI, fora dos pull requests

- **Status:** Proposto (2026-10-12)
- **Data:** 2026-10-12
- **Spec:** [002-fluxo-de-contribuicao](../specs/002-fluxo-de-contribuicao/spec.md)

## Contexto

Desde a spec 001, `README.md`, `data/sources.json` e `data/index.json` são gerados a partir de `catalogo/` por `tools/build_dataset.py`, e o CI roda `--check`, que falha se qualquer um deles estiver desatualizado. Na prática, todo pull request que muda o catálogo precisa trazer os três arquivos regenerados.

Isso tem dois custos:

- **Quem edita pelo navegador do GitHub não consegue passar no CI.** Não há como rodar o build sem clonar o repositório, instalar Python e PyYAML. O ADR 0001 escolheu YAML justamente para manter a edição pelo navegador.
- **Os gerados voltam a causar conflito.** Dois PRs em categorias diferentes mexem no mesmo `README.md` e nos mesmos JSON; o segundo a entrar fica em conflito, que o ADR 0001 prometia eliminar.

Restrições que pesam na escolha:

- PRs vêm de forks. No evento `pull_request` de um fork, o `GITHUB_TOKEN` só tem leitura e não há acesso a segredos; o GitHub também não deixa o `GITHUB_TOKEN` gravar no repositório do fork.
- O evento `pull_request_target` roda com token de escrita no contexto do repositório base. Fazer checkout e executar o código do PR nesse evento é a falha clássica de segurança de Actions ("pwn request"): o PR pode trocar `tools/build_dataset.py` e rodar o que quiser com o token.
- O dono assina todos os commits. Um commit automático precisa ser identificável e, de preferência, verificado.
- O `main` de `webminas/osint-brazuca` não tem proteção de branch hoje.

Opções avaliadas:

1. **Action que regenera e commita no branch do PR.** Exige `pull_request_target` com checkout do código do PR (inseguro) ou um token pessoal com escrita em forks alheios (só funciona com "Allow edits by maintainers" e expõe o token). Recusada.
2. **CI do PR só valida; um passo manual do mantenedor regenera depois do merge.** Seguro e simples, mas depende de lembrar; o `main` fica com gerados atrasados até alguém rodar o build.
3. **CI do PR valida o catálogo e só recusa gerado editado à mão; um job no `main` regenera e publica.** O PR roda sem privilégio; só o job do `main`, que executa código já revisado e mesclado, tem escrita.
4. **Deixar de versionar os gerados.** O `README.md` precisa estar no repositório para o GitHub exibi-lo, e o dataset é consumido por URL raw. Recusada.

## Decisão

Opção 3, no workflow `.github/workflows/validar-dataset.yml`:

- **Em pull request**, o job `validar` roda com `contents: read`. Ele passa a lista de arquivos alterados (`git diff --name-only HEAD^1 HEAD` sobre o commit de merge do PR) para `build_dataset.py --check --alterados -`. O catálogo precisa ser válido; um arquivo gerado só é comparado com o gerado se o PR o alterou. Gerado intocado e desatualizado vira aviso. Depois o job regenera os arquivos na própria execução e roda testes e `validar_docs.py` sobre o resultado, para validar o README que existirá depois do merge.
- **Em push no `main`** (e em execução manual, `workflow_dispatch`), o job `regenerar`, depois do `validar`, roda o build e, se algum gerado mudou, cria um commit no `main` pela mutação GraphQL `createCommitOnBranch`, chamada com o `GITHUB_TOKEN` (`contents: write` só nesse job). Commits criados por essa API com o `GITHUB_TOKEN` saem assinados pelo GitHub e aparecem como verificados, com autor `github-actions[bot]`. O pedido leva `expectedHeadOid` igual ao commit que disparou o job, para nunca gravar gerados de um estado antigo sobre um `main` que andou.
- O job usa `concurrency` com fila (sem cancelamento). Commits feitos com o `GITHUB_TOKEN` não disparam novos workflows, então não há laço.
- O hook `tools/hooks/pre-commit` aplica a mesma regra sobre o índice do git.
- `pull_request_target` não é usado em nenhum workflow.

## Consequências

Positivas:

- Quem edita pelo navegador abre o PR e passa no CI sem instalar nada.
- PRs de categorias diferentes deixam de conflitar nos arquivos gerados.
- Nenhum código vindo de fork roda com permissão de escrita.
- Editar o `README.md` à mão continua sendo erro de CI, com a mesma mensagem `arquivo:linha`.

Negativas e riscos:

- Entre o merge e o fim do job `regenerar` (cerca de um minuto), o `main` mostra `README.md` e dataset da versão anterior.
- O `main` passa a ter commits de `github-actions[bot]`, fora da regra de autoria do dono. Eles são verificados pelo GitHub e só tocam os três arquivos gerados (`tools/commit_gerados.py` recusa qualquer outro caminho).
- O pedido GraphQL leva os três arquivos em base64, cerca de 3,9 MB hoje. Se a API recusar o tamanho, o job falha de forma visível e o `main` fica com gerados atrasados, mas válidos; o dono roda o build e commita, como na opção 2.
- Dois merges seguidos fazem o job do primeiro falhar por `expectedHeadOid`; o job do segundo regenera tudo. Se não houver segundo push, o dono dispara o workflow à mão (`workflow_dispatch`).
- Se o `main` ganhar proteção de branch que exija PR ou aprovação, o job precisa de exceção para o `github-actions[bot]`, ou a decisão volta para a opção 2.
- Um PR que inclua os gerados ainda pode conflitar; o guia orienta a não incluí-los.
