# Dengue em Joinville — dados, mídia e IA em linguagem natural (TP5)

Projeto de Bloco · Ciência de Dados Aplicada · ODS 3 (Saúde e Bem-Estar), 16.10 (acesso à informação) e 17.

Um **dashboard** com dados reais do **InfoDengue** (Joinville/SC) e notícias reais coletadas na web, e uma **IA local** (Qwen3-4B, sem nuvem) que:

- 💬 **conversa com os dados**: você pergunta em português *"qual foi o ano com mais casos de dengue?"*, a IA transforma a pergunta em uma consulta ao InfoDengue e responde com base nos números retornados (sempre **Joinville**, sempre **dengue**, com memória da conversa);
- 📰 **lê as notícias**: resume, classifica o **sentimento** (quanto a notícia transmite preocupação), responde perguntas e gera relatório;
- 📊 **cruza os dois** no dashboard: curva de casos × tom da mídia.

> ⚠️ A IA pode errar (toda resposta traz esse aviso). Os **números** não vêm da IA: são calculados em código a partir da resposta do InfoDengue, e cada resposta mostra a requisição feita e os fatos usados.

## Como as peças se encaixam

| Peça | O que é | Precisa ligar? |
|---|---|---|
| **InfoDengue** | Fonte pública dos dados (internet) | Não: é consultada sozinha |
| **API do projeto** (FastAPI) | Entrega dados e IA por rotas HTTP | **Sim, para usar a IA** (`python Code/run_api.py`) |
| **Interface** (Streamlit) | Dashboard, conversa e demais páginas | Sim (`python -m streamlit run Code/streamlit_app.py`) |
| **Modelo de IA** | Arquivo de 2,5 GB que roda no seu computador | Baixar uma vez (`python Code/cli.py baixar-modelo`) |

---

## Passo a passo no Windows (do zero)

Tempo estimado: 20 a 40 minutos (a maior parte é o download do modelo). Todos os comandos são digitados no **PowerShell**.

### 1. Instale o Python 3.12
> **Importante:** use o **3.12**. Em versões mais novas (como 3.14) não existe versão pronta da biblioteca da IA (`llama-cpp-python`) e a instalação falha.

1. Veja o que você já tem: abra o PowerShell e digite `py -0`. Se aparecer `3.12`, pule para o passo 2.
2. Baixe o instalador **Windows installer (64-bit)** do Python 3.12 em <https://www.python.org/downloads/> (procure "Python 3.12.x" na lista de versões).
3. Ao abrir o instalador, **marque "Add python.exe to PATH"** e clique em *Install Now*.
4. Feche o PowerShell e abra outro. Confirme com `py -3.12 --version` (deve mostrar `Python 3.12.x`).

### 2. Instale o Git (opcional, mas recomendado)
Baixe em <https://git-scm.com/download/win> e instale aceitando as opções padrão. Se preferir não instalar, pule o `git clone` do próximo passo e use *Code → Download ZIP* no GitHub.

### 3. Baixe o projeto
Escolha uma pasta (ex.: `Documentos`) e rode:
```powershell
cd $HOME\Documents
git clone https://github.com/GVO8/Projeto_de_Bloco_Dengue_Joinville
cd Projeto_de_Bloco_Dengue_Joinville
```
(Com o ZIP: extraia e entre na pasta com `cd`.)

### 4. Crie e ative o ambiente virtual
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```
Se aparecer um erro de *"execução de scripts desabilitada"*, rode antes: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` e ative de novo.
O prompt deve passar a começar com `(.venv)`. Confirme com `python --version` → **3.12.x**.

