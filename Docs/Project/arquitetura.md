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
     │  services/  ProcessarNoticia · ConversarComDados · AnalisarSentimentos  │
     │             PrepararCorpus · ServicoSerieInfoDengue · ServicoHistorico… │
     │             ServicoNoticias · ColetarNoticias · fatos_dengue (cálculo)  │
     │  ports/   ModeloLinguagem · ConsultaInfoDengue · RepositorioConversas   │
     │           RepositorioNoticias · ArmazenamentoCorpus · RepositorioSentimentos │
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
Tests/                   314 testes (núcleo, adaptadores, API, interface, CLI, arquitetura)
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

## Fluxo da conversa com os dados (TP5, memória conversacional)

1. `ConversarComDados.executar(sessao_id, pergunta)` valida a pergunta e a sessão.
2. **Guarda de escopo em 3 camadas:** (1) `domain/escopo.py`, determinística e sem custo de IA, barra outras cidades/territórios, assuntos sem relação com dengue e tentativas de alterar as regras; (2) o plano do modelo também sinaliza `assunto_valido` e `cidade`; (3) a resposta só usa os dados de Joinville.
3. **Planejamento:** o modelo (modo JSON, *few-shot*) gera o plano; `domain/planejamento.py` o valida e reconcilia com regras (anos escritos na pergunta prevalecem); se o JSON falhar, as regras assumem.
4. **Requisição:** porta `ConsultaInfoDengue` (adaptador HTTP + cache de 15 min). Sem alternativa sintética.
5. **Fatos:** `fatos_dengue.calcular_fatos` (pandas, determinístico): totais, picos, ranking só de anos completos, comparação nas mesmas semanas.
6. **Resposta:** o modelo redige só a partir dos fatos e dos últimos 3 turnos; o turno é gravado na porta `RepositorioConversas` (memória em RAM por sessão, com limite de sessões e turnos).

**Por que os números não vêm da IA:** um modelo de 4 bilhões de parâmetros erra aritmética e comparações. Calcular em código torna cada número auditável e testável.

## Dashboard (TP5)

`views/dashboard.py` consome o gateway (`historico_infodengue`, `sentimentos`, `listar_noticias`): KPIs calculados, ciclo de dados com contadores reais, três gráficos de casos (sazonalidade por ano, total por ano, semanas por nível de alerta), mídia (tom das notícias e linha do tempo cruzada com os casos) e convite à conversa. O que é IA é identificado.

## Tratamento de erros (Questão 4)

Toda falha previsível é um `ErroDengue` com `mensagem` (o que houve), `sugestao` (o que fazer), `categoria` (`entrada`, `dados`, `ia`, `sistema`) e status HTTP. Erros de IA começam com "Houve um problema com a IA (modelo …)".

| Situação | HTTP | Categoria |
|---|---|---|
| Operação inválida / corpo inválido / pergunta ausente | 422 | entrada |
| Notícia inexistente | 404 | dados |
| Corpus não pôde ser preparado | 503 | dados |
| Modelo não baixado / biblioteca ausente / falha ao carregar | 503 | ia |
| IA ocupada com outra solicitação | 429 | ia |
| Pergunta vazia/longa ou sessão inválida | 422 | entrada |
| Conversa inexistente | 404 | dados |
| InfoDengue indisponível | 503 | dados |
| InfoDengue sem dados para o período | 404 | dados |
| InfoDengue com formato inesperado | 502 | dados |
| Tempo limite da IA | 504 | ia |
| Falha na inferência / resposta vazia | 502 | ia |
| Qualquer outra exceção | 500 | sistema (código de protocolo no log, sem vazar detalhes) |

A interface (`componentes.protegido`) mostra o mesmo formato, sem *stack trace*.

## Revisão crítica (engenheiro sênior): pontos fortes e dívidas conhecidas

**Pontos fortes:** núcleo testável sem rede/modelo/disco; regra de dependência garantida por teste; modelo real isolado atrás de uma porta com fila, *timeout* real, modo JSON e métricas; números calculados em código; mensagens de erro consistentes de ponta a ponta; 314 testes + verificação por mutação (15 quebras propositais detectadas).

**Dívidas e riscos (por prioridade):**
1. **Concorrência em arquivos:** reconstrução do corpus e `uploads.csv` não têm trava; seguro para uso local de um usuário, não para vários. *Evolução:* banco (SQLite) ou trava de arquivo.
2. **Rotas síncronas esperam a IA** (até 10 min) ocupando uma *thread* do servidor; aceitável com 1 usuário. *Evolução:* tarefa em segundo plano + consulta de status (`202 Accepted`).
3. **`pandas.DataFrame` no núcleo** (série InfoDengue): pragmático em ciência de dados, mas acopla o domínio ao pandas. *Evolução:* entidade `RegistroSemanal`.
4. **Abertura/fechamento (O):** nova operação exige editar 3 pontos; um registro de operações (estratégia) resolveria se elas crescerem.
5. **`Gateway` largo (I)** e `LocalGateway` dependendo do `Container` (localizador de serviços): dividir em portas menores.
6. **API sem autenticação** (uso local). Obrigatória antes de qualquer exposição.
7. **Modelo real e InfoDengue real não foram executados no ambiente de desenvolvimento** (sem acesso de rede): o adaptador do modelo foi validado com um `Llama` falso e a consulta ao InfoDengue com respostas simuladas. O primeiro teste real é na máquina do projeto (`python Code/cli.py medir-modelo`).
8. **Guarda de escopo heurística:** a lista de cidades é finita e os termos de domínio são aproximações; a camada 2 (IA) cobre o resto, com a margem de erro de um modelo pequeno.
9. **`evidencia.py` (adaptador de entrada) importa `llama_cpp` para ler a versão:** pequeno vazamento de detalhe de adaptador; o ideal é a porta do modelo expor essa informação.
