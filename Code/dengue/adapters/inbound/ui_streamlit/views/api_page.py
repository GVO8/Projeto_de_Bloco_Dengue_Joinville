import requests
import streamlit as st

from dengue.adapters.inbound.ui_streamlit import componentes as ui
from dengue.adapters.inbound.ui_streamlit.deps import obter_gateway
from dengue.core.domain.erros import ApiIndisponivelError

st.title("🔌 Explorar a API")
st.markdown("Para iniciar a API, em outro terminal na raiz do projeto: `python Code/run_api.py`")

gw = obter_gateway()
with ui.protegido():
    try:
        estado = gw.estado()
    except ApiIndisponivelError as e:
        ui.exibir_erro(e)
        st.stop()
    st.success("API no ar. Documentação interativa em `/docs`.")
    m = estado["modelo_ia"]
    st.write(f"**Modelo de IA:** {m['nome']} — "
             f"{'pronto' if m['pronto'] else 'NÃO pronto (' + m['detalhe'] + ')'}; "
             f"{'carregado na memória' if m['carregado'] else 'ainda não carregado (carrega no primeiro uso)'}.")

    st.subheader("Rotas")
    st.table([
        {"Método": "GET", "Rota": "/health", "Função": "Estado da API e do modelo"},
        {"Método": "GET", "Rota": "/operacoes", "Função": "Operações de IA disponíveis"},
        {"Método": "GET / POST", "Rota": "/infodengue", "Função": "Consulta / envia linhas da série"},
        {"Método": "DELETE", "Rota": "/infodengue/uploads", "Função": "Descarta dados enviados"},
        {"Método": "GET", "Rota": "/noticias, /noticias/{id}, /noticias/texto", "Função": "Notícias coletadas"},
        {"Método": "POST", "Rota": "/noticias/{id}/processar", "Função": "Processa a notícia com a IA"},
    ])