### 5. Instale as dependências
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-llm.txt
```
O segundo instala o painel e a API; o terceiro, a IA local (usa uma versão pronta, sem compilar nada). Confirme:
```powershell
python -c "import streamlit, fastapi, llama_cpp; print('tudo certo')"
```

### 6. Baixe o modelo de IA (uma única vez)
```powershell
python Code/cli.py baixar-modelo
```
São ≈ **2,5 GB**: tenha espaço livre e internet estável. Se a conexão cair, rode o comando de novo. Depois confira:
```powershell
python Code/cli.py status
```
Deve mostrar `Pronto: sim`.

### 7. (Opcional) Atualize as notícias e analise o sentimento
```powershell
python Code/cli.py coletar-noticias          # busca notícias novas (internet)
python Code/cli.py analisar-sentimentos      # a IA classifica cada notícia (alguns minutos por notícia)
```
O dashboard funciona sem isso, mas a seção de mídia só aparece depois da análise de sentimento.

### 8. Ligue a API (Terminal 1)
```powershell
python Code/run_api.py
```
Deixe esta janela aberta. Na primeira vez, o Windows pode pedir permissão no firewall: clique em *Permitir*. Para conferir, abra <http://127.0.0.1:8000/docs>.

### 9. Ligue a interface (Terminal 2)
Abra **outro** PowerShell, entre na pasta do projeto, ative o ambiente e rode:
```powershell
cd $HOME\Documents\Projeto_de_Bloco_Dengue_Joinville
.venv\Scripts\Activate.ps1
python -m streamlit run Code/streamlit_app.py
```
O navegador abre em <http://localhost:8501>.

### 10. Use
- **Dashboard**: situação atual, gráficos e mídia.
- **Converse com os dados**: clique em um exemplo ou digite uma pergunta. A primeira resposta demora mais, porque o modelo é carregado; em computadores sem placa de vídeo compatível cada resposta pode levar **alguns minutos** (uma pergunta usa duas chamadas à IA).
- **Notícias e IA**: abra uma notícia e use **Resumir · Sentimento · Perguntar · Relatório**.

### 11. Meça o modelo e guarde a evidência (necessário para o relatório)
```powershell
python Code/cli.py medir-modelo --hardware "i7-7500U, 24 GB RAM, GPU 4 GB" --pergunta "Qual foi o ano com mais casos de dengue?"
```
Gera `Docs/Evidencias/medicao_*.md` com os tempos reais. Veja `Docs/Evidencias/README.md`.

### 12. Encerrar e voltar depois
Em cada janela, `Ctrl + C` para parar e `deactivate` para sair do ambiente. **Nas próximas vezes**, basta repetir só os passos **4 (apenas a linha de ativar)**, **8** e **9**.

### Problemas comuns no Windows

| Sintoma | O que fazer |
|---|---|
| `python`/`py` não é reconhecido | Reinstale o Python marcando *Add python.exe to PATH*; abra um PowerShell novo |
| `py -3.12` não encontra a versão | Instale o Python 3.12 (passo 1) |
| Erro de *execução de scripts desabilitada* | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `pip` tenta compilar e falha (cita Visual Studio/Meson/vswhere) | Você está no Python errado (ex.: 3.14). Apague a pasta `.venv` e refaça do passo 4 com `py -3.12` |
| `llama-cpp-python` não instala | Confirme `python --version` = 3.12 dentro do `(.venv)` e rode `python -m pip install -r requirements-llm.txt` de novo |
| "…o arquivo do modelo ainda não foi baixado" | `python Code/cli.py baixar-modelo` |
| "O aplicativo não conseguiu falar com a API" | Ligue a API (passo 8) e tente de novo |
| "Porta 8000 em uso" | `python Code/run_api.py --porta 8001` e, no Terminal 2, `$env:DENGUE_API_URL="http://127.0.0.1:8001"` antes de ligar a interface |
| "…não foi possível consultar o InfoDengue" | Verifique a internet; o serviço também pode estar fora do ar |
| "…a IA ainda está respondendo a outra solicitação" | Aguarde a resposta atual terminar |
| "…passou do tempo limite" | Use uma operação mais curta, aumente `DENGUE_LLM_TIMEOUT_S` ou tente usar a placa de vídeo (abaixo) |
| Página do Streamlit em branco | Recarregue (F5); confira se o Terminal 2 não mostra erro |

### Usar a placa de vídeo (opcional)
Por padrão a IA roda só na CPU. Se a sua placa for compatível e a instalação enxergá-la, tente `$env:DENGUE_LLM_GPU_LAYERS="-1"` (tudo na GPU) ou um valor menor (ex.: `20`) antes de ligar a API. Não garantido em placas antigas: se der erro ou faltar memória de vídeo, remova a variável.

### Testar sem baixar o modelo (somente para demonstração)
`$env:DENGUE_LLM_BACKEND="fake"` antes de `python Code/run_api.py` usa um modelo **simulado** (respostas marcadas como "[resposta simulada]"). Serve só para ver a interface; **não é IA real** e `medir-modelo` se recusa a rodar assim.

---

## Variáveis de ambiente (opcionais)

| Variável | Padrão | Para que serve |
|---|---|---|
| `DENGUE_LLM_BACKEND` | `llamacpp` | `fake` = modelo simulado |
| `DENGUE_LLM_GPU_LAYERS` | `0` (só CPU) | `-1` = tudo na GPU; ou número de camadas |
| `DENGUE_LLM_THREADS` | automático | Threads da CPU |
| `DENGUE_LLM_N_CTX` | `4096` | Janela de contexto |
| `DENGUE_LLM_TIMEOUT_S` | `600` | Tempo máximo por chamada à IA |
| `DENGUE_LLM_CAMINHO` | `Models/…gguf` | Usar um GGUF em outro lugar |
| `DENGUE_API_URL` | `http://127.0.0.1:8000` | Endereço da API usado pela interface |
| `DENGUE_HARDWARE` | — | Texto de hardware para `medir-modelo` |

