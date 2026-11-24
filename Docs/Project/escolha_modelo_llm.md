# Escolha do modelo LLM local (TP4 — Questão 1)

**Modelo escolhido:** `Qwen3-4B-Instruct-2507`, quantizado em 4 bits (`Q4_K_M`, formato GGUF).
**Arquivo:** `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (≈ 2,50 GB) · **Repositório:** [`unsloth/Qwen3-4B-Instruct-2507-GGUF`](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF) · **Licença:** Apache-2.0.

## 1. Requisitos do projeto que guiaram a escolha

| Requisito | Origem | Consequência |
|---|---|---|
| Resumir, classificar sentimento, responder perguntas e gerar relatório sobre **notícias em português** | Enunciado + `prompts.py` | Modelo **generativo, instruído e com bom domínio do português** |
| **Fidelidade** ao texto (sem inventar fatos sobre saúde pública) | Contexto do projeto | Modelo de instruções, com decodificação de baixa temperatura (0,2) |
| Rodar **100% local**, sem nuvem | Enunciado | Pesos baixáveis e executáveis offline |
| Máquina: **i7-7500U (2 núcleos/4 threads), 24 GB de RAM, placa de vídeo de 4 GB** | Hardware do projeto | Modelo pequeno e quantizado; **CPU como caminho principal** |
| Execução em **FastAPI** com tratamento de erros | Enunciado | Carregamento sob demanda, fila de 1 inferência, limite de tempo |

## 2. Critérios do enunciado

### 2.1 Desempenho
- **Tipo de tarefa:** é um modelo *decoder* generativo ajustado para seguir instruções (`Instruct`), que cobre as quatro tarefas do projeto com **um único modelo** trocando apenas o prompt. Modelos como BERT/BERTimbau são *encoders*: ótimos para classificação, mas **não geram** resumo, resposta ou relatório; T5/PTT5 geram, mas exigem ajuste fino por tarefa.
- **Português:** a família Qwen3 é multilíngue e inclui o português entre os idiomas suportados.
- **Versão `2507` "Instruct":** é a variante *sem modo de raciocínio* (não emite blocos `<think>`), o que é desejável aqui: a resposta é direta, mais curta e **mais rápida** em hardware limitado.
- **Contexto:** suporta janelas de até 262 mil tokens; usamos **4.096** (notícias coletadas têm de ≈ 2,4 mil a 4,6 mil caracteres, ou seja ≈ 600–1.500 tokens), o que é bem confortável.
- **Nota honesta:** não executamos benchmarks de qualidade. A escolha se apoia nas características do modelo e na adequação ao hardware; a qualidade real deve ser **avaliada na próxima etapa** com uma amostra de notícias conferida manualmente (ver `llm_readiness.md`).

### 2.2 Custo computacional local
Os números abaixo são **estimativas de engenharia** (não medições na máquina do projeto).

| Item | Estimativa | Observação |
|---|---|---|
| Pesos (Q4_K_M) | ≈ 2,5 GB | Arquivo medido no repositório |
| Cache de contexto (n_ctx = 4.096) | ≈ 0,6 GB | Calculado a partir da arquitetura (36 camadas × 8 cabeças KV × 128 dim × fp16) |
| Memória total na execução | ≈ 3,2–3,6 GB | Cabe com folga na **RAM de 24 GB**; na **VRAM de 4 GB** fica no limite |
| Velocidade em CPU (i7-7500U) | da ordem de **2 a 5 tokens/s** na geração | Leitura do texto da notícia é mais rápida que a geração |
| Tempo por clique (CPU) | **cerca de 1 a 3 minutos** | Daí o limite de tempo de 600 s e o aviso na interface |

**Decisão:** o padrão é **CPU** (`DENGUE_LLM_GPU_LAYERS=0`). Usar a placa de vídeo é opcional: não confirmamos o modelo da GPU nem se as versões prontas do `llama-cpp-python` com CUDA a suportam (placas antigas costumam não ser). Se funcionar, `DENGUE_LLM_GPU_LAYERS=-1` (tudo na GPU) ou um valor parcial (ex.: `20`) acelera bastante; se faltar memória de vídeo, reduza o valor.

### 2.3 Acessibilidade local
- **Download direto** do Hugging Face Hub (`python Code/cli.py baixar-modelo`, usa `huggingface_hub`), uma única vez; depois funciona **sem internet**.
- **Execução:** `llama-cpp-python` (llama.cpp) carrega GGUF quantizado em CPU/GPU modestas.
- **Por que não Transformers + PyTorch?** O enunciado cita Transformers como *exemplo* de biblioteca. Para este hardware ele é pior: o checkpoint original (`Qwen/Qwen3-4B-Instruct-2507`, bf16) tem ≈ 8 GB e **não cabe nos 4 GB de VRAM**; quantizar em 4 bits com `bitsandbytes` exige GPU NVIDIA moderna; e em CPU o bf16 é lento. Como a aplicação fala com o modelo por uma **porta** (`ModeloLinguagem`), um adaptador Transformers pode ser acrescentado sem alterar o resto do sistema.
- **Restrição importante de ambiente:** o `llama-cpp-python` **não tem versão pronta para Python 3.14**. A parte de IA deve rodar em **Python 3.12** (veja `requirements-llm.txt`). O restante do projeto roda em qualquer versão.

## 3. Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| `Qwen/Qwen3-4B` (modelo híbrido original) | Gera "raciocínio" (`<think>`) por padrão → mais lento e verboso; pesos em bf16 (≈ 8 GB) não cabem na VRAM |
| Modelos de 7–8 B (Q4) | ≈ 4,5–5 GB: não cabem na VRAM e ficariam ~2× mais lentos em CPU |
| Modelos de 1–2 B | Mais rápidos, porém menos fiéis em português e mais propensos a erros factuais |
| BERT/BERTimbau | Não geram texto (só classificam/extraem) |
| T5/PTT5 | Exigiriam ajuste fino por tarefa, fora do escopo |

## 3.1 Uso do modelo no projeto

O mesmo modelo atende a duas funções: **(a)** operações sobre notícias (resumo, sentimento de preocupação, perguntas, relatório) e **(b)** a **conversa com os dados do InfoDengue**, que usa duas chamadas por pergunta: planejamento (saída em **modo JSON**, 120 tokens no máximo) e redação (250 tokens). Por isso a resposta de uma pergunta leva o dobro de uma operação simples.

## 4. Parâmetros adotados e por quê

| Parâmetro | Valor | Motivo |
|---|---|---|
| `temperature` | 0,2 | Resumos fiéis, pouca "criatividade" |
| `top_p` | 0,8 | Corta caudas improváveis |
| `n_ctx` | 4.096 | Cobre as notícias com folga e limita memória |
| Entrada máxima | 8.000 caracteres | Notícia maior é cortada em fronteira de frase e o usuário é avisado |
| `max_tokens` por operação | resumo 250 · sentimento 120 · pergunta 300 · relatório 350 | Respostas curtas = menos tempo de espera |
| Limite de tempo | 600 s | CPU antiga; a geração é interrompida de forma limpa (streaming) |

Todos podem ser alterados por variáveis `DENGUE_LLM_*` (ver README).

## 5. Evidência de execução real (PENDENTE — a ser preenchida na máquina do projeto)

As tabelas acima trazem **estimativas**, não medições. Como a avaliação do TP4 apontou, falta mostrar uma resposta real do modelo (os testes usam FakeLLM). Para substituir as estimativas:

```powershell
python Code/cli.py baixar-modelo                 # uma vez
python Code/cli.py medir-modelo --hardware "i7-7500U, 24 GB RAM, GPU 4 GB" --pergunta "Qual foi o ano com mais casos de dengue?"
```
O comando roda o **modelo real** duas vezes (a 1ª inclui carregar o modelo na memória, a 2ª não) e, com `--pergunta`, mede também a conversa com os dados (planejamento, InfoDengue e resposta). Salva `Docs/Evidencias/medicao_AAAAMMDD_HHMMSS.md` com ambiente, tokens, tokens/s, tempo até o 1º token, tempo total e o texto das respostas. Recusa-se a rodar com o modelo simulado, para não gerar falsa evidência.

| Medida | Estimativa | Medido na máquina do projeto |
|---|---|---|
| Carregar o modelo | — | _preencher_ |
| Tokens por segundo (CPU) | 2 a 5 | _preencher_ |
| Resposta a uma notícia (resumo) | 1 a 3 min | _preencher_ |
| Conversa com os dados (2 chamadas) | 2 a 6 min | _preencher_ |

Depois de medir, **substitua as estimativas desta página e do Charter pelos valores medidos** e anexe o arquivo de evidência e um print da tela ao relatório do TP. Veja `Docs/Evidencias/README.md`.
