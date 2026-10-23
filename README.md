# Dengue em Múltiplas Dimensões (TP3)

Painel de dados de dengue para Joinville/SC: série semanal do InfoDengue (nível de alerta), notícias coletadas por *web scraping*, **API FastAPI** para consulta/envio de dados e preparação dos dados para **LLMs** (próxima etapa). Alinhado ao ODS 3.

O projeto não envolve contato com órgãos públicos; as "partes interessadas" são hipotéticas.

## Estrutura

```
dengue-esg-tp3/
├── requirements.txt
├── Code/
│   ├── api/main.py                  # API FastAPI (4 rotas)
│   ├── app/
│   │   ├── app.py                   # Entrada do app + menu de navegação
│   │   ├── common.py                # Cache e componentes compartilhados
│   │   └── views/                   # Páginas: inicio, painel, noticias, upload, api_page, llm
│   ├── scraping/scrape_nsc_dengue.py
│   ├── llm_prep/                    # prepare_corpus.py + prompts.py
│   └── utils/                       # infodengue_api.py, data_ops.py, data_service.py
├── Data/
│   ├── Raw/                         # CSV/TXT coletados + amostras
│   └── Processed/                   # corpus .jsonl, contexto .json, uploads
└── Docs/
    ├── API.md
    ├── Project/                     # project_charter.md, llm_readiness.md, tdsp_crispdm_mapping.md
    └── DataReport/                  # data_summary_report.md
```

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell)  |  Mac/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Como os dados chegam ao app (leia antes de executar)

Existem **duas APIs** no projeto, com papéis diferentes:

| | O que é | Você precisa fazer algo? |
|---|---|---|
| **API do InfoDengue** | Fonte pública dos dados (internet) | **Não.** O código (`Code/utils/infodengue_api.py`) a consulta sozinho ao abrir o app. Sem internet, usa uma amostra local e avisa na tela. |
| **API FastAPI do projeto** | Camada opcional que entrega os mesmos dados por rotas HTTP (`/infodengue`, `/noticias`) | **Só se quiser usá-la:** ligue-a em um terminal separado (comando abaixo). |

```
InfoDengue (internet) --> dados --> [FastAPI, opcional] --> Streamlit
                                  \_______ (sem API) _______/
```

- **Nenhum script precisa ser criado** para buscar dados da API.
- O único script rodado à parte é o **scraper de notícias** (`scrape_nsc_dengue.py`), que apenas atualiza as notícias.
- Com a FastAPI ligada, as páginas mostram "🟢 Dados obtidos pela API FastAPI"; desligada, "🟡 leitura local". Os dados são os mesmos; só o caminho muda.
- Para a entrega do TP3, mostre o app com a FastAPI ligada e abra http://127.0.0.1:8000/docs.

## Execução

Todos os comandos na **raiz do projeto**, com o ambiente ativo.

```bash
# 1) (opcional) coletar notícias atualizadas — precisa de internet
python Code/scraping/scrape_nsc_dengue.py

# 2) (opcional) regenerar o corpus e o contexto para LLM
python Code/llm_prep/prepare_corpus.py

# 3) API — terminal 1 (opcional: o app funciona sem ela)
python -m uvicorn main:app --app-dir Code/api --port 8000

# 4) App — terminal 2
python -m streamlit run Code/app/app.py
```

- Swagger da API: http://127.0.0.1:8000/docs (rotas em [`Docs/API.md`](Docs/API.md))
- O app mostra, em cada página, se os dados vieram da **API** ou de **leitura local**.
- Sem internet, o app usa uma amostra **sintética** do InfoDengue e avisa na tela.

## Git

```bash
git init
git add .
git commit -m "TP3: app multipágina, API FastAPI, preparação para LLM"
git remote add origin <URL_DO_REPOSITORIO>
git branch -M main
git push -u origin main
```

## Documentação
[Project Charter](Docs/Project/project_charter.md) · [Data Summary Report](Docs/DataReport/data_summary_report.md) · [API](Docs/API.md) · [Prontidão para LLM](Docs/Project/llm_readiness.md) · [CRISP-DM × TDSP](Docs/Project/tdsp_crispdm_mapping.md)
