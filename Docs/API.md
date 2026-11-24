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
| POST | `/chat` | **Pergunta em linguagem natural sobre casos de dengue em Joinville** (com memória) |
| GET | `/chat/{sessao_id}` | Histórico de uma conversa |
| DELETE | `/chat/{sessao_id}` | Encerra a conversa (apaga a memória) |
| GET | `/infodengue/historico` | Série de vários anos + fatos calculados (dados reais, sem alternativa sintética) |
| GET | `/sentimentos` | Sentimento (preocupação) das notícias já analisadas |

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

**Campo `metricas`:** tempos e tokens medidos pelo modelo real (`tempo_carga_s`, `tempo_primeiro_token_s`, `tokens_gerados`, `tokens_por_s`, `tempo_total_s`); com o modelo simulado traz só `simulado: true`.

**Erros:** `404` notícia inexistente · `422` operação/corpo inválido ou pergunta ausente · `429` IA ocupada · `502` falha do modelo/resposta vazia · `503` modelo indisponível (não baixado, biblioteca ausente, sem memória) ou corpus não preparado · `504` tempo limite da IA.

> Em computador sem placa de vídeo compatível, uma resposta pode levar **de 1 a 3 minutos** (estimativa). Chamadas simultâneas esperam a vez; se a espera passar do limite, retornam 429.

## `POST /chat`

Conversa com os dados do InfoDengue. **Sempre Joinville, sempre dengue.**

**Corpo:** `{"sessao_id": "opcional (8–64 caracteres)", "pergunta": "1 a 300 caracteres"}`. Sem `sessao_id`, inicia uma conversa nova; a resposta traz o `sessao_id` para as próximas perguntas.

```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"pergunta":"Qual foi o ano com mais casos de dengue?"}'
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"sessao_id":"<id recebido>","pergunta":"e em 2024?"}'
```

**Como a pergunta vira uma resposta:**
1. *Guarda de escopo* (sem custo de IA): outra cidade, outro território, assunto sem relação com dengue ou tentativa de alterar as regras → resposta `tipo: "recusa"` (HTTP 200) com exemplos do que perguntar.
2. *Planejamento* (1ª chamada ao modelo, em modo JSON): a IA gera o plano (`intencao`, `ano_inicio`, `ano_fim`); o plano é validado e reconciliado com regras. Se o JSON for inválido, as regras assumem (`plano.origem: "regras"` e um aviso).
3. *Requisição ao InfoDengue* (`requisicao.url`, com `geocode=4209102`, `disease=dengue`, semanas 1–53).
4. *Fatos calculados em código* (`fatos`): totais por ano, pico, ranking de anos completos, comparação nas mesmas semanas.
5. *Resposta* (2ª chamada ao modelo), só a partir dos fatos e da conversa recente.

**Resposta 200:** `sessao_id`, `pergunta`, `tipo` (`resposta` | `recusa`), `resposta`, `plano`, `requisicao`, `fatos`, `etapas` (nome, tempo e tokens de cada etapa), `avisos`, `aviso_padrao`, `modelo`, `tempo_segundos`.

**Erros:** `422` pergunta vazia/longa ou identificador inválido · `404` sem dados para o período · `503` InfoDengue indisponível ou modelo indisponível · `504` tempo limite da IA · `429` IA ocupada · `502` falha do modelo. Não há dado sintético: sem o InfoDengue, a resposta é o erro.

## `GET /infodengue/historico`
Parâmetros `ano_inicio` (padrão: ano final − 3) e `ano_fim` (padrão: ano atual); válidos entre 2010 e o ano atual. Devolve `requisicao`, `fatos` (estrutura usada no dashboard) e `serie` (`SE`, `ano`, `semana`, `casos`, `nivel`, `data_iniSE`, ...).

## `GET /sentimentos`
`{"total", "por_classe", "itens": [{"noticia_id", "titulo", "classe", "rotulo", "justificativa", "modelo", "tempo_segundos", "analisado_em", "data_publicacao"}]}`. Os itens surgem quando o botão **Sentimento** é usado em uma notícia ou quando se roda `python Code/cli.py analisar-sentimentos`.

## Como o app usa a API
`ui_streamlit/gateways.py`: `ApiGateway` (HTTP) com alternativa local (`LocalGateway`) para dados e notícias quando a API está fora do ar. **O processamento por IA e a conversa exigem a API** (o modelo não é carregado dentro do processo da interface).
