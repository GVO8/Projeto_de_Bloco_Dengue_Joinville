# Project Charter — Dengue em Múltiplas Dimensões (Joinville/SC)

**Versão TP3 · Projeto de IA Generativa e ESG · Ciência de Dados**
Histórico: TP1 (proposta) → TP2 (interface dinâmica, scraping, API InfoDengue, upload/download) → **TP3 (multipáginas, FastAPI, preparação para LLM)**.

---

## 1. Contexto e Justificativa

Joinville (SC) está numa região historicamente pouco afetada por dengue, mas o aumento das temperaturas e a expansão do *Aedes aegypti* para o Sul do Brasil a tornam vulnerável a surtos. Sistemas de alerta baseados em notificação (como o InfoDengue) já são referência; este projeto **não os replica**: usa-os como uma das dimensões de um painel mais amplo, que também reúne conteúdo textual de notícias públicas e, em etapas futuras, clima, satélite e população.

## 2. Problema de Negócio (reavaliado no TP3)

**Como reunir, num único painel interativo e acessível por API, indicadores públicos de dengue para Joinville/SC — série epidemiológica semanal, notícias recentes e, futuramente, clima, satélite e densidade populacional — de forma que partes interessadas e outras aplicações consumam esses dados e, na próxima etapa, recebam resumos e respostas geradas por LLM?**

**O que mudou em relação ao TP2 à luz das novas ferramentas:**
- A **FastAPI** transforma o projeto de "um app" em "uma plataforma de dados": o mesmo conjunto de dados passa a ser consumível por outros sistemas (rotas GET/POST), não apenas pela interface.
- O **objetivo de preparar os dados para LLM** passa a ser explícito: o painel deixa de ser apenas visualização e passa a produzir um corpus e contexto numérico prontos para resumo, classificação, Q&A e geração de relatório.
- Metas e KPIs foram atualizados (seção 4). O escopo de dimensões (SINAN, Copernicus, GEE, IBGE) **não mudou**: continuam documentadas como fontes futuras.

## 3. Pilar ESG e ODS

| Pilar ESG | Conexão |
|---|---|
| **Social (S)** | Saúde pública, prevenção de doença negligenciada |
| **Governança (G)** | Transparência e acessibilidade de dados públicos (agora inclusive por API) |

- **ODS 3** (Saúde e Bem-Estar), meta 3.3 — principal.
- **ODS 11** (Cidades e Comunidades Sustentáveis) — leitura territorial de indicadores.
- **ODS 17** (Parcerias e Meios de Implementação) — uso exclusivo de dados abertos e interface programática para reuso.

## 4. Metas e Indicadores (KPIs) — atualizados no TP3

| Meta | Indicador | Status ao fim do TP3 |
|---|---|---|
| Consolidar fontes públicas num só painel | Dimensões integradas tecnicamente | InfoDengue (API) + notícias (scraping); SINAN em amostra; demais documentadas |
| Interface multipágina | Nº de páginas navegáveis | 6 páginas com menu de navegação |
| Acesso programático aos dados | Nº de endpoints documentados | 4 (`GET /health`, `GET /infodengue`, `POST /infodengue`, `GET /noticias`) |
| Robustez | App funciona sem a API no ar | Sim (leitura local como alternativa) |
| Prontidão para LLM | Artefatos de preparação | Corpus em trechos (`.jsonl`), contexto numérico (`.json`), 4 templates de prompt |
| Transparência das fontes | Fontes documentadas | Todas, no Data Summary Report |
| Uso exclusivo de dados abertos | Fontes pagas/restritas | 0 |

## 5. Público-Alvo (fictício)

Perfis hipotéticos, sem contato real com instituições, apenas para orientar o design:
- **Primário:** gestores de vigilância em saúde de um município como Joinville.
- **Secundário:** moradores interessados em entender a situação local.
- **Terciário:** estudantes, pesquisadores e **outras aplicações** que consumam a API.

> **Nota de escopo:** o projeto não envolve contato, parceria ou validação com a Prefeitura de Joinville ou qualquer órgão público.

