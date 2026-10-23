# Mapeamento CRISP-DM × TDSP — Dengue em Múltiplas Dimensões

| Fase CRISP-DM | Fase TDSP | Artefatos do projeto | Diretório |
|---|---|---|---|
| Entendimento do Negócio | Business Understanding | Project Charter | `Docs/Project/` |
| Entendimento dos Dados | Data Acquisition & Understanding | Data Summary Report, amostras | `Docs/DataReport/`, `Data/Raw/` |
| Preparação dos Dados | Data Acquisition & Understanding | Scraper, cliente InfoDengue, `data_ops`, corpus para LLM | `Code/scraping/`, `Code/utils/`, `Code/llm_prep/`, `Data/Processed/` |
| Modelagem | Modeling | Prompts/LLM (próxima etapa) | `Code/llm_prep/` |
| Avaliação | Modeling / Acceptance | KPIs do Charter; avaliação de LLM (futura) | `Docs/Project/` |
| Implantação | Deployment | API FastAPI e app Streamlit multipágina | `Code/api/`, `Code/app/` |
| (transversal) | Customer Acceptance | Documentação, README, apresentações | `Docs/` |

**Papéis (TDSP) no projeto:** Solution Architect/Project Lead (escopo, arquitetura); Data Scientist (dados e, depois, LLM); Data Engineer (scraping, API); Stakeholder de negócio (fictício).
