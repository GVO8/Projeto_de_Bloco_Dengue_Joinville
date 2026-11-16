# Dengue em Múltiplas Dimensões (TP4)

Painel de dados de dengue para Joinville/SC: série semanal do InfoDengue, notícias coletadas por *web scraping*, **API FastAPI** e uma **IA local** (Qwen3-4B-Instruct) que resume, classifica o sentimento, responde perguntas e gera relatórios a partir das notícias. Alinhado ao ODS 3. O projeto não envolve contato com órgãos públicos.

> ⚠️ As respostas da IA podem conter erros; toda resposta traz esse aviso.

## Como os dados e a IA chegam ao app

| | O que é | Você precisa fazer algo? |
|---|---|---|
| **API do InfoDengue** | Fonte pública dos dados | **Não.** É consultada sozinha; sem internet usa uma amostra **sintética** e avisa na tela |
| **API FastAPI do projeto** | Entrega os dados e a **IA** por rotas HTTP | **Sim, para usar a IA:** ligar em um terminal (`python Code/run_api.py`). Para só ver o painel e as notícias, é opcional |
| **Modelo de IA** | Arquivo de 2,5 GB que roda no seu computador | Baixar **uma vez** (`python Code/cli.py baixar-modelo`) |

## Instalação (Windows / PowerShell)

> **Use Python 3.12 para a IA.** Não existe versão pronta do `llama-cpp-python` para Python 3.14 (o Windows tentaria compilar e falharia). Verifique com `py -0` (lista as versões instaladas); se não houver a 3.12, instale-a em python.org (marque "Add python.exe to PATH").

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-llm.txt      # IA local (opcional para ver só o painel)
python Code/cli.py baixar-modelo                    # ≈ 2,5 GB, uma única vez, precisa de internet
python Code/cli.py status                           # confere se está tudo pronto
```
Mac/Linux: `python3.12 -m venv .venv && source .venv/bin/activate`.

## Execução (raiz do projeto, ambiente ativo)

```powershell
# Terminal 1 — API (necessária para os botões de IA)
python Code/run_api.py

# Terminal 2 — Interface
python -m streamlit run Code/streamlit_app.py
```
Na página **Notícias e IA**, abra uma notícia e use os botões **Resumir · Sentimento · Perguntar · Relatório**. Em computador sem placa de vídeo compatível, **a primeira resposta leva mais tempo** (o modelo é carregado) e cada resposta pode levar **de 1 a 3 minutos**. Swagger: http://127.0.0.1:8000/docs.

### Demonstração sem baixar o modelo
`$env:DENGUE_LLM_BACKEND="fake"` (PowerShell) antes de `python Code/run_api.py` usa um modelo **simulado** (respostas marcadas como "[resposta simulada]"). Serve só para testar a interface; não é IA real.

### Outras tarefas
```powershell
python Code/cli.py coletar-noticias --max-paginas 3   # scraping (internet) + reconstrói o corpus
python Code/cli.py gerar-corpus                        # só reconstrói o corpus a partir das notícias salvas
```

## Variáveis de ambiente (opcionais)

| Variável | Padrão | Para que serve |
|---|---|---|
| `DENGUE_LLM_BACKEND` | `llamacpp` | `fake` = modelo simulado |
| `DENGUE_LLM_GPU_LAYERS` | `0` (só CPU) | `-1` = tudo na placa de vídeo; ou um número (ex.: `20`) para dividir |
| `DENGUE_LLM_THREADS` | automático | Nº de threads da CPU |
| `DENGUE_LLM_N_CTX` | `4096` | Janela de contexto |
| `DENGUE_LLM_TIMEOUT_S` | `600` | Tempo máximo por resposta |
| `DENGUE_LLM_CAMINHO` | `Models/…gguf` | Usar um arquivo GGUF em outro lugar |
| `DENGUE_API_URL` | `http://127.0.0.1:8000` | Endereço da API usado pela interface |

## Testes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```
150 testes: núcleo, adaptadores, API, interface, o adaptador do modelo (com um `Llama` falso), **FakeLLM** nas operações de IA e um **teste de arquitetura** (regra de dependência). Nenhum teste baixa o modelo ou usa a internet.

## Problemas comuns

| Mensagem | O que fazer |
|---|---|
| "…o arquivo do modelo ainda não foi baixado" | `python Code/cli.py baixar-modelo` |
| "…a biblioteca … (llama-cpp-python) não está instalada" | Use Python 3.12 e `python -m pip install -r requirements-llm.txt` |
| "O aplicativo não conseguiu falar com a API" | Em outro terminal: `python Code/run_api.py` |
| "…passou do tempo limite" | Notícia/operação menor, ou aumente `DENGUE_LLM_TIMEOUT_S`, ou use a GPU |
| "…a IA ainda está respondendo a outra solicitação" | Aguarde a resposta atual terminar |

## Estrutura

```
Code/
├── dengue/
│   ├── core/          domain · ports · services · prompts.py      (regras de negócio, sem frameworks)
│   ├── adapters/
│   │   ├── inbound/   api_fastapi · ui_streamlit                  (quem chama o sistema)
│   │   └── outbound/  infodengue · arquivos · scraper · llm       (o que o sistema usa)
│   ├── config.py · container.py                                   (configuração e composição)
├── run_api.py · streamlit_app.py · cli.py
Data/  Raw/ (coletado)  Processed/ (corpus, contexto, uploads)
Models/                modelo GGUF (não versionado)
Docs/  API.md · Project/ (charter, arquitetura, escolha do modelo, …) · DataReport/
Tests/
```

## Documentação
[Arquitetura](Docs/Project/arquitetura.md) · [Escolha do modelo](Docs/Project/escolha_modelo_llm.md) · [API](Docs/API.md) · [Project Charter](Docs/Project/project_charter.md) · [Data Summary Report](Docs/DataReport/data_summary_report.md) · [Prontidão para LLM](Docs/Project/llm_readiness.md) · [CRISP-DM × TDSP](Docs/Project/tdsp_crispdm_mapping.md)
