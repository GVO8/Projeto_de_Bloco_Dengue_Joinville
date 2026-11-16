# Prontidão para LLM — **concluída no TP4** (modelo local integrado)

> Status: o corpus e os prompts descritos abaixo agora alimentam o modelo **Qwen3-4B-Instruct-2507** pela rota `POST /noticias/{id}/processar`. Escolha do modelo: `escolha_modelo_llm.md`. Arquitetura: `arquitetura.md`. As quatro tarefas (resumo, sentimento, perguntas e respostas, relatório) estão implementadas; a **avaliação quantitativa** continua pendente (seção 4).

## 1. Dados disponíveis → tarefas possíveis

| Tarefa (enunciado) | Dados de entrada | Artefato pronto | Observações |
|---|---|---|---|
| **Resumo** de textos longos | Corpo das notícias | `Data/Processed/noticias_corpus.jsonl` (trechos de até 800 caracteres) | Notícias longas são resumidas por trecho e depois combinadas |
| **Classificação de sentimento** | Título + resumo das notícias | `nsc_noticias_joinville_dengue.csv` | "Sentimento" aqui = tom para a saúde pública (positivo/negativo/neutro). Sem rótulos prévios, a avaliação exigirá uma amostra rotulada manualmente |
| **Perguntas e respostas** | Trechos das notícias + contexto numérico | `noticias_corpus.jsonl` + `contexto_infodengue.json` | Recuperação simples por busca de trechos antes de montar o prompt (RAG básico) |
| **Geração de relatório** | Níveis de alerta semanais + títulos recentes | `contexto_infodengue.json` + CSV de notícias | Texto descritivo; o prompt proíbe previsões |

## 2. O que foi preparado
- `Code/dengue/core/services/corpus.py` (`PrepararCorpus`): gera o corpus em trechos **limpos** (com id, título, data, autor, URL, resumo) e o contexto numérico. Comando: `python Code/cli.py gerar-corpus`.
- `Code/dengue/core/prompts.py`: 4 templates versionados (v0.2), um por tarefa, com limite de tokens e indicação de pergunta obrigatória.
- Página **Assistente de IA** no app: estado do modelo, mapa dados × tarefas e prompts.

## 3. Decisões de projeto
- **Trechos de 800 caracteres:** cabem em qualquer janela de contexto e preservam a URL de origem para citação.
- **Prompts ancorados:** o template de Q&A manda responder "somente com o contexto" e admitir quando não souber.
- **Formato `.jsonl`:** uma linha por trecho, fácil de indexar ou enviar em lote.
- **Dados da API do InfoDengue** entram como texto compacto (`contexto_infodengue.json`), não como a tabela inteira.

## 4. Limitações e pontos de atenção
- Corpus pequeno (depende do que o scraper coletar); para Q&A útil convém ampliar `--max-paginas`.
- Notícias têm autoria e direitos próprios: o uso é educacional e as respostas devem citar a URL de origem.
- Sem avaliação ainda: a próxima etapa deve definir como medir qualidade (ex.: amostra rotulada para sentimento, conferência manual de resumos).
- Risco de alucinação em relatórios: manter a instrução de não prever e conferir números contra `contexto_infodengue.json`.

## 5. Para a próxima etapa
Avaliar a qualidade: montar uma amostra de notícias com resumos e rótulos de sentimento conferidos manualmente, medir fidelidade/erros e comparar parâmetros (temperatura, tamanho do trecho) ou outro modelo (basta um novo adaptador de `ModeloLinguagem`).
