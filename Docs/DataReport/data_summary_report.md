# Data Summary Report (versão final — TP2) — Dengue em Múltiplas Dimensões

## 1. Visão geral

Este relatório lista todas as fontes de dados do projeto — todas **públicas
e gratuitas** — indicando quais já estão **implementadas tecnicamente** no
app (TP2) e quais permanecem **documentadas como fontes futuras**.

| Fonte | Status no TP2 |
|---|---|
| SINAN/DATASUS | Documentada + amostra ilustrativa carregada no app |
| InfoDengue (API) | **Implementada** — consumo real via API, com fallback local |
| NSC Total (web scraping) | **Implementada** — script de coleta + integração no app |
| Copernicus (clima) | Documentada, integração futura |
| Google Earth Engine (sensoriamento remoto) | Documentada, integração futura |
| IBGE (população) | Documentada, integração futura |

## 2. Fontes de dados

### 2.1 SINAN — Sistema de Informação de Agravos de Notificação

| Campo | Descrição |
|---|---|
| **Órgão responsável** | Ministério da Saúde / DATASUS |
| **Tipo de dado** | Epidemiológico — notificações individuais de casos de dengue |
| **Formato** | DBC/CSV (Tabnet, OpenDataSUS) |
| **Granularidade** | Município (Joinville/SC) |
| **Acesso** | http://tabnet.datasus.gov.br/ · https://opendatasus.saude.gov.br/ |
| **Objetivo de uso** | Contexto epidemiológico de base, complementar ao InfoDengue |
| **Status no TP2** | Amostra ilustrativa em `Data/Raw/sinan_sample.csv` |

### 2.2 InfoDengue — API pública de alerta de dengue

| Campo | Descrição |
|---|---|
| **Órgão responsável** | PROCC/Fiocruz + FGV EMAp |
| **Tipo de dado** | Série epidemiológica semanal por município: casos, nível de alerta (1–4), Rt, entre outros |
| **Formato** | API REST, retorno em CSV |
| **Endpoint usado** | `https://info.dengue.mat.br/api/alertcity?geocode=4209102&disease=dengue&format=csv&ew_start=1&ew_end=52&ey_start=2026&ey_end=2026` |
| **Granularidade** | Município (geocode 4209102 = Joinville/SC), semanal |
| **Objetivo de uso** | Gráfico de linha temporal por nível de alerta (SE 1 a 52, ano 2026) |
| **Status no TP2** | **Implementado** em `Code/utils/infodengue_api.py`, consumido com cache (`st.cache_data`) na aba "Painel InfoDengue" |
| **Restrições/observações** | Requer conexão com a internet; o app usa um fallback local (`Data/Raw/infodengue_sample.csv`) quando a API está indisponível, para não quebrar a demo |

### 2.3 NSC Total — Notícias públicas (Web Scraping)

| Campo | Descrição |
|---|---|
| **Fonte** | https://www.nsctotal.com.br/tag/dengue |
| **Tipo de dado** | Textual — notícias jornalísticas públicas |
| **Formato** | HTML, extraído via BeautifulSoup |
| **Critério de seleção** | Notícias da tag "dengue" cujo título também contenha "Joinville" |
| **Ferramenta** | `requests` + `beautifulsoup4`, script `Code/scraping/scrape_nsc_dengue.py` (executado separadamente do app, conforme orientação do enunciado) |
| **Saída** | `Data/Raw/nsc_noticias_joinville_dengue.csv` (metadados: id, título, data, autor, url, resumo) e `Data/Raw/nsc_noticias_texto.txt` (corpo completo, para nuvem de palavras) |
| **Objetivo de uso** | Contexto qualitativo/textual: nuvem de palavras e estatísticas básicas (nº de notícias, autores) na aba "Notícias" do app |
| **Restrições/observações** | Depende da estrutura HTML do site (mitigado com seletores baseados em padrões estáveis — cabeçalhos e meta tags); frequência de execução deve respeitar os termos de uso do site (delay entre requisições implementado no script) |

### 2.4 Copernicus — Dados Climáticos por Satélite (fonte futura)

| Campo | Descrição |
|---|---|
| **Tipo de dado** | Climático — temperatura, precipitação |
| **Formato** | API pública |
| **Objetivo de uso previsto** | Dimensão climática associada a janelas favoráveis à proliferação do vetor |
| **Status no TP2** | Documentada, não implementada |

### 2.5 Google Earth Engine (Sentinel-2/Landsat) — Sensoriamento Remoto (fonte futura)

| Campo | Descrição |
|---|---|
| **Tipo de dado** | Índices espectrais de satélite (NDVI, área impermeabilizada) |
| **Formato** | API / plataforma de processamento em nuvem |
| **Objetivo de uso previsto** | Dimensão ambiental territorial |
| **Status no TP2** | Documentada, não implementada |

### 2.6 IBGE — Censo / Malha Territorial (fonte futura)

| Campo | Descrição |
|---|---|
| **Tipo de dado** | Densidade populacional, malha de bairros/setores censitários |
| **Formato** | API IBGE / shapefiles públicos |
| **Objetivo de uso previsto** | Dimensão populacional, contextualização de exposição |
| **Status no TP2** | Documentada, não implementada |

## 3. Estrutura de dados no app (TP2)

| Arquivo | Origem | Uso no app |
|---|---|---|
| `Data/Raw/sinan_sample.csv` | Amostra ilustrativa (TP1) | Aba "Dados e Upload" |
| `Data/Raw/infodengue_sample.csv` | Fallback local, mesmo schema da API | Usado apenas se a API estiver indisponível |
| `Data/Raw/nsc_noticias_joinville_dengue.csv` | Web scraping (NSC Total) | Aba "Notícias" — tabela |
| `Data/Raw/nsc_noticias_texto.txt` | Web scraping (NSC Total) | Aba "Notícias" — nuvem de palavras |
| CSV enviado pelo usuário (upload) | Usuário, mesmo formato da API InfoDengue | Mesclado por `id` ao `st.session_state["infodengue_df"]` |

## 4. Regra de mesclagem de dados (upload)

Ao enviar um CSV no mesmo formato da API do InfoDengue (contendo a coluna
`id`), o app concatena esse CSV com os dados já carregados e remove
duplicatas por `id`, **mantendo a linha original** já existente na base
(a linha nova do upload é descartada em caso de conflito de `id`). Essa
lógica está implementada e testada em `Code/app/app.py` (função
`mesclar_upload`).

## 5. Próximos passos

- Integrar extração real via API do Google Earth Engine (NDVI, impermeabilização).
- Integrar API pública do Copernicus para série climática de Joinville.
- Integrar API do IBGE para densidade populacional por setor censitário.
- Ampliar o scraper para cobrir mais páginas/fontes de notícias, se necessário.
- Avaliar granularidade do SINAN por bairro via microdado bruto.
