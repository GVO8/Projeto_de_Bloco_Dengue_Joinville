# Data Summary Report (versão TP4) — Dengue em Múltiplas Dimensões

## 1. Visão geral

Todas as fontes são **públicas e gratuitas**. A tabela indica o que está implementado e o que permanece documentado para etapas futuras.

| Fonte | Status no TP3 | Mudança desde o TP2 |
|---|---|---|
| InfoDengue (API) | **Implementada** | Agora também exposta pela API FastAPI do projeto |
| NSC Total (scraping, BeautifulSoup) | **Implementada** | Agora também exposta pela API e convertida em corpus para LLM |
| SINAN/DATASUS | Documentada, amostra ilustrativa | — |
| Copernicus (clima) | Documentada, futura | — |
| Google Earth Engine (satélite) | Documentada, futura | — |
| IBGE (população) | Documentada, futura | — |
| Páginas dinâmicas (Selenium) | **Não utilizado** — nenhuma fonte exige | Decisão documentada no Charter |
| Modelo de linguagem (Qwen3-4B-Instruct-2507, GGUF) | **Implementado** (artefato, não é fonte de dados) | Novo no TP4; baixado em `Models/` (não versionado) |

> **Sobre as amostras:** `infodengue_sample.csv` é **sintética** (gerada para o app funcionar sem internet; só é usada quando a API pública está inacessível — o app informa isso). `nsc_noticias_*` e `sinan_sample.csv` são amostras pequenas de demonstração; rode o scraper localmente para substituí-las por dados reais.

## 2. Fontes

### 2.1 InfoDengue — API pública
| Campo | Descrição |
|---|---|
| Órgão | PROCC/Fiocruz + FGV EMAp |
| Tipo | Série epidemiológica semanal por município (casos, nível de alerta 1–4, Rt, entre outros) |
| Endpoint | `https://info.dengue.mat.br/api/alertcity?geocode=4209102&disease=dengue&format=csv&ew_start=1&ew_end=52&ey_start=2026&ey_end=2026` |
| Granularidade | Município (Joinville = 4209102), semanal |
| Uso | Gráfico por nível de alerta; contexto numérico para LLM |
| Código | `Code/utils/infodengue_api.py` |
| Observações | O campo `id` é numérico na API real; o projeto o normaliza como texto para a deduplicação |

### 2.2 NSC Total — notícias (web scraping)
| Campo | Descrição |
|---|---|
| Fonte | https://www.nsctotal.com.br/tag/dengue (páginas `/page/N`) |
| Tipo | Textual (HTML estático) |
| Critério | Notícias da tag "dengue" com "Joinville" no título |
| Ferramenta | `requests` + BeautifulSoup — `Code/scraping/scrape_nsc_dengue.py` |
| Saídas | `Data/Raw/nsc_noticias_joinville_dengue.csv`, `Data/Raw/nsc_noticias_texto.txt` |
| Uso | Tabela, nuvem de palavras, estatísticas; corpus para LLM |
| Restrições | Depende da estrutura do site; script usa pausa entre requisições |

### 2.3 SINAN/DATASUS — epidemiológico (amostra)
Notificações de dengue, granularidade municipal. `Data/Raw/sinan_sample.csv` (ilustrativa). Acesso: Tabnet / OpenDataSUS.

### 2.4 a 2.6 Copernicus, Google Earth Engine, IBGE — fontes futuras
Clima (temperatura/precipitação), índices de satélite (NDVI, impermeabilização) e densidade populacional. Documentadas; integração prevista para etapas futuras.

## 3. Arquivos de dados

| Arquivo | Origem | Gerado por | Uso |
|---|---|---|---|
| `Data/Raw/infodengue_sample.csv` | Sintético, schema do InfoDengue | manual | Alternativa offline |
| `Data/Raw/nsc_noticias_joinville_dengue.csv` | Scraping | `scrape_nsc_dengue.py` | Notícias (app, API, corpus) |
| `Data/Raw/nsc_noticias_texto.txt` | Scraping | `scrape_nsc_dengue.py` | Nuvem de palavras, corpus |
| `Data/Raw/sinan_sample.csv` | Amostra ilustrativa | manual | Referência de schema |
| `Data/Processed/infodengue_uploads.csv` | Usuário (upload ou POST) | app / API | Linhas adicionadas à base (não versionado) |
| `Data/Processed/noticias_corpus.jsonl` | Derivado (texto **limpo**) | `python Code/cli.py gerar-corpus` ou automaticamente pela API | Entrada de LLM |
| `Data/Processed/contexto_infodengue.json` | Derivado | idem | Contexto numérico para LLM |
| `Models/*.gguf` | Hugging Face (`unsloth/Qwen3-4B-Instruct-2507-GGUF`, 2,5 GB) | `python Code/cli.py baixar-modelo` | Modelo de IA local (não versionado) |

## 4. Schemas

**Série InfoDengue (mínimo exigido em upload/POST):**

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | texto/número | Identificador único (chave de mesclagem) |
| `SE` | inteiro | Semana epidemiológica AAAASS (ex.: 202614) |
| `nivel` | inteiro 1–4 | 1 verde, 2 amarelo, 3 laranja, 4 vermelho |
| `casos` | inteiro (opcional) | Casos notificados |
| demais colunas | livres | Aceitas e preservadas (ex.: `Rt`, `casos_est`) |

**Corpus (`noticias_corpus.jsonl`, uma linha por trecho):** `id_noticia`, `chunk_id`, `titulo`, `texto` (até 800 caracteres) e, repetidos em todos os trechos da notícia, `data_publicacao`, `autor`, `url`, `resumo`. A "notícia inteira" é a junção dos trechos por `chunk_id`.

**Limpeza aplicada ao texto raspado (TP4):** o HTML do NSC Total traz, junto do corpo, rodapé de copyright, aviso de cookies, convite a colunistas, legendas de foto, o título repetido e **manchetes de outras matérias** (ex.: "Cidade litorânea de SC leiloa terrenos…"). Esse ruído levaria a IA a resumir assuntos alheios. Regras (`core/domain/texto.py`): remover linhas com padrões de rodapé/menu/legenda, remover o título duplicado e descartar linhas curtas (< 140 caracteres) que não terminam em pontuação. Efeito nos 6 artigos coletados: nenhum dos ruídos de teste permanece no corpus (32 trechos).

**Observação de qualidade:** o corpus é **reconstruído** quando não existe ou não cobre a notícia pedida (ex.: após uma nova coleta), evitando respostas com dados desatualizados. O `contexto_infodengue.json` marca `origem_dados`; quando é `amostra_local` (dados **sintéticos**), a resposta da IA que usa números traz o aviso correspondente.

**Contexto (`contexto_infodengue.json`):** município, origem dos dados, nº de semanas, semanas por nível, total de casos e semana de pico.

## 5. Regra de mesclagem

Em upload ou `POST /infodengue`, as linhas são concatenadas à base e deduplicadas por `id` (comparado como texto), **mantendo a linha original**; a enviada é descartada. A API informa quantas foram adicionadas e quantas ignoradas. Implementação única em `Code/utils/data_ops.py`.

## 6. Próximos passos
- Substituir amostras por coleta real (rodar o scraper; usar a API do InfoDengue com internet).
- Integrar Copernicus, Google Earth Engine e IBGE.
- Usar o corpus e o contexto como entrada dos LLMs na próxima etapa.
