# Documentação da API (FastAPI)

**Iniciar** (raiz do projeto, ambiente ativo): `python Code/run_api.py` · Swagger: http://127.0.0.1:8000/docs · OpenAPI: `/openapi.json`
Sem autenticação (uso local). Dados da série: API pública do InfoDengue (ou amostra local) + linhas enviadas por `POST`.

## Formato de erro (todas as rotas)

```json
{"codigo": "modelo_indisponivel", "categoria": "ia", "mensagem": "Houve um problema com a IA (modelo …): …",
 "sugestao": "Rode uma vez, com internet: python Code/cli.py baixar-modelo …", "detalhe": "…"}
```
`categoria`: `entrada` · `dados` · `ia` · `sistema`. Erros inesperados devolvem 500 com um código de protocolo (também no log), sem detalhes internos.

## Rotas

| Método | Rota | Função |
|---|---|---|
| GET | `/health` | API no ar + estado do modelo de IA (pronto? carregado?) |
| GET | `/operacoes` | Operações de IA e se exigem pergunta |
| GET | `/infodengue` | Série semanal. Filtros: `se_inicio`, `se_fim`, `nivel` (repetível) |
| POST | `/infodengue` | Envia linhas (`id`, `SE`, `nivel` 1–4, `casos` opcional, extras aceitos). `id` repetido: mantém o original |
| DELETE | `/infodengue/uploads` | Descarta as linhas enviadas (204) |
| GET | `/noticias` | Lista notícias. Filtros: `busca`, `limit` (1–200) |
| GET | `/noticias/{id}` | Uma notícia (404 se não existir) |
| GET | `/noticias/texto` | Texto limpo de todas as notícias (nuvem de palavras) |
| POST | `/noticias/{id}/processar` | **Processa a notícia com a IA local** |

## `POST /noticias/{noticia_id}/processar`

Busca a notícia inteira no corpus, monta o prompt da operação e devolve a resposta do modelo.

**Corpo:** `{"operacao": "resumo" | "sentimento" | "qa" | "relatorio", "pergunta": "texto (obrigatória só em qa, até 500 caracteres)"}`

```bash
curl -X POST http://127.0.0.1:8000/noticias/3/processar -H "Content-Type: application/json" -d '{"operacao":"resumo"}'
curl -X POST http://127.0.0.1:8000/noticias/3/processar -H "Content-Type: application/json" -d '{"operacao":"qa","pergunta":"Quantas mortes houve em 2024?"}'
```

**Resposta 200** (ordem dos campos = ordem de exibição):

| Campo | Conteúdo |
|---|---|
| `noticia_id`, `titulo` | A notícia processada |
| `operacao`, `nome_operacao` | Ex.: `resumo`, "Resumo automático de notícia" |
| `resultado` | Texto gerado pelo modelo |
| `resumo_final` | Sentimento: `Sentimento: POSITIVO/NEGATIVO/NEUTRO`; demais: primeira frase do resultado |
| `avisos` | Ex.: texto truncado; números do InfoDengue são dados de exemplo (sintéticos) |
| `aviso_padrao` | "Este conteúdo foi gerado por um modelo de IA e pode conter erros…" |
| `modelo`, `tempo_segundos` | Modelo usado e duração |
| `markdown` | Resposta completa formatada: título → operação → resultado → resumo final → avisos → aviso padrão |

**Erros:** `404` notícia inexistente · `422` operação/corpo inválido ou pergunta ausente · `429` IA ocupada · `502` falha do modelo/resposta vazia · `503` modelo indisponível (não baixado, biblioteca ausente, sem memória) ou corpus não preparado · `504` tempo limite da IA.

> Em computador sem placa de vídeo compatível, uma resposta pode levar **de 1 a 3 minutos** (estimativa). Chamadas simultâneas esperam a vez; se a espera passar do limite, retornam 429.

## Como o app usa a API
`ui_streamlit/gateways.py`: `ApiGateway` (HTTP) com alternativa local (`LocalGateway`) para dados e notícias quando a API está fora do ar. **O processamento por IA exige a API** (o modelo não é carregado dentro do processo da interface).
