# Project Charter — Dengue em Joinville: dados, mídia e IA em linguagem natural

**Versão final — TP5 · Projeto de Bloco · Ciência de Dados Aplicada**
Histórico: TP1 (proposta) → TP2 (interface, scraping, upload/download) → TP3 (multipáginas, FastAPI) → TP4 (IA local na API, arquitetura hexagonal) → **TP5 (conversa com os dados, dashboard final)**.

---

## 1. Contexto e justificativa

A dengue é um problema de saúde pública crescente no Sul do Brasil: o aumento das temperaturas permite que o *Aedes aegypti* circule em regiões antes pouco afetadas, como Joinville (SC). Os dados para acompanhá-la existem e são públicos — o **InfoDengue** publica, por API, a série semanal de casos e o nível de alerta de cada município —, mas têm dois obstáculos:

1. **Acesso técnico.** Obter, limpar e comparar anos exige conhecimento de APIs, semanas epidemiológicas e programação. Um morador, um jornalista ou um gestor sem formação técnica dificilmente responde sozinho a *"foi o ano com mais casos?"* ou *"os casos subiram em relação ao ano passado?"*.
2. **Ausência da dimensão humana.** Os números não dizem **o que a população está sendo levada a sentir**. A mídia local é o canal pelo qual a maioria das pessoas toma conhecimento da situação, e o tom das notícias é um sinal indireto da preocupação veiculada.

## 2. Problema de negócio

**Como tornar os dados públicos de dengue de Joinville acessíveis a qualquer pessoa, em linguagem natural, e relacioná-los à preocupação veiculada pela mídia, com uma IA que roda localmente, é auditável e não inventa números?**

### Justificativa da solução (o que o projeto traz de novo)
- **Democratizar o acesso à informação (ODS 16.10).** O usuário pergunta em português e recebe uma resposta baseada nos dados. Não precisa conhecer a API, a semana epidemiológica ou o pandas.
- **A mídia como fonte de análise da preocupação.** Notícias reais são coletadas por *web scraping* e classificadas por IA quanto ao tom (tranquilizador, neutro, preocupante). O painel as coloca ao lado da curva de casos.
- **Confiança por construção.** Os números **não** vêm da IA: são calculados em código a partir da resposta do InfoDengue. A IA apenas interpreta a pergunta e redige a resposta. Toda resposta mostra a requisição feita e os fatos usados, e traz o aviso de que o modelo pode errar.

## 3. Fontes de dados (únicas, públicas e gratuitas)

| Fonte | O que fornece | Observação |
|---|---|---|
| **InfoDengue** (API) | Série semanal de dengue em Joinville: casos notificados, nível de alerta e outros indicadores | O InfoDengue já consolida notificações do SINAN, dados climáticos e estimativas populacionais do IBGE; por isso esses dados não são tratados como fontes separadas |
| **NSC Total** (web scraping) | Notícias sobre dengue em Joinville | Texto limpo, classificado por IA |

Qualquer outra fonte (satélite, clima, população) está **fora do escopo**; o projeto herda esses dados apenas indiretamente, por meio do InfoDengue.

## 4. Pilares ESG e ODS

| Pilar | Como o projeto se conecta |
|---|---|
| **Social (S)** | Saúde pública e acesso à informação: qualquer cidadão consegue consultar a situação da dengue sem conhecimento técnico |
| **Governança (G)** | Transparência e uso responsável de IA: modelo **local** (nenhum texto sai da máquina), escopo restrito (só dengue em Joinville), números auditáveis, aviso de limitações e erros tratados com orientação |

O pilar Ambiental aparece só de forma indireta (o InfoDengue incorpora clima em seus modelos); o projeto não trata indicadores ambientais.

- **ODS 3 — Saúde e Bem-Estar** (meta 3.3, doenças tropicais negligenciadas): principal.
- **ODS 16 — Paz, Justiça e Instituições Eficazes** (meta 16.10, acesso público à informação): a conversa em linguagem natural democratiza dados públicos.
- **ODS 17 — Parcerias e Meios de Implementação**: uso exclusivo de dados abertos.

## 5. Metas e indicadores (KPIs)

| Meta | Indicador | Resultado |
|---|---|---|
| Responder perguntas em linguagem natural com base nos dados | As 4 perguntas-modelo (pico, ano com mais casos, ano com menos casos, comparação com o ano anterior) respondidas a partir de uma requisição ao InfoDengue | Implementado; coberto por testes com respostas conhecidas |
| Restringir o escopo | Perguntas de outras cidades, outros territórios, outros assuntos e tentativas de alterar as regras são recusadas | Implementado (3 camadas); recusa sem gastar IA nos casos óbvios |
| Números confiáveis | Números calculados em código, nunca pela IA; ano em andamento tratado à parte; comparação nas mesmas semanas | Implementado e testado |
| Memória conversacional | Perguntas de continuação ("e em 2024?") entendidas | Implementado, por sessão, com janela de 3 turnos |
| Mídia como sinal de preocupação | Sentimento de cada notícia, cruzado com a curva de casos | Implementado; classificação roda em lote (`analisar-sentimentos`) |
| Dashboard simples e profundo | KPIs, ciclo de dados, 3 gráficos de casos, mídia e conversa | Implementado |
| Robustez | Erros com mensagem e sugestão; erros de IA identificados | 18 códigos de erro, cada um com HTTP, mensagem e sugestão próprios |
| Qualidade de engenharia | Testes automatizados e arquitetura verificada | 314 testes (FakeLLM), regra de dependência testada, verificação por mutação |
| **Evidência real do modelo** | Chamada real, com tempo medido na máquina do projeto | **Pendente de execução do aluno** (ver `Docs/Evidencias/`) |

