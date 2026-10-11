<h1 align="center">🇧🇷 OSINT BRAZUCA 🇧🇷</h1>

<p align="center">
  A curated catalog of Brazilian open sources: public, legal and ready for investigation.<br>
  Know in order to protect, investigate in order to defend.
</p>

<h1 align="center">
  <a href="#"><img src="./assets/logo_profile.png" width="600px" alt="OSINT Brazuca"></a>
</h1>

<p align="center">
<a href="https://github.com/osintbrazuca/osint-brazuca/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/osintbrazuca/osint-brazuca?style=for-the-badge&color=1E88E5&logo=opensourceinitiative&logoColor=white"></a>
<a href="https://github.com/osintbrazuca/osint-brazuca/graphs/contributors"><img alt="Contributors" src="https://img.shields.io/github/contributors-anon/osintbrazuca/osint-brazuca?style=for-the-badge&color=2E7D32&logo=github&logoColor=white"></a>
<a href="https://github.com/osintbrazuca/osint-brazuca/issues"><img alt="Open issues" src="https://img.shields.io/github/issues-raw/osintbrazuca/osint-brazuca?style=for-the-badge&color=EF6C00&logo=github&logoColor=white"></a>
<a href="https://github.com/osintbrazuca/osint-brazuca/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/osintbrazuca/osint-brazuca?style=for-the-badge&color=F9A825&logo=github&logoColor=white"></a>
</p>

---

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

> [!NOTE]
> This is the English entry point to the project. The full catalog lives in [README.md](README.md) and is written in Portuguese, because almost every source it lists (court portals, company registries, state agencies) only exists in Portuguese. This page explains how Brazil's public records are organized, what the identifiers mean and where to look, so you can use the catalog without speaking the language.

## Contents

