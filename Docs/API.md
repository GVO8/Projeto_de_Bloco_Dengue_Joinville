# Documentação da API (FastAPI)

**Iniciar** (na raiz do projeto, com o ambiente ativo):

```bash
python -m uvicorn main:app --app-dir Code/api --port 8000
```

Swagger interativo: http://127.0.0.1:8000/docs · Esquema OpenAPI: `/openapi.json`

A API não tem autenticação (uso local). Os dados vêm da API pública do InfoDengue (ou da amostra local) somados às linhas enviadas por `POST`, que ficam salvas em `Data/Processed/infodengue_uploads.csv`.

## Rotas

### `GET /health`
Verifica se a API está no ar e de onde vêm os dados (`api` pública do InfoDengue ou `amostra_local`).
```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","origem_dados_infodengue":"api"}
```

### `GET /infodengue`
Consulta a série semanal (base + dados enviados).

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `se_inicio` | int (opcional) | SE inicial, inclusiva (AAAASS) |
| `se_fim` | int (opcional) | SE final, inclusiva |
| `nivel` | int, repetível (opcional) | Níveis 1–4. Ex.: `?nivel=3&nivel=4` |

```bash
curl "http://127.0.0.1:8000/infodengue?se_inicio=202610&se_fim=202620&nivel=3&nivel=4"
# {"origem":"api","total":3,"dados":[{"id":...,"SE":202618,"nivel":3,...}]}
```

### `POST /infodengue`
Envia novas linhas. Corpo: lista de objetos com `id`, `SE`, `nivel` (1–4) e, opcionalmente, `casos` e campos extras. Se o `id` já existir, a linha **original** é mantida.
```bash
curl -X POST http://127.0.0.1:8000/infodengue \
  -H "Content-Type: application/json" \
  -d '[{"id":"u1","SE":202650,"nivel":3,"casos":10}]'
# {"adicionadas":1,"ignoradas_por_id_repetido":0,"total":53}
```
Erros: `422` se `nivel` estiver fora de 1–4, faltar campo obrigatório ou a lista for vazia.

### `GET /noticias`
Lista as notícias coletadas por scraping.

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `busca` | texto (opcional) | Filtra por trecho no título |
| `limit` | int, 1–200 (padrão 20) | Máximo de notícias |

```bash
curl "http://127.0.0.1:8000/noticias?busca=joinville&limit=5"
# {"total":3,"noticias":[{"id":1,"titulo":"...","data_publicacao":"...","autor":"...","url":"...","resumo":"..."}]}
```

## Como o app usa a API
`Code/utils/data_service.py` chama estas rotas; se a API não responder, usa a mesma lógica localmente (`data_ops.py`). A página **Explorar a API** permite testar os `GET` pela interface.
