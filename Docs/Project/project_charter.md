# Project Charter — Dengue em Múltiplas Dimensões (Joinville/SC)

**Versão final — TP2 · Projeto de IA Generativa e ESG · Ciência de Dados**

---

## 1. Contexto e Justificativa (Background)

Joinville (SC) está numa região historicamente pouco afetada por dengue, mas
o aumento das temperaturas médias e a expansão do *Aedes aegypti* para o Sul
do Brasil tornam o município vulnerável a surtos. Sistemas nacionais de
alerta epidemiológico (baseados em notificação de casos, como o próprio
InfoDengue) já existem e são referência consolidada nessa frente — por isso
este projeto não busca replicá-los, mas sim **usar seus dados como uma das
dimensões de um painel mais amplo**, que também reúne clima, sensoriamento
remoto, densidade populacional e conteúdo textual de notícias públicas.

## 2. Problema de Negócio

**Como reunir, num único painel interativo, indicadores públicos de
epidemiologia, clima, sensoriamento remoto (satélite) e densidade
populacional para Joinville/SC — complementados por notícias públicas
recentes — tornando visíveis dimensões de risco de dengue que vão além da
simples contagem de casos notificados?**

## 3. Pilar ESG e ODS Atendidos

| Pilar ESG | Como o projeto se conecta |
|---|---|
| **Social (S)** | Saúde pública, prevenção de doença negligenciada |
| **Governança (G)** | Transparência de dados públicos, consolidação de fontes oficiais dispersas |

**ODS principal — ODS 3 (Saúde e Bem-Estar)**, meta 3.3: até 2030, acabar com
as epidemias de doenças tropicais negligenciadas, entre elas a dengue.

**ODS secundários:**
- **ODS 11 (Cidades e Comunidades Sustentáveis)** — leitura territorial de indicadores ambientais e populacionais.
- **ODS 17 (Parcerias e Meios de Implementação)** — uso exclusivo de dados e conteúdo públicos e gratuitos (SINAN, InfoDengue, Copernicus, Google Earth Engine, IBGE, NSC Total).

## 4. Metas e Indicadores de Sucesso (KPIs)

| Meta | Indicador | Status ao final do TP2 |
|---|---|---|
| Consolidar múltiplas fontes públicas num só painel | Nº de dimensões de dados integradas | 2 integradas tecnicamente (InfoDengue via API, notícias via scraping) + SINAN (amostra) documentadas |
| Painel interativo e funcional | Nº de funcionalidades dinâmicas implementadas | Abas, filtro por período, upload, download, cache, nuvem de palavras |
| Performance e persistência | Uso de cache e estado de sessão | Implementado (`st.cache_data`, `st.session_state`) |
| Transparência da fonte | Rastreabilidade da origem de cada indicador | Documentada no Data Summary Report |
| Uso exclusivo de dados abertos | Nº de fontes pagas ou de acesso restrito | 0 |
| Extensibilidade pelo usuário | Serviço de upload/download funcional | Implementado, com regra de deduplicação por `id` |

## 5. Público-Alvo

Definido de forma **fictícia**, sem contato real ou articulação com
instituições, apenas como referência de perfil de usuário para orientar o
design do painel:

- **Primário (fictício):** gestores de vigilância em saúde de um município como Joinville.
- **Secundário (fictício):** população local interessada em entender fatores de risco de dengue na sua região.
- **Terciário:** estudantes e pesquisadores de ciência de dados aplicada à saúde pública.

> **Nota de escopo:** este projeto não envolve, em nenhuma etapa, contato,
> parceria ou validação com a Prefeitura de Joinville ou qualquer órgão
> público. Todas as referências a "partes interessadas" são hipotéticas.

## 6. Escopo do TP2

**Entregue nesta etapa:**
- Configuração do ambiente de desenvolvimento (`requirements.txt`, `.gitignore`, estrutura pronta para controle de versão via Git/GitHub).
- Interface Streamlit reorganizada em abas, com filtros dinâmicos (slider de período).
- Web scraping com BeautifulSoup de notícias do NSC Total (Joinville + Dengue), executado como script separado, com saída em CSV e TXT.
- Consumo da API pública do InfoDengue (`alertcity`) para Joinville/SC, com gráfico de linha temporal — uma linha por nível de alerta — para o ano de 2026.
- Cache (`st.cache_data`) e estado de sessão (`st.session_state`) para performance e persistência entre interações.
- Serviço de upload de CSV (mesmo formato da API), mesclado por `id` com a base atual (id novo é descartado em caso de conflito).
- Serviço de download do CSV resultante do gráfico, disponível antes ou depois de um upload.
- Nuvem de palavras e estatísticas básicas a partir do conteúdo textual raspado.
- Finalização deste Project Charter e do Data Summary Report.

**Fora do escopo do TP2:**
- Qualquer contato ou validação com órgãos públicos.
- Modelo preditivo treinado.
- Integração real com Copernicus, Google Earth Engine e IBGE (documentadas como fontes previstas, não implementadas nesta etapa).
- Deploy em produção (preparação de ambiente incluída; publicação efetiva é etapa futura).

## 7. Metodologia

- **CRISP-DM** para o ciclo analítico.
- **TDSP (Team Data Science Process)** para organização de artefatos, papéis e diretórios (ver `Docs/Project/tdsp_crispdm_mapping.md`).

## 8. Configuração do Ambiente e Controle de Versão

- **Ambiente:** `venv` (Python), dependências fixadas em `requirements.txt`.
- **Controle de versão:** Git, com `.gitignore` configurado para excluir ambientes virtuais e arquivos sensíveis.
- **Repositório remoto:** GitHub (o projeto é entregue como pacote `.zip` pronto para `git init` + push a um repositório remoto).
- **Preparação para deploy:** estrutura compatível com Streamlit Community Cloud (basta apontar para `Code/app/app.py` e o `requirements.txt` na raiz).

## 9. Stakeholders (papéis do projeto, não instituições reais)

| Papel | Responsável |
|---|---|
| Product Owner / Solicitante | Disciplina de IA Generativa e ESG |
| Equipe de execução | Aluno(s) do curso de Ciência de Dados |
| Orientador acadêmico | Professor(a) da disciplina |
| Parte interessada (fictícia) | Perfil de gestor de saúde pública, sem vínculo institucional real |
| Fontes de dados oficiais (públicas, sem contato direto) | SINAN/DATASUS, InfoDengue, NSC Total, Copernicus, Google Earth Engine, IBGE |

## 10. Riscos Identificados

- Estrutura HTML do NSC Total pode mudar e quebrar o scraper (mitigação: seletores baseados em padrões estáveis — cabeçalhos `<h2>` e meta tags — em vez de classes CSS específicas).
- Disponibilidade da API do InfoDengue pode falhar (mitigação: fallback local implementado no app).
- Granularidade do SINAN é municipal, não por bairro.
- Correlação entre indicadores ambientais e risco pode ser espúria sem validação estatística formal (fora do escopo do TP2).

## 11. Cronograma (alto nível)

| Fase | Entrega |
|---|---|
| TP1 | Proposta, planejamento inicial, demo Streamlit básica |
| TP2 (atual) | Interface dinâmica, scraping, API InfoDengue, cache/sessão, upload/download, documentação finalizada |
| Próximas etapas | Integração real de Copernicus/GEE/IBGE, modelagem preditiva, deploy público |