- [What is OSINT Brazuca](#what-is-osint-brazuca)
- [Legal and ethical notice](#legal-and-ethical-notice)
- [How Brazilian public records are organized](#how-brazilian-public-records-are-organized)
- [Brazilian identifiers cheat sheet](#brazilian-identifiers-cheat-sheet)
- [Portuguese glossary for investigators](#portuguese-glossary-for-investigators)
- [Start from what you have](#start-from-what-you-have)
- [Catalog map](#catalog-map)
- [International sources with Brazil coverage](#international-sources-with-brazil-coverage)
- [Practical tips for investigating Brazil](#practical-tips-for-investigating-brazil)
- [Structured dataset (JSON)](#structured-dataset-json)
- [Contributing](#contributing)
- [Authors and credits](#authors-and-credits)

---

## What is OSINT Brazuca

**OSINT Brazuca** gathers sources (websites, portals, APIs, datasets) and search tricks for open source intelligence in the Brazilian context. OSINT is the practice of finding, selecting and collecting information from public sources and analyzing it, together with other sources, to produce knowledge. Open sources are cheap compared with field operations, and Brazil publishes a remarkable amount of data: court cases, company registries, public spending, electoral filings, vehicle and aircraft registries, environmental enforcement, and much more.

The catalog is useful for:

- **Journalists and researchers** following public money, companies and public officials.
- **Compliance, KYC and due diligence teams** vetting Brazilian counterparties, partners and suppliers.
- **Fraud, security and threat intelligence analysts** investigating domains, phone numbers, scams and infrastructure in Brazil.
- **Lawyers, auditors and public servants** looking for official certificates, lawsuits and sanctions.
- **Anyone abroad** who needs to make sense of Brazilian records without a local guide.

---

## Legal and ethical notice

> [!IMPORTANT]
> This repository only lists **public and legal** sources. Misuse of the information is the sole responsibility of the user.

> [!WARNING]
> Every query involving personal data must comply with Brazil's **General Data Protection Law (LGPD, Law 13,709/2018)**. Processing personal data requires a legal basis and a legitimate purpose, even when the data is publicly accessible.

Relevant legislation: **LGPD** (Law 13,709/2018, data protection), **Marco Civil da Internet** (Law 12,965/2014, internet rights and duties) and **LAI** (Law 12,527/2011, Brazil's freedom of information act).

**Good practice:** prefer official sources, respect people's privacy and dignity, document your sources and methodology, have a legitimate purpose (journalism, research, security, compliance), and never republish sensitive personal data.

**Not allowed:** social engineering or system intrusion, stalking or harassment, discrimination, unauthorized resale of data, breach of professional secrecy, and use of leaked databases.

---

## How Brazilian public records are organized

Understanding the structure of the Brazilian state saves hours of searching:

- **Three levels of government.** The Union (*federal*), 26 states plus the Federal District (*estados*, abbreviated by a two-letter **UF** code such as SP, RJ, MG) and 5,570 municipalities (*municípios*). Many records exist separately at each level, so a single nationwide search is often impossible.
- **Domains tell you who runs a site.** `.gov.br` is the executive branch (federal agencies use `gov.br/<agency>`, states use `<agency>.<uf>.gov.br`), `.jus.br` is the judiciary, `.mp.br` is the public prosecution service, `.leg.br` is the legislature, `.def.br` is the public defender's office. Anything else is private, academic or civil society.
- **The judiciary is fragmented.** There are state courts (*Tribunais de Justiça*, TJ), federal regional courts (TRF), labor courts (TRT), electoral courts (TRE), military courts and the superior courts (STF, STJ, TST, TSE, STM). Each runs its own case lookup. The National Council of Justice (CNJ) provides unified tools, and every case since 2010 carries a unique national number.
- **Companies are registered twice.** The Federal Revenue Service (*Receita Federal*) issues the **CNPJ** tax ID and publishes partners (*sócios*), while the state commercial registries (*Juntas Comerciais*) hold articles of incorporation and amendments.
- **Real estate lives in notary offices.** Property records are kept by private registry offices (*cartórios de registro de imóveis*) under state oversight. The national ONR platform and state portals provide online requests, usually paid.
- **Official gazettes are a gold mine.** Appointments, contracts, sanctions, company acts and court notices are published in *Diários Oficiais* at every level of government.
- **Transparency portals are mandatory.** The LAI requires every public body to publish spending, contracts and payroll. Salaries of public servants, including judges, are public by name.

---

## Brazilian identifiers cheat sheet

Most Brazilian lookups start from an identifier. Knowing its format tells you what you are looking at and which source accepts it.

| Identifier | What it is | Format / example | Notes |
|---|---|---|---|
| **CPF** | Individual taxpayer ID, the de facto national ID number | `000.000.000-00` (11 digits) | Last two digits are check digits. Required for most services and for creating a gov.br account. |
| **CNPJ** | Company and legal entity tax ID | `00.000.000/0001-00` (14 digits) | `/0001` is the head office; other numbers are branches. Since 2026 new CNPJs may contain letters. |
| **RG** | State-issued identity card number | Varies by state | Not unique nationwide; being replaced by the CIN, which uses the CPF. |
| **Título de eleitor** | Voter registration number | 12 digits | Used by the Electoral Court (TSE). |
| **NIS / PIS / NIT** | Social security and social programs number | 11 digits | Appears in social benefit records. |
| **CNH** | Driver's license number | 11 digits | Issued by state DETRANs. |
| **Placa** | Vehicle license plate | `ABC1D23` (Mercosur) or `ABC-1234` (old) | Most DETRAN lookups also ask for the RENAVAM. |
| **RENAVAM** | National vehicle registry code | 11 digits | Printed on the vehicle registration certificate. |
| **Chassi** | Vehicle identification number (VIN) | 17 characters | |
| **CEP** | Postal code | `00000-000` | First digits encode the region. |
| **Número CNJ** | Unified court case number | `NNNNNNN-DD.AAAA.J.TR.OOOO` | `AAAA` is the year, `J` the branch of the judiciary, `TR` the court and `OOOO` the originating unit. |
| **OAB** | Lawyer's bar registration | Number + UF, e.g. `123456/SP` | Searchable on the national lawyers registry (CNA). |
| **CRM / CRO / CREA...** | Professional council registrations (doctors, dentists, engineers...) | Number + UF | Each council has its own public registry. |
| **NIRE** | Company registration number at the state Junta Comercial | 11 digits | |
| **Inscrição Estadual (IE)** | State tax registration | Varies by state | Searchable via SINTEGRA. |
| **CNES** | Health facility and health professional registry | 7 digits | |
| **CAR** | Rural Environmental Registry code | `UF-0000000-XXXX...` | Links rural properties to their boundaries. |
| **Matrícula** | Real estate registration number | Number + registry office | Only meaningful together with the *cartório* that issued it. |
| **Prefixo / Marca** | Aircraft registration | `PP-`, `PR-`, `PS-`, `PT-`, `PU-` | Searchable in the ANAC aircraft registry (RAB). |
| **IMEI** | Mobile handset identifier | 15 digits | Anatel and carriers can check blocked devices. |

---

## Portuguese glossary for investigators

| Portuguese | English | Where it shows up |
|---|---|---|
| Consulta | Lookup, search | Almost every search form |
| Certidão (negativa / positiva) | Certificate (clean / with records) | Court, tax, labor and electoral certificates |
| Antecedentes criminais | Criminal record | Federal Police and state police certificates |
| Processo / Jurisprudência | Lawsuit / case law | Court portals |
| Mandado de prisão | Arrest warrant | BNMP (national warrant database) |
| Procurado / Desaparecido | Wanted / Missing | Police portals |
| Razão social / Nome fantasia | Legal name / Trade name | Company records |
| Quadro societário (QSA) / Sócio | Shareholder structure / Partner | CNPJ records |
| Junta Comercial | State commercial registry | Articles of incorporation |
| Cartório | Notary and registry office | Births, deaths, marriages, property, protests |
| Protesto | Formal protest of unpaid debt | Credit risk indicator |
| Dívida ativa | Outstanding tax debt | PGFN and state attorney offices |
| Diário Oficial | Official gazette | Appointments, contracts, sanctions |
| Licitação / Contrato / Convênio | Public tender / Contract / Grant agreement | Transparency portals |
| Servidor público / Remuneração | Civil servant / Salary | Transparency portals |
| Emenda parlamentar | Congressional budget earmark | Transparency portals |
| Inidônea / Punida / Suspensa | Debarred / Sanctioned / Suspended | CEIS, CNEP, TCU |
| Candidato / Prestação de contas | Candidate / Campaign finance report | TSE |
| Auto de infração / Embargo | Violation notice / Embargo | IBAMA, labor inspection |
| Óbito / Nascimento / Casamento | Death / Birth / Marriage | Civil registry |
| Matrícula do imóvel | Property title registration | Real estate registry |
| Placa / Veículo / Multa | Plate / Vehicle / Traffic fine | DETRAN and SENATRAN |

---

## Start from what you have

The catalog is also indexed by **input type** (what you already know) and **output type** (what the source returns). Use this table as a starting point, then follow the links to the Portuguese sections.

| You have | Look in |
|---|---|
| A **person's name** | [Court cases](README.md#consulta-processos), [Official gazettes](README.md#diarios-oficiais), [Wanted persons](README.md#pessoas-procuradas), [Missing persons](README.md#pessoas-desaparecidas), [Academic records](README.md#informacoes-academicas), [Judiciary salaries](README.md#dados-de-remuneracao-do-judiciario), [Search engine dorks](README.md#dorks) |
| A **CPF** | [CPF/CNPJ lookups](README.md#busca-cpf-cnpj-crm-cna), [Social benefits](README.md#beneficios-sociais), [Electoral records](README.md#registros-eleitorais-politicos) |
| A **CNPJ** or company name | [CPF/CNPJ lookups](README.md#busca-cpf-cnpj-crm-cna), [Transparency and consumer protection](README.md#transparencia-defesa-consumidor), [Foreign trade](README.md#comercio-exterior), [Trademarks and patents](README.md#registros-marcas-patentes), [Environmental records](README.md#registros-ambientais) |
| A **professional license** (OAB, CRM...) | [CPF/CNPJ/CRM/CNA lookups](README.md#busca-cpf-cnpj-crm-cna), [Professional councils](README.md#servicos-estaduais) |
| A **license plate**, RENAVAM or VIN | [Road transport](README.md#consulta-transporte-terrestre) |
| An **aircraft or vessel** | [Air transport](README.md#consulta-transporte-aereo), [Water transport](README.md#consulta-transporte-aquaviario) |
| A **phone number** | [Telecom](README.md#telecom), [Messaging app indexers](README.md#indexador-mensagens) |
| A **domain, IP or ASN** | [.br domains](README.md#dominios-br), [Cybersecurity](README.md#seguranca-cibernetica) |
| An **address or coordinates** | [Maps and geodata](README.md#mapas-geo), [Real estate](README.md#registros-imoveis-propriedades), [Territory and environment](README.md#territorio-meio-ambiente-fiscalizacao), [Base stations (ERBs)](README.md#estacoes-radio-erbs) |
| A **social media handle** | [Social networks](README.md#redes-sociais), [Messaging app indexers](README.md#indexador-mensagens) |
| Nothing yet, just a topic | [Open data and datasets](README.md#datasets), [Public safety statistics](README.md#estatísticas), [Public APIs](README.md#apis-publicas) |

---

## Catalog map

The catalog is split into the categories below. Each link opens the corresponding section of the Portuguese README.

| Category (Portuguese section) | What you find | Sources |
|---|---|---:|
| [Social benefits](README.md#beneficios-sociais) <br><sub>Benefícios sociais (Políticas Públicas)</sub> | Social programs, social security (INSS) and unclaimed money in the financial system | 6 |
| [Missing persons](README.md#pessoas-desaparecidas) <br><sub>Pessoas Desaparecidas</sub> | National and state missing persons databases | 3 |
| [Wanted persons](README.md#pessoas-procuradas) <br><sub>Pessoas Procuradas pela Justiça no Brasil</sub> | Federal and state wanted lists, arrest warrants | 6 |
| [Court cases](README.md#consulta-processos) <br><sub>Consulta de Processos</sub> | Case lookup in every branch of the judiciary, case law, CNJ unified tools | 32 |
| [Individuals, companies and licenses](README.md#busca-cpf-cnpj-crm-cna) <br><sub>Busca de Informações via CPF/CNPJ/CRM/CNA</sub> | CPF/CNPJ status, partners, commercial registries, professional councils, certificates | 67 |
| [Public safety statistics](README.md#estatísticas) <br><sub>Estatísticas Segurança Pública</sub> | Crime dashboards, prison data, violence atlases | 13 |
| [Elections and politics](README.md#registros-eleitorais-politicos) <br><sub>Registros Eleitorais e Políticos</sub> | Candidates, campaign finance, party membership, legislatures, votes | 31 |
| [Real estate](README.md#registros-imoveis-propriedades) <br><sub>Registros de Imóveis e Propriedades</sub> | Property registries, property tax, asset freezes | 11 |
| [Environmental records](README.md#registros-ambientais) <br><sub>Registros Ambientais</sub> | Environmental licenses, fines and embargoes | 16 |
| [Foreign trade](README.md#comercio-exterior) <br><sub>Comércio Exterior</sub> | Import and export statistics and registered traders | 9 |
| [Trademarks and patents](README.md#registros-marcas-patentes) <br><sub>Registros de Marcas e Patentes</sub> | INPI trademark, patent and design searches | 3 |
| [Transparency and consumer protection](README.md#transparencia-defesa-consumidor) <br><sub>Transparência Pública e Defesa do Consumidor</sub> | Public spending, contracts, tenders, audit courts, sanctions, consumer complaints | 53 |
| [Official gazettes](README.md#diarios-oficiais) <br><sub>Diários Oficiais</sub> | Federal, state and municipal gazettes | 6 |
| [Culture and media](README.md#cultura-audiovisual) <br><sub>Cultura e Audiovisual</sub> | Cultural funding, film agency and broadcasting records | 18 |
| [Telecom](README.md#telecom) <br><sub>Telecom</sub> | Carriers, number portability, licensed stations, Anatel lookups | 34 |
| [Cell towers](README.md#estacoes-radio-erbs) <br><sub>Estação Rádio Base / ERBs</sub> | Location of mobile base stations | 1 |
| [Academic records](README.md#informacoes-academicas) <br><sub>Informações Acadêmicas</sub> | CVs (Lattes), theses, accredited institutions, research groups | 33 |
| [Maps and geodata](README.md#mapas-geo) <br><sub>Mapas e Georreferenciamento</sub> | IBGE, state and municipal geoportals, cadastral maps | 17 |
| [Territory and environment](README.md#territorio-meio-ambiente-fiscalizacao) <br><sub>Território, Meio Ambiente & Fiscalização</sub> | Deforestation, fires, rural properties, indigenous lands, mining | 33 |
| [Health](README.md#saude) <br><sub>Saúde</sub> | Health facilities and professionals, DATASUS, ANVISA, health insurers | 24 |
| [Search engine dorks](README.md#dorks) <br><sub>Motores de Busca Contexto Brasil</sub> | Ready-made queries for Brazilian government and court domains | 40 |
| [Social networks](README.md#redes-sociais) <br><sub>Rede Social</sub> | Profile search tools and ad libraries | 23 |
| [Messaging app indexers](README.md#indexador-mensagens) <br><sub>Indexadores de Serviço de Mensagens Instantâneas</sub> | Telegram and WhatsApp group indexers | 2 |
| [Open data](README.md#datasets) <br><sub>Datasets / Dados Abertos</sub> | Federal, state and city open data portals and bulk datasets | 60 |
| [Judiciary salaries](README.md#dados-de-remuneracao-do-judiciario) <br><sub>Dados de remuneração do Judiciário</sub> | Payroll of judges and court staff | 1 |
| [Road transport](README.md#consulta-transporte-terrestre) <br><sub>Consulta de Transporte Terrestre</sub> | Vehicles, plates, fines, DETRANs, carriers | 32 |
| [Bus tracking](README.md#tracking-viagens-onibus) <br><sub>Tracking de Viagens de Ônibus</sub> | Real-time public transport positions | 6 |
| [Water transport](README.md#consulta-transporte-aquaviario) <br><sub>Consulta de Transporte Aquaviário</sub> | Vessels, ports and maritime authorities | 14 |
| [Air transport](README.md#consulta-transporte-aereo) <br><sub>Consulta de Transporte Aéreo</sub> | Aircraft registry, airports, accidents | 12 |
| [Live cameras](README.md#cameras-online) <br><sub>Câmeras Online</sub> | Public traffic and city cameras | 27 |
| [Prosecutors and public defenders](README.md#ministerios-publicos-defensorias) <br><sub>Ministérios Públicos e Defensorias Públicas</sub> | Public prosecution services and public defender offices | 4 |
| [Cybersecurity](README.md#seguranca-cibernetica) <br><sub>Segurança Cibernética</sub> | CERT.br, incident statistics, internet infrastructure | 10 |
| [Public APIs](README.md#apis-publicas) <br><sub>APIs Públicas Brasileiras</sub> | BrasilAPI, IBGE, Central Bank, transparency and procurement APIs | 24 |
| [Blockchain and crypto](README.md#blockchain-criptomoedas) <br><sub>Blockchain e Criptomoedas</sub> | Regulator alerts and crypto-asset oversight | 6 |
| [Civil defense](README.md#defesa-civil-emergencias) <br><sub>Defesa Civil e Emergências</sub> | Disaster alerts and emergency records | 13 |
| [Energy and infrastructure](README.md#energia-infraestrutura) <br><sub>Energia e Infraestrutura</sub> | Power, oil and gas, infrastructure registries | 14 |
| [State services and professional councils](README.md#servicos-estaduais) <br><sub>Serviços Públicos Estaduais e Conselhos Profissionais</sub> | State services and professional registries | 7 |
| [Other searches](README.md#outras-buscas) <br><sub>Outras Buscas</sub> | Notaries, archives, newspaper collections, fact-checkers, miscellaneous | 54 |
| [Brazilian domains](README.md#dominios-br) <br><sub>Categorias de Domínios .br</sub> | Registro.br data and .br domain categories | 2 |
| [International sources](README.md#fontes-internacionais) <br><sub>Fontes Internacionais com Cobertura do Brasil</sub> | Offshore, sanctions, tracking, infrastructure, imagery, Latin America | 107 |
| **Total** | 40 categories, 874 sources and 2,313 links | **874** |

---

## International sources with Brazil coverage

Brazilian investigations rarely stop at the border: companies hold assets offshore, vessels and aircraft cross borders, and sanctions lists are global. The section [Fontes Internacionais com Cobertura do Brasil](README.md#fontes-internacionais) lists international databases and tools that return meaningful results for Brazilian people, companies and infrastructure, including:

- **Companies and offshore structures:** corporate registries aggregators, leaked offshore records published by journalists, legal entity identifiers.
- **Sanctions and wanted lists:** consolidated sanctions, international debarment lists and wanted notices.
- **Transport and trade:** flight and vessel tracking, fishing activity, trade statistics.
- **Domains and infrastructure:** certificate transparency, passive DNS, routing and IP reputation.
- **Archives and verification:** web archives, reverse image search, fact-check aggregators.
- **Satellite imagery and geolocation:** free imagery browsers, fire alerts, street-level imagery.
- **Latin America:** registries and investigative outlets in neighboring countries, useful for border and Mercosur cases.

---

## Practical tips for investigating Brazil

> [!TIP]
> - **Search in Portuguese.** Use the glossary above and remember accents: `certidão`, `processo`, `licitação`. Most search engines handle both accented and unaccented spellings, but government search boxes often do not.
> - **Use domain operators.** `site:jus.br "full name"` finds court documents, `site:gov.br` official pages and `site:in.gov.br` the federal gazette. See the [dorks section](README.md#dorks) for ready-made queries.
> - **Expect gov.br logins.** Many federal services require a gov.br account, which in turn requires a CPF. Public lookups (company data, court cases, transparency portals) usually do not.
> - **Expect CAPTCHAs and bot blocking.** Government sites often return 403 or 503 to scripts and some block foreign IP addresses. Check in a regular browser before assuming a link is dead.
> - **Cross-check everything.** Public records can be outdated or inconsistent between levels of government. Always note the date of the record and confirm with a second source.
> - **Prefer bulk data for scale.** For large analyses, use the open datasets and APIs (CNPJ dumps, TSE repository, transparency APIs) instead of scraping search forms.

---

## Structured dataset (JSON)

Besides the Markdown catalog, the [`data/`](data/) folder publishes a structured JSON version, generated automatically from [README.md](README.md). It lets you find sources by **input type** (CPF, CNPJ, plate, domain, phone...) and by **output type** (company data, lawsuits, sanctions, vehicle data...).

| File | Content |
|---|---|
| [`data/sources.json`](data/sources.json) | One record per source, with its links grouped. Canonical file. |
| [`data/index.json`](data/index.json) | One record per link, flattened and ready for search. |
| [`data/taxonomy.json`](data/taxonomy.json) | Controlled vocabulary for input, output and source type. |
| [`data/overrides.json`](data/overrides.json) | Manual classification fixes. |

Examples with [`jq`](https://jqlang.org/):

```bash
# Every source that accepts a license plate
jq -r '.sources[] | select(.input | index("placa")) | "\(.nome)\t\(.links[0].url)"' data/sources.json

# Every link from the state of Bahia
jq -r '.links[] | select(.uf == "BA") | "\(.fonte)\t\(.url)"' data/index.json

# Every international source
jq -r '.sources[] | select(.tipo_fonte == "internacional") | .nome' data/sources.json
```

To regenerate the dataset after editing the README (Python 3, no dependencies):

```bash
python3 tools/build_dataset.py
```

---

## Contributing

Contributions are welcome, in Portuguese or English. The full guide is in [CONTRIBUICAO.md](CONTRIBUICAO.md); in short:

1. **Report broken links** by opening an issue titled `[LINK QUEBRADO] Source name` with the URL, the date you tested it and the error.
2. **Add new sources** to [README.md](README.md) following the existing format: a `###` heading, a short objective description and the links. Sources must be public, legal and relevant to Brazil.
3. **Regenerate the dataset** with `python3 tools/build_dataset.py` and commit `data/sources.json` and `data/index.json` together with your change.
4. **Run the checks** with `python3 tools/validar_docs.py`, or enable the pre-commit hook once with `git config core.hooksPath tools/hooks`.

> [!CAUTION]
> Pull requests with affiliate links, spam, fraud forums, exploits, leaked databases, discriminatory content or paid tools without a free tier are rejected.

---

## Authors and credits

- **Cleiton P. (a.k.a MrCl0wnLab)** - [Twitter](https://twitter.com/MrCl0wnLab), [GitHub](https://github.com/MrCl0wnLab), [LinkedIn](https://www.linkedin.com/in/cleiton-p-80818b255/)
- **Diego (a.k.a c4nh0t0)** - [Twitter](https://twitter.com/C4nh0t0GH), [GitHub](https://github.com/c4nh0t0)

Thanks to every public institution and private initiative that makes these lookups available, and to everyone who has shared links and search tricks with the community.

<a href="https://github.com/osintbrazuca/osint-brazuca/graphs/contributors">
  <img src="https://contributors-img.web.app/image?repo=osintbrazuca/osint-brazuca&max=500" alt="Contributors" width="100%"/>
</a>

---

<div align="center">

**⭐ If this project helped you, consider giving it a star!**

**💀 Hacker Hackeia!**

</div>
