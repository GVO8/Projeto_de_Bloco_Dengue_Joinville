import streamlit as st

from dengue.adapters.inbound.ui_streamlit import componentes as ui
from dengue.adapters.inbound.ui_streamlit.deps import obter_gateway
from dengue.core.domain.chat import PERGUNTAS_EXEMPLO

st.title("💬 Converse com os dados do InfoDengue")
st.caption("Pergunte em linguagem natural. A IA transforma a pergunta em uma consulta ao InfoDengue (sempre **Joinville**, sempre **casos de dengue**) "
           "e responde com base nos números retornados. A conversa tem memória: você pode fazer perguntas de continuação.")

gw = obter_gateway()
estado = st.session_state
estado.setdefault("chat_mensagens", [])
estado.setdefault("chat_sessao", None)

with st.sidebar:
    if st.button("🗑️ Nova conversa", key="nova_conversa"):
        with ui.protegido():
            gw.encerrar_conversa(estado["chat_sessao"])
        estado["chat_mensagens"], estado["chat_sessao"] = [], None
        st.rerun()
    st.markdown("**Experimente:**")
    for i, exemplo in enumerate(PERGUNTAS_EXEMPLO):
        if st.button(exemplo, key=f"exemplo_{i}"):
            estado["chat_pendente"] = exemplo


def mostrar_assistente(m: dict) -> None:
    st.markdown(m["conteudo"])
    meta = m.get("meta")
    if meta and meta["tipo"] == "resposta":
        with st.expander("Como a resposta foi obtida"):
            plano = meta.get("plano") or {}
            st.markdown(f"**1. A IA interpretou a pergunta** (origem do plano: {plano.get('origem')}) → intenção `{plano.get('intencao')}`, "
                        f"anos {plano.get('ano_inicio')}–{plano.get('ano_fim')}.")
            if meta.get("requisicao"):
                st.markdown("**2. Requisição feita ao InfoDengue:**")
                st.code(meta["requisicao"]["url"], language="text")
            st.markdown("**3. Fatos calculados em código (os números vêm daqui, não da IA):**")
            st.text(meta.get("fatos") or "")
            st.markdown("**4. A IA redigiu a resposta usando esses fatos.**")
            st.table([{"Etapa": e["nome"], "Tempo (s)": e["tempo_segundos"], "Tokens": e.get("tokens_gerados")} for e in meta["etapas"]])
        for aviso in meta.get("avisos", []):
            st.caption(f"ℹ️ {aviso}")
    if meta:
        st.caption(f"Modelo: {meta['modelo']} · {meta['tempo_segundos']} s · {meta['aviso_padrao']}")


for m in estado["chat_mensagens"]:
    with st.chat_message(m["papel"]):
        mostrar_assistente(m) if m["papel"] == "assistant" else st.markdown(m["conteudo"])

pergunta = estado.pop("chat_pendente", None) or st.chat_input("Pergunte sobre casos de dengue em Joinville…", max_chars=300)
if pergunta:
    estado["chat_mensagens"].append({"papel": "user", "conteudo": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with ui.protegido():
            with st.spinner("A IA está interpretando a pergunta, consultando o InfoDengue e redigindo a resposta… "
                            "em computadores sem placa de vídeo compatível isso pode levar alguns minutos."):
                resp = gw.perguntar(estado["chat_sessao"], pergunta)
            estado["chat_sessao"] = resp["sessao_id"]
            msg = {"papel": "assistant", "conteudo": resp["resposta"], "meta": resp}
            estado["chat_mensagens"].append(msg)
            mostrar_assistente(msg)
