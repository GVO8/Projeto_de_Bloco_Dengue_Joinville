import streamlit as st

from dengue.adapters.inbound.ui_streamlit import componentes as ui
from dengue.adapters.inbound.ui_streamlit.deps import obter_gateway
from dengue.core.domain.erros import ApiIndisponivelError
from dengue.core import prompts_chat
from dengue.core.prompts import PROMPTS, VERSAO

st.title("🤖 Assistente de IA (modelo local)")
st.caption("A IA roda no seu computador (sem nuvem). O modelo é carregado na primeira vez que você usa um botão.")

with ui.protegido():
    try:
        m = obter_gateway().estado()["modelo_ia"]
        st.success(f"Modelo: **{m['nome']}** · {'pronto' if m['pronto'] else 'ainda não disponível'}")
        if not m["pronto"]:
            st.info(f"**O que fazer:** {m['detalhe']}. Rode `python Code/cli.py baixar-modelo`.")
    except ApiIndisponivelError as e:
        ui.exibir_erro(e)

    st.subheader("Operações e dados de entrada")
    st.table([{"Operação": v["titulo"], "Dados de entrada": v["dados_de_entrada"]} for v in PROMPTS.values()])
    st.subheader(f"Templates de prompt (v{VERSAO})")
    for p in PROMPTS.values():
        with st.expander(p["titulo"]):
            st.code(p["template"], language="text")

    st.subheader(f"Conversa com os dados (prompts v{prompts_chat.VERSAO})")
    st.markdown("A pergunta passa por **duas chamadas ao modelo**: uma gera o plano da consulta ao InfoDengue (em JSON) e outra redige a resposta "
                "a partir dos fatos calculados em código.")
    for nome, template in prompts_chat.TEMPLATES.items():
        with st.expander(f"Prompt: {nome}"):
            st.code(template, language="text")
