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

Obrigado por considerar contribuir com o projeto OSINT Brazuca! Este documento fornece diretrizes para diferentes tipos de contribuições.

---

## 📋 Tipos de Contribuição

### 1. 🔗 Reportar Links Quebrados

Se você encontrou um link que não está funcionando:

**Crie uma Issue com as seguintes informações:**
- **Título**: `[LINK QUEBRADO] Nome da fonte`
- **Descrição**: 
  - URL completo do link quebrado
  - Data em que testou
  - Tipo de erro (404, timeout, redirecionamento, etc.)
  - Se possível, sugira uma alternativa

**Exemplo:**
```markdown
**Título:** [LINK QUEBRADO] Consulta CNPJ Receita Federal

**Descrição:**
- URL: http://servicos.receita.fazenda.gov.br/Servicos/cnpjreva/
- Data do teste: 02/02/2026
- Erro: 404 - Página não encontrada
- Alternativa sugerida: https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/
```

---

### 2. ➕ Adicionar Novas Fontes

Quer adicionar uma nova fonte de informação pública?

**Antes de submeter:**
1. ✅ Verifique se a fonte já não existe em `catalogo/`
2. ✅ Teste o link para garantir que está funcionando
3. ✅ Confirme que a fonte é **pública** e **legal**
4. ✅ Verifique se está no contexto brasileiro

**Informações a fornecer:**
- Nome da fonte
- Descrição clara e objetiva (diga aqui se é gratuita ou paga e se exige cadastro)
- URL (testado e funcionando)
- Categoria apropriada

**Exemplo de entrada** em `catalogo/<categoria>.yml` (campos definidos em `data/schemas/catalogo.schema.json`; `input`, `output` e `tipo_fonte` usam os termos de `data/taxonomy.json`):
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
Para recolher os links num `<details>`, acrescente `resumo: Links de pesquisa`; para um subtítulo de grupo antes de um link, use `grupo: '**Região Sul:**'`. Ao dar `build_dataset.py`, o README é gerado e a entrada é validada.

> [!NOTE]
> Coloque o texto entre aspas quando ele contiver `: ` ou começar com `[`, `*`, `@`, `!` ou crase. Sem isso, o YAML é inválido.

---

### 3. 📝 Melhorar Documentação

Contribuições para melhorar a documentação são sempre bem-vindas:

- Corrigir erros ortográficos ou gramaticais
- Melhorar explicações existentes
- Adicionar exemplos práticos
- Traduzir termos técnicos
- Melhorar a formatação

---

### 4. 🔧 Desenvolver Ferramentas

Contribuições técnicas também são valiosas:

- Scripts de automação para consultas
- Integrações com APIs públicas
- Parsers de dados
- Ferramentas de validação de links
- Conversores de formato

**Requisitos:**
- Código bem documentado
- Instruções claras de uso
- Respeitar as limitações das APIs
- Incluir avisos sobre LGPD

---

## 🔄 Processo de Pull Request

### Passo a Passo

1. **Fork o Repositório**
   - Clique em "Fork" no canto superior direito

2. **Clone seu Fork**
   ```bash
   git clone https://github.com/SEU-USUARIO/osint-brazuca.git
   cd osint-brazuca
   ```

3. **Crie uma Branch**
   ```bash
   git checkout -b minha-contribuicao
   ```
   
   **Convenção de nomes:**
   - `adicionar-fonte-X` - para novas fontes
   - `corrigir-link-Y` - para correções de links
   - `melhorar-docs-Z` - para melhorias na documentação

4. **Faça suas Alterações**
   - Edite os arquivos necessários
   - Siga os padrões de formatação (veja abaixo)
   - Teste todas as URLs adicionadas

