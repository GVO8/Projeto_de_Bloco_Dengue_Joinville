# Mapeamento CRISP-DM × TDSP — Dengue em Múltiplas Dimensões

| Fase CRISP-DM | Fase TDSP | Artefatos do projeto | Local |
|---|---|---|---|
| Entendimento do Negócio | Business Understanding | Project Charter | `Docs/Project/` |
| Entendimento dos Dados | Data Acquisition & Understanding | Data Summary Report, amostras | `Docs/DataReport/`, `Data/Raw/` |
| Preparação dos Dados | Data Acquisition & Understanding | Coletor, cliente InfoDengue, limpeza e corpus | `Code/dengue/adapters/outbound/`, `core/services/corpus.py`, `Data/Processed/` |
| Modelagem | Modeling | Escolha do LLM, prompts (notícias e conversa), `ProcessarNoticia`, `ConversarComDados`, cálculo de fatos | `Docs/Project/escolha_modelo_llm.md`, `core/prompts*.py`, `core/services/` |
| Avaliação | Modeling / Acceptance | KPIs do Charter; testes automatizados; avaliação de qualidade da IA (próxima etapa) | `Tests/`, `Docs/Project/` |
| Implantação | Deployment | API FastAPI, dashboard e conversa em Streamlit, CLI | `Code/dengue/adapters/inbound/`, `Code/*.py` |
| (transversal) | Customer Acceptance | Documentação, arquitetura, README, apresentação, evidências | `Docs/`, `Docs/Apresentacao/`, `Docs/Evidencias/` |

**Papéis (TDSP):** Solution Architect/Project Lead (escopo, arquitetura); Data Scientist (dados, prompts, avaliação); Data Engineer (coleta, API); Stakeholder de negócio (fictício).
