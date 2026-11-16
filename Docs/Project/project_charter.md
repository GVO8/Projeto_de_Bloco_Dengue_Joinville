# Project Charter — Dengue em Múltiplas Dimensões (Joinville/SC)

**Versão TP4 · Projeto de IA Generativa e ESG · Ciência de Dados**
Histórico: TP1 (proposta) → TP2 (interface dinâmica, scraping, upload/download) → TP3 (multipáginas, FastAPI, preparação para LLM) → **TP4 (LLM local integrado à API, arquitetura hexagonal, testes)**.

---

## 1. Contexto e Justificativa

Joinville (SC) está numa região historicamente pouco afetada por dengue, mas o aumento das temperaturas e a expansão do *Aedes aegypti* para o Sul do Brasil a tornam vulnerável a surtos. Sistemas de alerta baseados em notificação (como o InfoDengue) já são referência; este projeto **não os replica**: usa-os como uma das dimensões de um painel mais amplo, que também reúne conteúdo textual de notícias públicas e, em etapas futuras, clima, satélite e população.

## 2. Problema de Negócio (reavaliado no TP4)

**Como reunir, num único painel interativo e acessível por API, indicadores públicos de dengue para Joinville/SC — série epidemiológica semanal, notícias recentes e, futuramente, clima, satélite e densidade populacional — de forma que partes interessadas e outras aplicações consumam esses dados e, na próxima etapa, recebam resumos e respostas geradas por LLM?**

**O que mudou em relação ao TP2 à luz das novas ferramentas:**
- A **FastAPI** transforma o projeto de "um app" em "uma plataforma de dados": o mesmo conjunto de dados passa a ser consumível por outros sistemas (rotas GET/POST), não apenas pela interface.
- O **objetivo de preparar os dados para LLM** passa a ser explícito: o painel deixa de ser apenas visualização e passa a produzir um corpus e contexto numérico prontos para resumo, classificação, Q&A e geração de relatório.
- Metas e KPIs foram atualizados (seção 4). O escopo de dimensões (SINAN, Copernicus, GEE, IBGE) **não mudou**: continuam documentadas como fontes futuras.

**O que mudou no TP4:** os dados e notícias deixam de apenas ser exibidos e passam a ser **interpretados por uma IA local**: para cada notícia o usuário pode pedir resumo, classificação de sentimento, uma resposta a uma pergunta ou um relatório. O modelo roda no computador do projeto (sem nuvem, sem custo por uso e sem enviar texto a terceiros), o que reforça o pilar de **Governança** (controle e transparência sobre o uso de IA). Toda resposta traz o aviso de que o modelo pode errar.

## 3. Pilar ESG e ODS

| Pilar ESG | Conexão |
|---|---|
| **Social (S)** | Saúde pública, prevenção de doença negligenciada |
| **Governança (G)** | Transparência e acessibilidade de dados públicos (agora inclusive por API) |

- **ODS 3** (Saúde e Bem-Estar), meta 3.3 — principal.
- **ODS 11** (Cidades e Comunidades Sustentáveis) — leitura territorial de indicadores.
- **ODS 17** (Parcerias e Meios de Implementação) — uso exclusivo de dados abertos e interface programática para reuso.

## 4. Metas e Indicadores (KPIs) — atualizados no TP4

| Meta | Indicador | Status ao fim do TP3 |
|---|---|---|
| Consolidar fontes públicas num só painel | Dimensões integradas tecnicamente | InfoDengue (API) + notícias (scraping); SINAN em amostra; demais documentadas |
| Interface multipágina | Nº de páginas navegáveis | 6 páginas com menu de navegação |
| Acesso programático aos dados | Nº de endpoints documentados | 4 (`GET /health`, `GET /infodengue`, `POST /infodengue`, `GET /noticias`) |
| Robustez | App funciona sem a API no ar | Sim (leitura local como alternativa) |
| IA local integrada | Operações de IA na API e na interface | 4 operações (resumo, sentimento, perguntas, relatório), 1 rota `POST /noticias/{id}/processar`, 1 botão por operação |
| Respostas estruturadas | Padrão de resposta | Título, operação, resultado, resumo final e aviso de erro do modelo em toda resposta |
| Robustez | Erros tratados com orientação ao usuário | 8 tipos de erro de IA/dados/entrada com mensagem e sugestão; erros de IA identificados como tal |
| Qualidade de engenharia | Testes automatizados e arquitetura | 150 testes (com FakeLLM) e regra de dependência verificada por teste |
| Qualidade do texto de entrada | Limpeza do texto raspado | Rodapé, cookies, convites e manchetes soltas removidos antes de chegar à IA |
| Transparência das fontes | Fontes documentadas | Todas, no Data Summary Report |
| Uso exclusivo de dados abertos | Fontes pagas/restritas | 0 |

## 5. Público-Alvo (fictício)

Perfis hipotéticos, sem contato real com instituições, apenas para orientar o design:
- **Primário:** gestores de vigilância em saúde de um município como Joinville.
- **Secundário:** moradores interessados em entender a situação local.
- **Terciário:** estudantes, pesquisadores e **outras aplicações** que consumam a API.

