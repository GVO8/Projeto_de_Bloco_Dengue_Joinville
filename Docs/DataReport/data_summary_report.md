# Data Summary Report — versão final (TP5)

Este relatório descreve as fontes, como foram coletadas, preparadas e integradas, e como chegam ao dashboard e à IA. O ciclo completo está resumido na seção 1.

## 1. Visão geral do ciclo de dados

```
 COLETA                    PREPARAÇÃO                    IA LOCAL (Qwen3-4B)             INSIGHT
 InfoDengue (API) ───────► série semanal ──► fatos calculados em código ──► redação ──► respostas e gráficos
                                      (totais, picos, comparação)       ▲
                                                                        │ interpreta a pergunta (plano JSON)
 NSC Total (scraping) ───► limpeza do texto ──► corpus em trechos ──► sentimento por notícia ──► gráfico de mídia
```

| Fonte | Status | Como entra no projeto |
|---|---|---|
| **InfoDengue** (API pública) | Implementada | Série semanal de Joinville → painel, fatos e conversa |
| **NSC Total** (web scraping) | Implementada | Notícias → limpeza → corpus → sentimento/resumo/perguntas |

Não há outras fontes. O InfoDengue já consolida notificações do SINAN, dados climáticos e estimativas populacionais do IBGE; o projeto usa apenas o que o InfoDengue publica.

## 2. Fonte 1 — InfoDengue

| Campo | Descrição |
|---|---|
| Responsáveis | PROCC/Fiocruz e FGV EMAp |
| Endpoint | `https://info.dengue.mat.br/api/alertcity` |
| Parâmetros usados | `geocode=4209102` (Joinville), `disease=dengue`, `format=csv`, `ew_start=1`, `ew_end=53`, `ey_start`/`ey_end` (anos pedidos) |
| Granularidade | Município, semanal (semana epidemiológica, `SE` = AAAASS) |
| Código | `adapters/outbound/infodengue.py` (`ConsultaInfoDengueHttp`, com cache de 15 min) |

### Colunas usadas

| Coluna | Uso |
|---|---|
| `SE` | Ano (`SE // 100`) e semana (`SE % 100`) |
| `casos` | **Casos notificados na semana**: base de todos os cálculos (totais, picos, comparações) |
| `nivel` | Nível de alerta (1 verde · 2 amarelo · 3 laranja · 4 vermelho): gráficos de alerta |
| `data_iniSE` | Data de início da semana: "quando" foi o pico e linha do tempo da mídia |
| `id` | Chave de mesclagem (upload/POST); criada a partir de `SE` se ausente |
| demais (ex.: `casos_est`, `Rt`, clima) | Preservadas, mas **não usadas** nos cálculos |

### Tratamento e regras de negócio
- **Anos completos vs. em andamento.** Um ano é "completo" com 52 ou mais semanas e anterior ao ano atual. O **ranking** (mais/menos casos) só considera anos completos; comparar o total de um ano parcial com um ano inteiro seria enganoso.
- **Comparação com o ano anterior** usa **as mesmas semanas** (ex.: SE 1–40 de 2026 contra SE 1–40 de 2025).
- **Variação percentual** é omitida quando o ano anterior tem 0 casos.
- Linhas sem `casos` são descartadas; se não sobrar nada, o erro informa o período sem dados.
- **Janela histórica padrão:** 10 anos (quando a pergunta pede "todos os anos"); nenhuma consulta abaixo de 2010 nem acima do ano atual.

### Limitações
- `casos` são **notificados** e podem ser revisados; as últimas semanas são as mais incertas (as respostas avisam).
- A origem exata dos dados climáticos do InfoDengue (e seu histórico) deve ser conferida no dicionário de dados oficial do projeto; este trabalho não os utiliza diretamente.
- **Não verificado em ambiente real:** o comportamento da API para consultas de vários anos seguiu o exemplo oficial, mas foi testado apenas com respostas simuladas. Confirmar na primeira execução (`GET /infodengue/historico`).
- **Alternativa sintética:** `Data/Raw/infodengue_sample.csv` é **sintético** e serve apenas à página "Alertas de 2026" quando a API está inacessível. **Nunca** alimenta a conversa nem o dashboard.

