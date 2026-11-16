"""
App Streamlit (adaptador de entrada da interface).  Uso (raiz do projeto):
    python -m streamlit run Code/streamlit_app.py
"""

import streamlit as st

st.set_page_config(page_title="Dengue em Múltiplas Dimensões — Joinville/SC", page_icon="🦟", layout="wide")

V = "dengue/adapters/inbound/ui_streamlit/views"
st.navigation({
    "Visão geral": [st.Page(f"{V}/inicio.py", title="Início", icon="📌", default=True)],
    "Análises": [st.Page(f"{V}/painel.py", title="Painel InfoDengue", icon="📈"),
                 st.Page(f"{V}/noticias.py", title="Notícias e IA", icon="📰")],
    "Dados e API": [st.Page(f"{V}/upload.py", title="Upload e Download", icon="📂"),
                    st.Page(f"{V}/api_page.py", title="Explorar a API", icon="🔌")],
    "Modelo": [st.Page(f"{V}/ia.py", title="Assistente de IA", icon="🤖")],
}).run()
