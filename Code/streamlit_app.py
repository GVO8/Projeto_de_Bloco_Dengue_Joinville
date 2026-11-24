"""
App Streamlit (adaptador de entrada da interface).  Uso (raiz do projeto):
    python -m streamlit run Code/streamlit_app.py
"""

import streamlit as st

st.set_page_config(page_title="Dengue em Múltiplas Dimensões — Joinville/SC", page_icon="🦟", layout="wide")

V = "dengue/adapters/inbound/ui_streamlit/views"
st.navigation({
    "Dashboard": [st.Page(f"{V}/dashboard.py", title="Dashboard", icon="📊", default=True),
                  st.Page(f"{V}/chat.py", title="Converse com os dados", icon="💬")],
    "Análises": [st.Page(f"{V}/noticias.py", title="Notícias e IA", icon="📰"),
                 st.Page(f"{V}/painel.py", title="Alertas de 2026", icon="📈")],
    "Dados e API": [st.Page(f"{V}/upload.py", title="Upload e Download", icon="📂"),
                    st.Page(f"{V}/api_page.py", title="Explorar a API", icon="🔌")],
    "Projeto": [st.Page(f"{V}/inicio.py", title="Sobre o projeto", icon="📌"),
                st.Page(f"{V}/ia.py", title="Assistente de IA", icon="🤖")],
}).run()