## Comandos da CLI

```text
python Code/cli.py status                  estado do modelo e da configuração
python Code/cli.py baixar-modelo           baixa o GGUF (≈2,5 GB)
python Code/cli.py coletar-noticias        scraping das notícias + reconstrói o corpus
python Code/cli.py gerar-corpus            reconstrói o corpus a partir das notícias salvas
python Code/cli.py analisar-sentimentos    sentimento (preocupação) de cada notícia, para o dashboard
python Code/cli.py medir-modelo            chamada REAL ao modelo com tempos medidos → Docs/Evidencias/
```

## Testes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```
314 testes: núcleo, adaptadores, API, páginas, CLI, **FakeLLM** nas operações de IA, e um **teste de arquitetura** (regra de dependência). Nenhum teste baixa o modelo nem usa a internet.

## Gerar o PDF do TP5

A apresentação e a argumentação (Tarefa 4) ficam em `Docs/Apresentacao/`. O PDF é gerado a partir da mesma fonte do Markdown, e os **prints** entram sozinhos:

1. Coloque seus prints em `Docs/Apresentacao/prints/` com estes nomes: `dashboard.png`, `chat.png`, `midia.png`, `mensurado.png`.
2. Gere o PDF (com o ambiente ativo e `python -m pip install -r requirements-dev.txt`):
   ```powershell
   python Docs/Apresentacao/gerar_pdf.py --nome "Seu Nome" --saida nome_sobrenome_PB_TP5.pdf
   ```
3. Preencha a tabela da seção 8 (respostas reais) em `Docs/Apresentacao/conteudo.py`, rode de novo e confira o PDF.

## Estrutura

```
Code/
├── dengue/
│   ├── core/          domain · ports · services · prompts*.py     regras de negócio, sem frameworks
│   ├── adapters/
│   │   ├── inbound/   api_fastapi · ui_streamlit · evidencia      quem chama o sistema
│   │   └── outbound/  infodengue · notícias · conversas · llm …   o que o sistema usa
│   ├── config.py · container.py                                   configuração e composição
├── run_api.py · streamlit_app.py · cli.py
Data/  Raw/ (notícias coletadas)  Processed/ (corpus, contexto, sentimentos)
Models/                modelo GGUF (não versionado)
Docs/  API.md · Project/ · DataReport/ · Evidencias/ · Apresentacao/
Tests/
```

## Documentação
[Project Charter](Docs/Project/project_charter.md) · [Data Summary Report](Docs/DataReport/data_summary_report.md) · [Arquitetura](Docs/Project/arquitetura.md) · [Escolha do modelo](Docs/Project/escolha_modelo_llm.md) · [API](Docs/API.md) · [Apresentação](Docs/Apresentacao/argumentacao.md) · [Evidências](Docs/Evidencias/README.md) · [CRISP-DM × TDSP](Docs/Project/tdsp_crispdm_mapping.md)