## 6. Escopo do TP3

**Entregue:**
- Aplicação Streamlit **multipágina** com menu de navegação (`st.navigation`): Início, Painel InfoDengue, Notícias, Upload e Download, Explorar a API, Preparação para LLM.
- **API FastAPI** (`Code/api/main.py`) com 4 rotas, validação de dados (Pydantic) e documentação Swagger automática.
- Integração app ↔ API com **alternativa local** quando a API está desligada.
- Persistência dos dados enviados em `Data/Processed/`, compartilhada por API e app.
- Preparação para LLM: `Code/llm_prep/` (corpus, contexto numérico, prompts versionados) e página dedicada no app.
- Revisão deste Charter, do Data Summary Report; novos `Docs/API.md` e `Docs/Project/llm_readiness.md`.

**Fora do escopo:** contato com órgãos públicos; modelo preditivo; **chamadas reais a LLMs** (próxima etapa); integração real de Copernicus, Google Earth Engine e IBGE; deploy público.

## 7. Decisão técnica: Selenium não será utilizado

O enunciado prevê Selenium "se necessário". Avaliação por fonte:

| Fonte | Natureza | Ferramenta |
|---|---|---|
| InfoDengue | API REST (CSV) | `pandas`/`requests` |
| NSC Total (`/tag/dengue`) | HTML estático renderizado no servidor, com listagem paginada por URL | `requests` + BeautifulSoup |

Nenhuma exige interação com formulários ou carregamento assíncrono. Selenium acrescentaria dependência de navegador e driver, mais lentidão e fragilidade de setup, sem ganho de dados. **A decisão será reavaliada** se uma fonte futura (ex.: um portal que só carregue dados via JavaScript) exigir.

## 8. Metodologia e Ambiente

- **CRISP-DM** (ciclo analítico) + **TDSP** (artefatos, diretórios, papéis) — ver `Docs/Project/tdsp_crispdm_mapping.md`.
- Ambiente: `venv` + `requirements.txt` (versões mínimas); Git/GitHub para versionamento.
- Execução: API (`uvicorn`) e app (`streamlit`) em processos separados; ver README.

## 9. Stakeholders (papéis do projeto, não instituições reais)

| Papel | Responsável |
|---|---|
| Product Owner / Solicitante | Disciplina de IA Generativa e ESG |
| Equipe de execução | Aluno(s) de Ciência de Dados |
| Orientador acadêmico | Professor(a) da disciplina |
| Parte interessada (fictícia) | Perfil de gestor de saúde pública |
| Fontes oficiais (públicas, sem contato direto) | InfoDengue, NSC Total, SINAN/DATASUS, Copernicus, GEE, IBGE |

## 10. Riscos

- O HTML do NSC Total pode mudar e quebrar o scraper (mitigação: seletores baseados em cabeçalhos e meta tags, não em classes CSS).
- API do InfoDengue indisponível (mitigação: amostra local no mesmo schema; o app informa a origem dos dados).
- A API e o app compartilham arquivos em disco: adequado para este porte, mas não para múltiplos usuários simultâneos (fora do escopo; em produção seria um banco de dados).
- A API não tem autenticação: aceitável localmente; necessária antes de qualquer exposição pública.
- Dados em LLM: respostas devem ser ancoradas no corpus (templates de Q&A já instruem "somente o contexto") para reduzir alucinação.
- Granularidade municipal do InfoDengue/SINAN; correlações ambientais sem validação estatística (fora de escopo).

## 11. Cronograma

| Fase | Entrega |
|---|---|
| TP1 | Proposta, planejamento e demo básica |
| TP2 | Interface dinâmica, scraping (BeautifulSoup), API InfoDengue, cache/sessão, upload/download |
| **TP3 (atual)** | Multipáginas, FastAPI, preparação para LLM, documentação revisada |
| Próxima etapa | Integração de LLMs (resumo, sentimento, Q&A, relatório) sobre o corpus preparado |
