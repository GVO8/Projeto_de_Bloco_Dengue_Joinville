# Arquitetura (hexagonal / portas e adaptadores)

## Visão geral

```
                    ADAPTADORES DE ENTRADA (quem chama o sistema)
     ┌──────────────────────┐  ┌───────────────────────────┐  ┌──────────────┐
     │ API FastAPI          │  │ Interface Streamlit        │  │ CLI          │
     │ api_fastapi/         │  │ ui_streamlit/ (+ gateways) │  │ Code/cli.py  │
     └──────────┬───────────┘  └─────────────┬─────────────┘  └──────┬───────┘
                │  casos de uso               │                        │
     ┌──────────▼────────────────────────────▼────────────────────────▼───────┐
     │                         NÚCLEO  (Code/dengue/core)                      │
     │  domain/  entidades, erros, regras de texto   prompts.py                │
     │  services/  ProcessarNoticia · PrepararCorpus · ServicoSerieInfoDengue  │
     │             ServicoNoticias · ColetarNoticias                           │
     │  ports/   ModeloLinguagem · RepositorioNoticias · ArmazenamentoCorpus   │
     │           FonteInfoDengue · RepositorioUploads · ColetorNoticias        │
     └──────────┬────────────────────────────┬────────────────────────┬───────┘
                │ implementa                  │                        │
     ┌──────────▼───────────┐  ┌─────────────▼──────────┐  ┌──────────▼───────┐
     │ ModeloLlamaCpp (real)│  │ NoticiasCsvTxt, Corpus │  │ InfoDengueHttp,  │
     │ ModeloFake (testes)  │  │ Jsonl, UploadsCsv      │  │ ColetorNscTotal  │
     └──────────────────────┘  └────────────────────────┘  └──────────────────┘
                    ADAPTADORES DE SAÍDA (o que o sistema usa)  — adapters/outbound/
```

`container.py` é a **raiz de composição**: o único lugar que escolhe as implementações e as injeta nos casos de uso.

## Regra de dependência (verificada por teste)

As setas apontam sempre **para o núcleo**. `Tests/test_arquitetura.py` lê os `import` de cada arquivo e falha se:
- o **núcleo** importar adaptadores, `container`, `config` ou frameworks (FastAPI, Streamlit, requests, bs4, llama_cpp...);
- um adaptador de **saída** importar adaptadores de **entrada** ou o container;
- um adaptador de **entrada** importar adaptadores de saída (eles chegam às implementações só pelo container) ou a API conhecer a interface (e vice-versa).

## Mapa de pastas

```
Code/
├── dengue/
│   ├── core/            domain/ (modelos, erros, texto) · ports/ · services/ · prompts.py
│   ├── adapters/
│   │   ├── inbound/     api_fastapi/ (rotas, schemas, erros, app) · ui_streamlit/ (gateways, views)
│   │   └── outbound/    infodengue, noticias_arquivos, nsc_scraper, llm_llamacpp, llm_fake, modelo_download
│   ├── config.py        variáveis DENGUE_*  ·  container.py  (composição)
├── run_api.py · streamlit_app.py · cli.py     pontos de entrada finos
Tests/                   150 testes (núcleo, adaptadores, API, interface, arquitetura)
```

## SOLID na prática

| Princípio | Onde aparece |
|---|---|
| **S**ingle Responsibility | Um caso de uso por classe (`ProcessarNoticia`, `PrepararCorpus`...); rotas só traduzem HTTP; parsing do scraper separado do I/O |
| **O**pen/Closed | Trocar o modelo = nova classe que implementa `ModeloLinguagem`, sem mexer no núcleo (ex.: um adaptador Transformers). *Exceção conhecida:* nova operação de IA exige editar `Operacao`, `prompts.py` e `ProcessarNoticia._montar` |
| **L**iskov | `ModeloFake` e `ModeloLlamaCpp` são intercambiáveis nos testes e na API; `InfoDengueComAlternativa` é uma `FonteInfoDengue` |
| **I**nterface Segregation | Portas pequenas e específicas. *Ponto fraco:* `Gateway` da interface tem 7 métodos |
| **D**ependency Inversion | Casos de uso dependem de portas (ABC), nunca de implementações; o container injeta |

## Fluxo da operação de IA (Questões 2 e 3)

1. Botão da notícia → `Gateway.processar_noticia` → `POST /noticias/{id}/processar`.
2. A rota valida o corpo (Pydantic) e chama `ProcessarNoticia.executar`.
3. O caso de uso busca a notícia **inteira** no corpus (`noticias_corpus.jsonl`, gerado por `PrepararCorpus`); se o corpus não existe ou não cobre a notícia, **reconstrói uma vez**.
4. Monta o prompt com `prompts.montar_prompt`, chama `ModeloLinguagem.gerar` e devolve `RespostaProcessamento`.
5. A rota converte para `RespostaProcessamentoSchema` (response model). O campo `markdown` já traz: título → operação → resultado → resumo final → avisos → **aviso padrão** (sempre por último).

## Tratamento de erros (Questão 4)

Toda falha previsível é um `ErroDengue` com `mensagem` (o que houve), `sugestao` (o que fazer), `categoria` (`entrada`, `dados`, `ia`, `sistema`) e status HTTP. Erros de IA começam com "Houve um problema com a IA (modelo …)".

| Situação | HTTP | Categoria |
|---|---|---|
| Operação inválida / corpo inválido / pergunta ausente | 422 | entrada |
| Notícia inexistente | 404 | dados |
| Corpus não pôde ser preparado | 503 | dados |
| Modelo não baixado / biblioteca ausente / falha ao carregar | 503 | ia |
| IA ocupada com outra solicitação | 429 | ia |
| Tempo limite da IA | 504 | ia |
| Falha na inferência / resposta vazia | 502 | ia |
| Qualquer outra exceção | 500 | sistema (código de protocolo no log, sem vazar detalhes) |

A interface (`componentes.protegido`) mostra o mesmo formato, sem *stack trace*.

## Revisão crítica (engenheiro sênior): pontos fortes e dívidas conhecidas

**Pontos fortes:** núcleo testável sem rede/modelo/disco; regra de dependência garantida por teste; modelo real isolado atrás de uma porta com fila, *timeout* real e erros traduzidos; mensagens de erro consistentes de ponta a ponta; 150 testes + verificação por mutação.

**Dívidas e riscos (por prioridade):**
1. **Concorrência em arquivos:** reconstrução do corpus e `uploads.csv` não têm trava; seguro para uso local de um usuário, não para vários. *Evolução:* banco (SQLite) ou trava de arquivo.
2. **Rotas síncronas esperam a IA** (até 10 min) ocupando uma *thread* do servidor; aceitável com 1 usuário. *Evolução:* tarefa em segundo plano + consulta de status (`202 Accepted`).
3. **`pandas.DataFrame` no núcleo** (série InfoDengue): pragmático em ciência de dados, mas acopla o domínio ao pandas. *Evolução:* entidade `RegistroSemanal`.
4. **Abertura/fechamento (O):** nova operação exige editar 3 pontos; um registro de operações (estratégia) resolveria se elas crescerem.
5. **`Gateway` largo (I)** e `LocalGateway` dependendo do `Container` (localizador de serviços): dividir em portas menores.
6. **API sem autenticação** (uso local). Obrigatória antes de qualquer exposição.
7. **Modelo real não foi executado no ambiente de desenvolvimento** (sem acesso ao Hugging Face): o adaptador foi validado com um `Llama` falso; o primeiro teste real é na máquina do projeto (ver README).