5. **Regenere o Dataset** (se mexeu em arquivos de `catalogo/`)
   ```bash
   python3 tools/build_dataset.py
   ```
   Isso atualiza `README.md`, `data/sources.json` e `data/index.json`. Inclua esses arquivos no commit.
   Veja a seção [Dataset JSON](#dataset-json) abaixo.

6. **Commit suas Mudanças**
   ```bash
   git add .
   git commit -m "Adiciona fonte de consulta X"
   ```
   
   **Boas práticas para mensagens de commit:**
   - Use verbos no imperativo ("Adiciona", "Corrige", "Atualiza")
   - Seja específico e conciso
   - Explique o "por quê" se necessário

7. **Push para seu Fork**
   ```bash
   git push origin minha-contribuicao
   ```

8. **Abra um Pull Request**
   - Acesse o repositório original no GitHub
   - Clique em "New Pull Request"
   - Selecione sua branch
   - Preencha a descrição detalhadamente

**Template para Pull Request:**
```markdown
## Tipo de Mudança
- [ ] Nova fonte
- [ ] Correção de link
- [ ] Melhoria de documentação
- [ ] Outra (especifique)

## Descrição
Descreva claramente as mudanças realizadas.

## Checklist
- [ ] Testei todos os links adicionados
- [ ] Segui o padrão de formatação do projeto
- [ ] Verifiquei que não há duplicatas
- [ ] Rodei `python3 tools/build_dataset.py` e incluí os arquivos gerados (`README.md` e JSON)
- [ ] Li as diretrizes de contribuição
- [ ] Minhas mudanças respeitam a LGPD

## Informações Adicionais
Qualquer contexto adicional sobre as mudanças.
```

---

## 🗂️ Dataset JSON <a name="dataset-json"></a>

> [!IMPORTANT]
> As fontes do catálogo ficam em `catalogo/<categoria>.yml`, um arquivo YAML por categoria, com a classificação (`input`, `output`, `tipo_fonte`) declarada em cada fonte. O `README.md`, o `data/sources.json` e o `data/index.json` são gerados a partir desses arquivos: não os edite à mão. O `data/overrides.json` e a classificação automática por palavra-chave não são mais usados pelo build.

```bash
python3 tools/build_dataset.py            # valida catalogo/ e regenera README.md e o dataset
python3 tools/build_dataset.py --report   # mostra estatísticas do catálogo
python3 tools/build_dataset.py --check    # só verifica se está atualizado
```

Requer Python 3 e PyYAML, com versão fixada em `requirements.txt`: `python3 -m pip install -r requirements.txt`.

| Arquivo | O que é |
|---|---|
| `data/sources.json` | **Gerado.** Uma entrada por fonte, com os links aninhados. Identificada pelo `id`, não por linha do README. |
| `data/index.json` | **Gerado.** Um registro por link, achatado para busca. |
| `data/taxonomy.json` | Manual. Vocabulário permitido de `input`, `output` e `tipo_fonte`. |
| `catalogo/<categoria>.yml` | **Fonte de verdade, editada à mão.** Um arquivo por categoria, com as fontes, links e classificação. |

> [!CAUTION]
> Nunca edite `sources.json` ou `index.json` à mão. Eles são sobrescritos no próximo build e seu trabalho é perdido.

### Corrigindo a classificação de uma fonte

Os campos `input` (o que a fonte aceita), `output` (o que ela devolve), `tipo_fonte` e `classificacao` são declarados na própria fonte, no arquivo da categoria em `catalogo/`. Para corrigir uma classificação, edite esse arquivo e rode `python3 tools/build_dataset.py`. Trecho de exemplo de `catalogo/apis-publicas-brasileiras.yml`:

```yaml
  - id: apis-publicas-brasileiras/receitaws-api-cnpj
    nome: ReceitaWS - API CNPJ
    input: [cnpj]
    output: [api_json, cnae, dados_cadastrais, endereco, situacao_cadastral, socios]
    tipo_fonte: privado
    classificacao: override
    observacao: Sem autenticação. Rate limit de 3 requisições por minuto.
```

O `id` (`categoria/nome`) identifica a fonte e não muda quando o nome muda. O campo `classificacao` aceita `heuristica` ou `override`. Todo termo de `input`, `output` e `tipo_fonte` é validado contra `data/taxonomy.json`. Para usar um termo novo, adicione-o lá antes, senão o build falha.

### Validação automática

Todo pull request passa pelo workflow `.github/workflows/validar-dataset.yml`, que falha se:

- `README.md`, `sources.json` ou `index.json` estiverem desatualizados (`build_dataset.py --check`)
- o catálogo violar o esquema (`build_dataset.py --check`): links obrigatórios, classificação, termos fora da taxonomia, ids repetidos e URLs de texto livre fora de `links`
- houver travessão (`—`) fora de crases, menu de navegação diferente entre os documentos ou link interno sem âncora (`tools/validar_docs.py`)

Para rodar as mesmas verificações antes de cada commit, ative o hook do repositório uma única vez:

```bash
git config core.hooksPath tools/hooks
```

### Ferramentas de curadoria (só local)

```bash
python3 tools/validar_docs.py --avisos   # lista URLs repetidas em mais de uma fonte e URLs em http://
python3 tools/checar_links.py            # testa todas as URLs do catálogo e resume ok/redirect/bloqueio/offline
python3 tools/checar_links.py --filtro detran --csv links.csv
```

Esses avisos não bloqueiam o commit: URL repetida pode ser legítima (a mesma consulta em duas categorias) e muitos sites só existem em `http://`. Sites `.gov.br` costumam bloquear robôs (`bloqueio` = 401/403/405/429/503), então confira no navegador antes de reportar um link como quebrado.

---

## 📐 Padrões de Formatação

### Pontuação

Não use travessão (`—`) em nenhum texto do projeto. Prefira vírgula, dois-pontos, ponto final ou parênteses. Em títulos de fonte, separe com hífen simples:

```markdown
### IBAMA - Consulta de Autuações Ambientais
```

### Alertas

Para destaques, use os alertas nativos do GitHub em vez de negrito com emoji. Os cinco tipos válidos são `NOTE`, `TIP`, `IMPORTANT`, `WARNING` e `CAUTION`:

```markdown
> [!WARNING]
> Respeite os limites de requisição das APIs públicas.
```

O marcador fica sozinho na primeira linha e todo o conteúdo seguinte é prefixado com `>`. Use com parcimônia: alerta em excesso perde o efeito. O menu de navegação no topo de cada documento é um bloco de badges centralizado (`<p align="center">` com badges do shields.io), idêntico em todos os arquivos: ao alterar um item do menu, replique a mudança em todos os documentos.

### Fontes no Catálogo

Cada fonte é uma entrada YAML em `catalogo/<categoria>.yml`, como no exemplo de [Adicionar Novas Fontes](#2--adicionar-novas-fontes). O README é gerado a partir delas. Orientações:

- Texto livre (descrição de API, requisitos, exemplos de código, tabelas) vai no campo `markdown` da fonte. Os links desse texto são marcados com `em_markdown: true` na lista `links`.
- Fontes estaduais levam `uf` em cada link, e o `resumo` recolhe a lista num `<details>`.
- Todo link fica em `links`; não escreva URLs soltas fora de `markdown`.

---

## ✅ Checklist Antes de Submeter

Antes de enviar seu Pull Request, verifique:

- [ ] **Contexto brasileiro** - É relevante para o Brasil?
- [ ] **Testei todos os links** - Todos funcionam?
- [ ] **Não há duplicatas** - Já existe em `catalogo/`?
- [ ] **Formatação correta** - Segue os padrões?
- [ ] **Descrição clara** - É fácil entender?
- [ ] **Categoria apropriada** - Está na seção certa?
- [ ] **Fonte pública** - É de acesso público?


---

## 🚫 O Que NÃO Será Aceito

> [!CAUTION]
> Pull requests com qualquer um dos itens abaixo são recusados sem análise adicional.

- ❌ Links fora do contexto brasileiro
- ❌ Links fora do contexto proposto
- ❌ Links para foruns de fraud / exploits
- ❌ Conteúdo discriminatório
- ❌ Links afiliados ou spam
- ❌ Ferramentas pagas sem versão gratuita (exceto se oficial)

---

## 🏆 Reconhecimento

Todos os contribuidores serão:
- Listados na seção de **Contribuições** do README
- Creditados no histórico do Git
- Mencionados nas releases quando aplicável

---

## 📞 Dúvidas?

Se tiver dúvidas sobre como contribuir:

1. **Leia a documentação:** README.md, GUIA_RAPIDO.md
2. **Consulte Issues existentes:** Alguém já teve a mesma dúvida?
3. **Abra uma Discussion:** Para perguntas gerais
4. **Abra uma Issue:** Para problemas específicos

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

Novo em contribuições open source? Sem problema!

**Boas primeiras contribuições:**
- Corrigir erros de digitação
- Atualizar links quebrados
- Melhorar descrições existentes
- Adicionar exemplos práticos

**Issues marcadas com:**
- `good first issue` - Boas para iniciantes
- `help wanted` - Precisam de ajuda
- `documentation` - Relacionadas a documentação

---

<p align="center">
  <strong>Obrigado por contribuir com o OSINT Brazuca! 🇧🇷</strong><br>
  <sub>Juntos estamos construindo a maior base de conhecimento OSINT do Brasil</sub>
</p>