## 6. Argumentação: dados, IA e engenharia de prompts a serviço do problema

1. **Dados.** A série do InfoDengue responde *o quê* (quantos casos, quando) e as notícias respondem *como isso é contado*. Sem a mídia, o painel é só mais um gráfico de casos; sem os dados, a análise de sentimento é opinião solta.
2. **Por que IA generativa.** O obstáculo é a linguagem: transformar "os casos subiram?" em uma consulta e a resposta em frase. Isso é o que um LLM faz bem. Cálculo e verificação, que ele faz mal, ficam em código.
3. **Engenharia de prompts (versionada em `core/prompts*.py`).**
   - *Planejador:* converte a pergunta em JSON (`assunto_valido`, `cidade`, `intencao`, `ano_inicio`, `ano_fim`) com 4 exemplos (*few-shot*) e **modo JSON** do llama.cpp. O plano é validado e reconciliado por regras determinísticas; se o JSON falhar, as regras assumem.
   - *Redator:* recebe só os fatos calculados e a conversa recente; é instruído a usar **somente** esses dados, citar números, responder em até 4 frases e dizer quando a informação não existe.
   - *Sentimento:* mede a **preocupação** transmitida (NEGATIVO = preocupante, POSITIVO = tranquilizador), não a "positividade" do texto.
   - Temperatura 0,2: respostas fiéis, não criativas.
4. **Por que um modelo local.** Privacidade (nenhum texto vai a terceiros), custo zero por uso e controle total, o que é coerente com a Governança.
5. **Insight gerado.** Qualquer pessoa obtém, em um clique, afirmações como "2026 está X% acima/abaixo de 2025 nas mesmas semanas", com a requisição e os fatos que a sustentam.

## 7. Público-alvo (fictício)

Gestores de saúde pública, jornalistas e moradores de Joinville, sem contato real com instituições (nenhum órgão público foi consultado nem valida o projeto).

## 8. Escopo

**Dentro:** dados do InfoDengue (Joinville, dengue); notícias do NSC Total; sentimento por IA; conversa em linguagem natural com memória; dashboard; API FastAPI; CLI; testes; documentação.
**Fora:** outras cidades e doenças; dados de satélite, clima ou população próprios; previsão de casos; autenticação; implantação pública; validação com órgãos de saúde.

## 9. Decisões técnicas

- **Opção escolhida no TP5:** memória conversacional (Opção 1), usando o Qwen3-4B local para conversar com os dados do InfoDengue.
- **Modelo:** Qwen3-4B-Instruct-2507 (GGUF Q4_K_M) via llama.cpp (`Docs/Project/escolha_modelo_llm.md`).
- **Selenium não usado:** as duas fontes são uma API e HTML estático.
- **Sem dado sintético nas respostas:** se o InfoDengue estiver inacessível, a conversa e o dashboard informam o erro em vez de usar amostra. Uma amostra sintética existe apenas para a página "Alertas de 2026" funcionar offline e é sinalizada como tal.
- **Arquitetura hexagonal** (`Docs/Project/arquitetura.md`).

## 10. Stakeholders (papéis, não instituições)

Product Owner: disciplina · Equipe: aluno de Ciência de Dados · Orientador: professor da disciplina · Parte interessada: perfil fictício de gestor/cidadão · Fontes: InfoDengue e NSC Total (sem contato direto).

## 11. Riscos e limitações

- **O tom da notícia é indicador indireto** da preocupação veiculada; não mede a opinião da população. O painel declara isso.
- **Amostra pequena de notícias** (6 coletadas): o gráfico de mídia é ilustrativo, não estatístico. Ampliar a coleta é o caminho.
- **Casos notificados são revisados** (atraso de notificação); as últimas semanas podem mudar. As respostas avisam.
- **Modelo pequeno (4B) e hardware modesto:** pode errar na interpretação; a resposta leva de 1 a 3 minutos em CPU (estimativa a confirmar com a medição real). Mitigações: números em código, escopo restrito, aviso padrão, limite de tempo e fila de uma chamada por vez.
- **Comportamento da API do InfoDengue em consultas de vários anos** foi implementado conforme o exemplo oficial, mas **não foi verificado contra o serviço real** durante o desenvolvimento (sem acesso de rede no ambiente). Deve ser confirmado na primeira execução.
- **Guarda de escopo não é infalível:** a lista de cidades é finita e um modelo de 4B pode errar a classificação; a última camada (resposta só a partir dos dados de Joinville) limita o dano.
- **Sem autenticação e sem persistência da conversa** (memória em RAM; perde-se ao reiniciar a API).

## 12. Cronograma

| TP | Entrega |
|---|---|
| TP1 | Proposta e planejamento |
| TP2 | Interface, scraping, API InfoDengue, upload/download |
| TP3 | Multipáginas, FastAPI, preparação para LLM |
| TP4 | IA local na API, arquitetura hexagonal, erros, testes |
| **TP5** | Conversa com os dados (memória), dashboard final, sentimento da mídia, documentação e apresentação |