> **Nota de escopo:** o projeto não envolve contato, parceria ou validação com a Prefeitura de Joinville ou qualquer órgão público.

## 6. Escopo do TP4

**Entregue:**
- **Escolha e justificativa do modelo** (`Docs/Project/escolha_modelo_llm.md`): Qwen3-4B-Instruct-2507 (GGUF, Q4_K_M), executado localmente com llama.cpp.
- **Rota `POST /noticias/{id}/processar`** (FastAPI): recebe o id da notícia e a operação, busca a notícia inteira no corpus (via `PrepararCorpus`), monta o prompt com `prompts.py`, consulta o modelo e devolve uma resposta estruturada (response model Pydantic).
- **Botões por operação em cada notícia** na interface (Resumir, Sentimento, Perguntar, Relatório).
- **Padrão de resposta:** título, nome da operação, resultado, resumo final (classe no caso do sentimento) e, ao final, o aviso padrão sobre erros do modelo.
- **Tratamento de erros** com mensagens amigáveis e orientação ao usuário, em todas as rotas e páginas; erros do modelo identificados como "problema com a IA e o modelo utilizado".
- **Limpeza do texto raspado** e corpus reconstruído automaticamente quando desatualizado.
- **Arquitetura hexagonal** (`Docs/Project/arquitetura.md`) com injeção de dependências, **FakeLLM** e **150 testes** automatizados.

**Fora do escopo:** contato com órgãos públicos; modelo preditivo; avaliação quantitativa da qualidade das respostas da IA (próxima etapa); integração de Copernicus, Google Earth Engine e IBGE; deploy público; autenticação da API.

## 7. Decisão técnica: Selenium não será utilizado

O enunciado prevê Selenium "se necessário". Avaliação por fonte:

| Fonte | Natureza | Ferramenta |
|---|---|---|
| InfoDengue | API REST (CSV) | `pandas`/`requests` |
| NSC Total (`/tag/dengue`) | HTML estático renderizado no servidor, com listagem paginada por URL | `requests` + BeautifulSoup |

Nenhuma exige interação com formulários ou carregamento assíncrono. Selenium acrescentaria dependência de navegador e driver, mais lentidão e fragilidade de setup, sem ganho de dados. **A decisão será reavaliada** se uma fonte futura (ex.: um portal que só carregue dados via JavaScript) exigir.

## 8. Metodologia e Ambiente

- **CRISP-DM** (ciclo analítico) + **TDSP** (artefatos, diretórios, papéis) — ver `Docs/Project/tdsp_crispdm_mapping.md`.
- Ambiente: `venv` + `requirements.txt` (versões mínimas) e `requirements-llm.txt` para a IA local (**requer Python 3.12**); Git/GitHub para versionamento.
- Execução: API (`uvicorn`) e app (`streamlit`) em processos separados; ver README.

## 9. Stakeholders (papéis do projeto, não instituições reais)

| Papel | Responsável |
|---|---|
| Product Owner / Solicitante | Disciplina de IA Generativa e ESG |
| Equipe de execução | Aluno(s) de Ciência de Dados |
| Orientador acadêmico | Professor(a) da disciplina |
| Parte interessada (fictícia) | Perfil de gestor de saúde pública |
| Fontes oficiais (públicas, sem contato direto) | InfoDengue, NSC Total, SINAN/DATASUS, Copernicus, GEE, IBGE |

## 10. Riscos

- O HTML do NSC Total pode mudar e quebrar o scraper (mitigação: seletores baseados em cabeçalhos e meta tags, não em classes CSS).
- API do InfoDengue indisponível (mitigação: amostra local no mesmo schema; o app informa a origem dos dados).
- A API e o app compartilham arquivos em disco: adequado para este porte, mas não para múltiplos usuários simultâneos (fora do escopo; em produção seria um banco de dados).
- A API não tem autenticação: aceitável localmente; necessária antes de qualquer exposição pública.
- **Modelo local em computador modesto:** sem placa de vídeo compatível, cada resposta leva de 1 a 3 minutos (estimativa). Mitigação: limite de tempo, uma inferência por vez, aviso na interface e opção de usar a GPU.
- **Python 3.14:** não há versão pronta do `llama-cpp-python`; usar Python 3.12 para a IA.
- **Respostas incorretas da IA:** aviso padrão em toda resposta; avaliação sistemática na próxima etapa.
- Dados em LLM: respostas devem ser ancoradas no corpus (templates de Q&A já instruem "somente o contexto") para reduzir alucinação.
- Granularidade municipal do InfoDengue/SINAN; correlações ambientais sem validação estatística (fora de escopo).

## 11. Cronograma

| Fase | Entrega |
|---|---|
| TP1 | Proposta, planejamento e demo básica |
| TP2 | Interface dinâmica, scraping (BeautifulSoup), API InfoDengue, cache/sessão, upload/download |
| TP3 | Multipáginas, FastAPI, preparação para LLM, documentação revisada |
| **TP4 (atual)** | LLM local na API e na interface, arquitetura hexagonal, tratamento de erros, testes |
| Próxima etapa | Avaliação da qualidade da IA e finalização do projeto |
