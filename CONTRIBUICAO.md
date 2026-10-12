# 🤝 Como Contribuir com o OSINT Brazuca

<p align="center">
  <a href="README.md"><img alt="README Principal" src="https://img.shields.io/badge/%F0%9F%8F%A0%20README%20Principal-1E88E5?style=flat-square"></a>
  <a href="README.en.md"><img alt="English" src="https://img.shields.io/badge/%F0%9F%8C%8E%20English-37474F?style=flat-square"></a>
  <a href="EXEMPLOS_PRATICOS.md"><img alt="Exemplos Práticos" src="https://img.shields.io/badge/%F0%9F%93%96%20Exemplos%20Pr%C3%A1ticos-2E7D32?style=flat-square"></a>
  <a href="FLUXOGRAMA.md"><img alt="Fluxogramas" src="https://img.shields.io/badge/%F0%9F%94%80%20Fluxogramas-6A1B9A?style=flat-square"></a>
  <a href="GUIA_RAPIDO.md"><img alt="Guia Rápido" src="https://img.shields.io/badge/%F0%9F%93%8A%20Guia%20R%C3%A1pido-EF6C00?style=flat-square"></a>
  <a href="CONTRIBUICAO.md"><img alt="Contribuir" src="https://img.shields.io/badge/%F0%9F%A4%9D%20Contribuir-00838F?style=flat-square"></a>
  <a href="data/"><img alt="Dataset" src="https://img.shields.io/badge/%F0%9F%97%82%EF%B8%8F%20Dataset-F9A825?style=flat-square"></a>
  <a href="tools/"><img alt="Ferramentas" src="https://img.shields.io/badge/%F0%9F%9B%A0%EF%B8%8F%20Ferramentas-546E7A?style=flat-square"></a>
</p>

Obrigado por considerar contribuir com o OSINT Brazuca! Há três jeitos de ajudar, do mais simples ao mais completo:

1. **[Abrir uma issue](#abrir-issue)** com um formulário: sem git e sem editar arquivo.
2. **[Editar o catálogo pelo navegador](#editar-navegador)**: altere um arquivo de `catalogo/` no GitHub e abra um pull request.
3. **[Trabalhar localmente](#trabalhar-localmente)**: clone o repositório, rode as verificações e mande o pull request.

> [!IMPORTANT]
> As fontes do catálogo ficam em `catalogo/<categoria>.yml`. O `README.md`, o `data/sources.json` e o `data/index.json` são gerados a partir desses arquivos: não os edite à mão e não os inclua no pull request. Depois do merge, o mantenedor os regenera no `main`.

---

## 📝 Abrir uma issue <a name="abrir-issue"></a>

Escolha o formulário em [Issues > New issue](https://github.com/webminas/osint-brazuca/issues/new/choose):

| Formulário | Quando usar |
|---|---|
| [Sugerir nova fonte](https://github.com/webminas/osint-brazuca/issues/new?template=nova-fonte.yml) | Uma fonte pública brasileira que ainda não está no catálogo. |
| [Reportar link quebrado](https://github.com/webminas/osint-brazuca/issues/new?template=link-quebrado.yml) | Um link não abre, mudou de endereço ou leva a outra página. |
| [Corrigir uma fonte](https://github.com/webminas/osint-brazuca/issues/new?template=correcao.yml) | Nome, descrição, classificação, categoria ou UF errados, ou fonte repetida. |

> [!TIP]
> Sites `.gov.br` costumam bloquear robôs. Antes de reportar um link quebrado, confira no navegador.

---

## 🌐 Editar o catálogo pelo navegador <a name="editar-navegador"></a>

Não precisa instalar nada nem rodar nenhum comando.

1. Abra a pasta [`catalogo/`](catalogo/) e o arquivo da categoria. O nome do arquivo é o id da categoria; o manifesto [`catalogo/_categorias.yml`](catalogo/_categorias.yml) lista todas, na ordem do README.
2. Clique no lápis (**Edit this file**). O GitHub cria um fork seu se for preciso.
3. Acrescente ou corrija a fonte seguindo o [formato de uma fonte](#formato-fonte). Uma fonte nova entra no ponto da lista onde deve aparecer no README.
4. Clique em **Commit changes...** e depois em **Propose changes**.
5. Preencha o modelo do pull request. O CI valida o catálogo em cerca de um minuto; se algo falhar, abra o detalhe da verificação e leia a mensagem, que aponta arquivo e linha (veja [Erros comuns](#erros-comuns)).

Você não precisa regenerar o `README.md` nem o dataset: os arquivos gerados são regenerados no `main` depois do merge.

---

## 🧩 Formato de uma fonte <a name="formato-fonte"></a>

Cada fonte é um item da lista `fontes:` do arquivo da categoria. Exemplo de uma fonte em `catalogo/consulta-de-processos.yml`:

```yaml
  - id: consulta-de-processos/exemplo-consulta-publica
    nome: Exemplo - Consulta Pública de Processos
    descricao: Consulta gratuita, sem cadastro, de processos pelo número ou pelo nome da parte.
    links:
      - url: https://exemplo.jus.br/consulta
        label: Portal nacional
      - url: https://sp.exemplo.jus.br/consulta
        label: Portal de São Paulo
        uf: SP
    input: [numero_processo, nome]
    output: [processo, partes]
    tipo_fonte: judiciario
    classificacao: override
```

A indentação conta: o hífen de cada fonte fica a 2 espaços da margem e os campos dela a 4, sempre com espaços (nunca tabulação). O formato completo está em [`data/schemas/catalogo.schema.json`](data/schemas/catalogo.schema.json).

| Campo | Obrigatório | O que é |
|---|---|---|
| `id` | sim | `categoria/nome-da-fonte`, em minúsculas, sem acento, com hífens. O prefixo é o nome do arquivo da categoria. Não muda quando o nome da fonte muda. |
| `nome` | sim | Título exibido no README. Separe órgão e serviço com hífen simples. |
| `descricao` | sim | O que a fonte permite consultar; diga se é gratuita e se exige cadastro. Pode ser `''`. |
| `links` | sim | Lista com ao menos um link. Cada link tem `url` (começa com `http://` ou `https://`) e, se quiser, `label` (rótulo) e `uf` (sigla do estado). |
| `input` | sim | O que a consulta pede, com termos de [`data/taxonomy.json`](data/taxonomy.json). Use `[nenhum]` quando a fonte é navegada ou baixada por inteiro. |
| `output` | sim | O que a fonte devolve, com termos de `data/taxonomy.json`. |
| `tipo_fonte` | sim | Quem mantém a fonte (`federal`, `estadual`, `municipal`, `judiciario`, `privado`...). |
| `classificacao` | sim | `override` em toda fonte nova. `heuristica` só existe em fontes herdadas da migração e ainda não revisadas; ao revisar a classificação de uma delas, troque para `override`. |
| `observacao` | não | Nota da curadoria (limites de uso, autenticação). |
| `resumo` | não | Recolhe os links num `<details>` com este título, como em `resumo: Links de pesquisa`. |
| `subsecao` | não | Abre um subtítulo `####` da categoria antes desta fonte. |
| `markdown` | não | Texto livre (exemplos de código, tabelas) exibido depois dos links. Os links citados nele levam `em_markdown: true` na lista `links`. |

Regras que o CI confere:

- Fonte com `classificacao: override` declara ao menos um termo em `input` e em `output`.
- Todo termo de `input`, `output` e `tipo_fonte` existe em `data/taxonomy.json`. Para criar um termo novo, acrescente-o lá, com a descrição, e no formulário `.github/ISSUE_TEMPLATE/nova-fonte.yml`, no mesmo pull request.
- Toda URL fica em `links`; URL solta em `descricao`, `resumo`, `observacao` ou `grupo` é erro.
- O `id` é único no catálogo inteiro.

### Quando usar aspas

Coloque o texto entre aspas simples quando ele contiver `: ` (dois-pontos seguido de espaço) ou começar com `[`, `{`, `*`, `&`, `!`, `@`, `%` ou crase. Para um apóstrofo dentro de aspas simples, escreva duas aspas:

```text
descricao: 'Consulta: CPF e CNPJ'
descricao: '[Beta] consulta gratuita'
descricao: 'Arquivo d''Ajuda do portal'
```

Um ` #` no meio de um texto sem aspas vira comentário e corta o resto da linha; use aspas nesse caso também.

### Erros comuns <a name="erros-comuns"></a>

Cada erro do CI começa com `arquivo:linha:` e, quando se refere a um campo, com o caminho dele (`fontes[3].links[0].url` é a URL do primeiro link da quarta fonte do arquivo). O CI mostra todos os erros de uma vez.

| Mensagem (trecho) | O que fazer |
|---|---|
| `YAML inválido: mapping values are not allowed ... Dica: texto com ': ' precisa ficar entre aspas simples` | Ponha o texto entre aspas simples ou corrija a indentação da linha. |
| `YAML inválido: did not find expected key ... alinhe a linha com os campos vizinhos` | A linha está mais ou menos indentada que as vizinhas, ou o texto começa com `[`. |
| `input 'cpff' fora da taxonomia (data/taxonomy.json); você quis dizer 'cpf'?` | Use o termo sugerido ou um termo da lista indicada. |
| `campo obrigatório 'nome' ausente` | Falta o campo na fonte apontada. |
| `a URL precisa começar com http:// ou https:// e não pode ter espaços` | Corrija a `url` do link. |
| `o id precisa começar com 'saude/', o nome do arquivo da categoria` | Ajuste o prefixo do `id` ao arquivo em que a fonte está. |
| `lista vazia em fonte com classificacao override` | Declare ao menos um termo em `input` ou `output`. |
| `README.md:120: difere do gerado a partir de catalogo/` | O pull request editou um arquivo gerado. Desfaça essa mudança e edite só `catalogo/`. |

---

## 💻 Trabalhar localmente <a name="trabalhar-localmente"></a>

1. Faça um fork, clone e crie uma branch:
   ```bash
   git clone https://github.com/SEU-USUARIO/osint-brazuca.git
   cd osint-brazuca
   git checkout -b adicionar-fonte-x
   ```
2. Instale a única dependência, com versão fixada, e ative o hook que roda as verificações antes de cada commit:
   ```bash
   python3 -m pip install -r requirements.txt
   git config core.hooksPath tools/hooks
   ```
3. Edite `catalogo/<categoria>.yml` e confira:
   ```bash
   python3 tools/build_dataset.py --check   # valida o catálogo e mostra todos os erros
   python3 tools/build_dataset.py           # opcional: regenera README.md e data/*.json para ver o resultado
   ```
4. Faça o commit só dos arquivos que você editou (`git add catalogo/`). Se regenerou os arquivos gerados para conferir, não precisa incluí-los; se incluir, eles precisam estar idênticos ao que o build gera.
5. Envie a branch e abra o pull request:
   ```bash
   git push origin adicionar-fonte-x
   ```

O hook confere o que está no índice do git (o que vai entrar no commit), não a pasta de trabalho. Mensagens de commit no imperativo: "Adiciona fonte X", "Corrige link de Y".

Para mudar ferramentas (`tools/`), rode também os testes:

```bash
python3 -m unittest discover -s tests
python3 tools/validar_docs.py
```

---

## 🔁 O que acontece depois do merge <a name="depois-do-merge"></a>

No pull request, a verificação "Catálogo válido e nenhum arquivo gerado editado à mão" pode avisar que os gerados estão desatualizados: é esperado e não bloqueia o merge.

Depois do merge, o workflow [`.github/workflows/validar-dataset.yml`](.github/workflows/validar-dataset.yml) valida o catálogo no `main`, e o job "Arquivos gerados em dia no main" fica vermelho enquanto `README.md`, `data/sources.json` e `data/index.json` não forem regenerados. Quem regenera é o mantenedor, como descrito a seguir.

### Para mantenedores <a name="mantenedores"></a>

Depois de mesclar um pull request que mude `catalogo/`, `data/taxonomy.json` ou `tools/readme/`, regenere os arquivos gerados num commit seu, assinado:

```bash
git switch main && git pull
python3 tools/build_dataset.py
git add README.md data/sources.json data/index.json
git commit -m "Regenera README.md e dataset a partir de catalogo/"
git push
```

Vários merges seguidos podem ser regenerados de uma vez. O job "Arquivos gerados em dia no main" volta a ficar verde no push desse commit.

---

## 🗂️ Dataset JSON <a name="dataset-json"></a>

As fontes do catálogo ficam em `catalogo/<categoria>.yml`, um arquivo YAML por categoria, com a classificação (`input`, `output`, `tipo_fonte`) declarada em cada fonte. O `README.md`, o `data/sources.json` e o `data/index.json` são gerados a partir desses arquivos: não os edite à mão.

| Arquivo | O que é |
|---|---|
| `catalogo/<categoria>.yml` | **Fonte de verdade, editada à mão.** Um arquivo por categoria, com as fontes, links e classificação. |
| `catalogo/_categorias.yml` | Manual. Ordem, título, emoji e âncora de cada categoria no README. |
| `data/taxonomy.json` | Manual. Termos permitidos de `input`, `output`, `tipo_fonte` e `classificacao`, com a descrição de cada um. |
| `data/sources.json` | **Gerado.** Uma entrada por fonte, com os links aninhados, identificada pelo `id`. |
| `data/index.json` | **Gerado.** Um registro por link, achatado para busca. |

```bash
python3 tools/build_dataset.py            # valida catalogo/ e regenera README.md e o dataset
python3 tools/build_dataset.py --check    # só verifica, sem gravar
python3 tools/build_dataset.py --report   # mostra estatísticas do catálogo
```

### Corrigindo a classificação de uma fonte

Edite `input`, `output` ou `tipo_fonte` na própria fonte, no arquivo da categoria, e marque `classificacao: override`. Trecho de `catalogo/apis-publicas-brasileiras.yml`:

```text
  - id: apis-publicas-brasileiras/receitaws-api-cnpj
    nome: ReceitaWS - API CNPJ
    input: [cnpj]
    output: [api_json, cnae, dados_cadastrais, endereco, situacao_cadastral, socios]
    tipo_fonte: privado
    classificacao: override
    observacao: Sem autenticação. Rate limit de 3 requisições por minuto.
```

### Ferramentas de curadoria (só local)

```bash
python3 tools/validar_docs.py --avisos   # URLs repetidas em mais de uma fonte e URLs em http://
python3 tools/checar_links.py            # testa todas as URLs do catálogo e resume ok/redirect/bloqueio/offline
python3 tools/checar_links.py --filtro detran --csv links.csv
```

Esses avisos não bloqueiam o commit: URL repetida pode ser legítima (a mesma consulta em duas categorias) e muitos sites só existem em `http://`. Em `checar_links.py`, `bloqueio` (401, 403, 405, 429 ou 503) costuma ser proteção contra robôs; confira no navegador antes de reportar.

---

## 📐 Padrões de Formatação

### Pontuação

Não use travessão em nenhum texto do projeto, nem nos arquivos de `catalogo/`. Prefira vírgula, dois-pontos, ponto final ou parênteses. Em nomes de fonte, separe com hífen simples: `IBAMA - Consulta de Autuações Ambientais`.

### Alertas

Para destaques nos documentos, use os alertas nativos do GitHub em vez de negrito com emoji. Os cinco tipos válidos são `NOTE`, `TIP`, `IMPORTANT`, `WARNING` e `CAUTION`:

```markdown
> [!WARNING]
> Respeite os limites de requisição das APIs públicas.
```

O marcador fica sozinho na primeira linha e todo o conteúdo seguinte é prefixado com `>`. Use com parcimônia.

### Menu de navegação

O menu no topo de cada documento é um bloco de badges centralizado, idêntico em todos os arquivos. Ao alterar um item, replique a mudança em todos os documentos; `tools/validar_docs.py` confere.

### Documentação e ferramentas

Correções de texto, exemplos práticos e ferramentas (scripts de consulta, validação de links) também são bem-vindos. Código precisa de instruções de uso, respeitar os limites das APIs e trazer avisos sobre a LGPD. As ferramentas do repositório usam só a biblioteca padrão do Python e o PyYAML.

---

## ✅ Checklist Antes de Submeter

- [ ] **Contexto brasileiro:** é relevante para o Brasil?
- [ ] **Links testados:** todos abrem no navegador?
- [ ] **Sem duplicata:** procurei a URL em `catalogo/`?
- [ ] **Categoria certa:** a fonte está no arquivo da seção certa e o `id` começa com o nome desse arquivo?
- [ ] **Classificação:** fonte nova com `classificacao: override` e termos da taxonomia?
- [ ] **Só o catálogo:** não editei `README.md` nem `data/*.json`?
- [ ] **Fonte pública:** é de acesso público e legal?

---

## 🚫 O Que NÃO Será Aceito

> [!CAUTION]
> Pull requests com qualquer um dos itens abaixo são recusados sem análise adicional.

- ❌ Links fora do contexto brasileiro
- ❌ Links fora do contexto proposto
- ❌ Links para fóruns de fraude ou exploits
- ❌ Bases vazadas ou dados pessoais expostos
- ❌ Conteúdo discriminatório
- ❌ Links afiliados ou spam
- ❌ Ferramentas pagas sem versão gratuita (exceto se oficial)

---

## 🏆 Reconhecimento

Todos os contribuidores ficam creditados no histórico do Git e na lista de contribuidores do GitHub, exibida na seção de **Contribuições** do README.

---

## 📞 Dúvidas?

1. **Leia a documentação:** README.md e GUIA_RAPIDO.md.
2. **Consulte as issues existentes:** alguém já teve a mesma dúvida?
3. **Abra uma issue:** escolha o formulário mais próximo do seu caso.

---

## 📜 Código de Conduta

Ao contribuir, você concorda em:

- ✅ Ser respeitoso com outros contribuidores
- ✅ Aceitar críticas construtivas
- ✅ Focar no melhor para a comunidade
- ✅ Demonstrar empatia com outros membros
- ✅ Respeitar diferentes pontos de vista

---

## 🎓 Primeiras Contribuições

Novo em contribuições open source? Bons primeiros passos:

- Reportar ou corrigir um link quebrado
- Melhorar a descrição de uma fonte
- Revisar a classificação de uma fonte `heuristica` e marcá-la como `override`
- Corrigir erros de digitação

Issues marcadas com `good first issue` são boas para começar.

---

<p align="center">
  <strong>Obrigado por contribuir com o OSINT Brazuca! 🇧🇷</strong><br>
  <sub>Juntos estamos construindo a maior base de conhecimento OSINT do Brasil</sub>
</p>
