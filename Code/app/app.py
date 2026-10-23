"""
Dengue em Múltiplas Dimensões — App Streamlit multipágina (TP3)

Executar (raiz do projeto):
    python -m streamlit run Code/app/app.py
"""

import streamlit as st

import common  # noqa: F401  (configura sys.path)

st.set_page_config(page_title="Dengue em Múltiplas Dimensões — Joinville/SC", page_icon="🦟", layout="wide")

paginas = {
    "Visão geral": [
        st.Page("views/inicio.py", title="Início", icon="📌", default=True),
    ],
    "Análises": [
        st.Page("views/painel.py", title="Painel InfoDengue", icon="📈"),
        st.Page("views/noticias.py", title="Notícias", icon="📰"),
    ],
    "Dados e API": [
        st.Page("views/upload.py", title="Upload e Download", icon="📂"),
        st.Page("views/api_page.py", title="Explorar a API", icon="🔌"),
    ],
    "Próxima etapa": [
        st.Page("views/llm.py", title="Preparação para LLM", icon="🤖"),
    ],
}
st.navigation(paginas).run()
