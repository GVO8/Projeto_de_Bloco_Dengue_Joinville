import requests
import streamlit as st

import data_service

st.title("🔌 Explorar a API")
st.markdown(
    f"API FastAPI em `{data_service.API_URL}`. Para iniciar, em outro terminal, na raiz do projeto:\n\n"
    "```\npython -m uvicorn main:app --app-dir Code/api --port 8000\n```"
)

if data_service.api_disponivel():
    st.success(f"API no ar. Documentação Swagger: {data_service.API_URL}/docs")
else:
    st.warning("API fora do ar. As demais páginas continuam funcionando com leitura local.")
    st.stop()

st.subheader("GET /infodengue")
c1, c2, c3 = st.columns(3)
se_i = c1.number_input("se_inicio (AAAASS)", value=0, step=1, help="0 = sem filtro")
se_f = c2.number_input("se_fim (AAAASS)", value=0, step=1, help="0 = sem filtro")
niveis = c3.multiselect("nivel", [1, 2, 3, 4])
if st.button("Executar GET /infodengue"):
    params = {"se_inicio": se_i or None, "se_fim": se_f or None, "nivel": niveis}
    r = requests.get(f"{data_service.API_URL}/infodengue", params=params, timeout=10)
    st.code(r.url)
    st.json({**r.json(), "dados": r.json()["dados"][:5]}, expanded=1)
    st.caption("Exibindo apenas as 5 primeiras linhas.")

st.subheader("GET /noticias")
busca = st.text_input("busca (trecho do título)", key="busca_api")
if st.button("Executar GET /noticias"):
    r = requests.get(f"{data_service.API_URL}/noticias", params={"busca": busca or None}, timeout=10)
    st.code(r.url)
    st.json(r.json(), expanded=1)

st.subheader("POST /infodengue")
st.markdown("Use a página **Upload e Download** (ela envia o CSV por POST quando a API está no ar) "
            "ou o Swagger em `/docs`.")