## 3. Fonte 2 — NSC Total (web scraping)

| Campo | Descrição |
|---|---|
| URL | `https://www.nsctotal.com.br/tag/dengue` (páginas `/page/N`) |
| Critério | Notícias da tag "dengue" com "Joinville" no título |
| Ferramenta | `requests` + BeautifulSoup (`adapters/outbound/nsc_scraper.py`); executada à parte: `python Code/cli.py coletar-noticias` |
| Campos | `id`, `titulo`, `data_publicacao`, `autor`, `url`, `resumo` + texto do corpo |
| Volume atual | 6 notícias |

### Limpeza (`core/domain/texto.py`)
O HTML traz, junto do corpo, rodapé, cookies, convite a colunistas, legendas e **manchetes de outras matérias**. Sem limpeza a IA resumiria assuntos alheios. Regras: remover linhas com padrões de rodapé/menu/legenda, remover o título repetido e descartar linhas curtas (< 140 caracteres) sem pontuação final. O texto limpo é dividido em trechos de até 800 caracteres.

### Limitações
- A estrutura do site pode mudar e quebrar o coletor (usa cabeçalhos `<h2>`/`<h3>` e metatags, não classes CSS).
- Seis notícias formam uma **amostra pequena**: o gráfico de mídia é ilustrativo, não estatístico.

## 4. Dados derivados

| Arquivo | Gerado por | Conteúdo | Uso |
|---|---|---|---|
| `Data/Raw/nsc_noticias_joinville_dengue.csv` | scraper | Metadados das notícias | Lista de notícias |
| `Data/Raw/nsc_noticias_texto.txt` | scraper | Corpo bruto | Entrada da limpeza |
| `Data/Processed/noticias_corpus.jsonl` | `gerar-corpus` ou automático | Trechos **limpos** (`id_noticia`, `chunk_id`, `titulo`, `texto` + data, autor, url, resumo) | Entrada da IA |
| `Data/Processed/contexto_infodengue.json` | idem | Resumo numérico da série | Contexto do relatório e das perguntas sobre notícias |
| `Data/Processed/sentimentos_noticias.csv` | botão **Sentimento** ou `analisar-sentimentos` | Classe (POSITIVO/NEGATIVO/NEUTRO), justificativa, modelo, tempo, data | Gráficos de mídia |
| `Data/Processed/infodengue_uploads.csv` | upload ou `POST /infodengue` | Linhas adicionadas pelo usuário (não versionado) | Página "Alertas de 2026" |
| `Docs/Evidencias/medicao_*.md` | `medir-modelo` | Tempos medidos do modelo real | Relatório |

O corpus é reconstruído automaticamente quando não existe ou não cobre a notícia pedida.

## 5. Como os dados se integram

1. **Série × conversa.** A pergunta vira um **plano** (anos) e uma **requisição** ao InfoDengue; a resposta (DataFrame) passa por `calcular_fatos`; a IA redige a partir do texto dos fatos. A requisição e os fatos são exibidos ao usuário.
2. **Série × mídia.** O dashboard sobrepõe a curva semanal de casos (`data_iniSE`) às datas de publicação (`data_publicacao`) das notícias, coloridas pelo sentimento.
3. **Memória conversacional.** Os últimos 3 turnos (pergunta + resposta) entram nos prompts, para perguntas de continuação.
4. **Mesclagem de uploads.** `id` repetido mantém a linha original.

## 6. Sentimento: definição

O prompt mede a **preocupação** transmitida pela notícia: **NEGATIVO** = preocupação, risco ou piora (rótulo "Preocupante"); **POSITIVO** = alívio, melhora ou controle ("Tranquilizador"); **NEUTRO** = informativa. É um indicador **indireto**: reflete como a mídia enquadra o assunto, não a opinião da população, e não foi validado contra uma amostra rotulada manualmente.

## 7. Qualidade e confiabilidade

- Números calculados em código e cobertos por testes com respostas conhecidas (ex.: ano com mais casos, variação nas mesmas semanas).
- Sem dado sintético nas respostas: com o InfoDengue fora do ar, a conversa e o dashboard informam o erro.
- Tudo que a IA produz é identificado, e toda resposta traz o aviso de que o modelo pode errar.
