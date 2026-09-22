# Dengue em Múltiplas Dimensões (TP2)

TP2 da disciplina de IA Generativa e ESG: evolução do painel que reúne
dimensões públicas de risco de dengue em Joinville/SC — agora com interface
interativa, dados em tempo real da API do InfoDengue, notícias coletadas via
*web scraping* (BeautifulSoup), cache, estado de sessão e serviço de
upload/download de arquivos.

O projeto não realiza alerta epidemiológico em tempo real (já bem coberto
pelo próprio InfoDengue) e não envolve, em nenhuma etapa, contato ou
validação com órgãos públicos — as "partes interessadas" mencionadas nos
documentos são hipotéticas.

## Estrutura do projeto (padrão TDSP)

```
dengue-esg-tp2/
├── .gitignore
├── requirements.txt
├── README.md
├── Code/
│   ├── app/
│   │   └── app.py                            # App Streamlit (abas, cache, sessão, upload/download)
│   ├── scraping/
│   │   └── scrape_nsc_dengue.py               # Scraper BeautifulSoup (executar separadamente)
│   └── utils/
│       └── infodengue_api.py                  # Cliente da API do InfoDengue
├── Data/
│   ├── Raw/
│   │   ├── sinan_sample.csv                   # Amostra SINAN (TP1)
│   │   ├── infodengue_sample.csv              # Fallback local (mesmo schema da API)
│   │   ├── nsc_noticias_joinville_dengue.csv  # Saída do scraper (metadados)
│   │   └── nsc_noticias_texto.txt             # Saída do scraper (corpus para nuvem de palavras)
│   └── Processed/
├── Docs/
│   ├── Project/
│   │   ├── project_charter.md                 # Finalizado
│   │   └── tdsp_crispdm_mapping.md
│   ├── DataReport/
│   │   └── data_summary_report.md             # Finalizado
│   └── Presentations/
```

## Como rodar

```bash
# 1. Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. (Opcional) Rodar o scraper para atualizar as notícias
python Code/scraping/scrape_nsc_dengue.py

# 4. Rodar o app
streamlit run Code/app/app.py
```

> O app já vem com uma amostra de notícias e um fallback local dos dados do
> InfoDengue em `Data/Raw/`, então funciona mesmo sem rodar o scraper ou sem
> internet — mas os dados "ao vivo" só aparecem com conexão ativa.

## Controle de versão (Git + GitHub)

```bash
git init
git add .
git commit -m "TP2: interface dinâmica, scraping NSC Total, API InfoDengue, cache/sessão, upload/download"

# Criar o repositório no GitHub e então:
git remote add origin <URL_DO_SEU_REPOSITORIO>
git branch -M main
git push -u origin main
```

O `.gitignore` já está configurado para não versionar ambientes virtuais
(`.venv/`), caches do Python e arquivos de segredos do Streamlit.

## Preparação para deploy (Streamlit Community Cloud)

1. Suba o repositório para o GitHub (passo acima).
2. Em [share.streamlit.io](https://share.streamlit.io), aponte para o
   repositório e defina `Code/app/app.py` como arquivo principal.
3. O `requirements.txt` na raiz é detectado automaticamente.

## Documentos principais

- [Project Charter](Docs/Project/project_charter.md)
- [Mapeamento CRISP-DM × TDSP](Docs/Project/tdsp_crispdm_mapping.md)
- [Data Summary Report](Docs/DataReport/data_summary_report.md)
