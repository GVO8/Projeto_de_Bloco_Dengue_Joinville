import pandas as pd
import streamlit as st

from dengue.adapters.inbound.ui_streamlit import componentes as ui
from dengue.adapters.inbound.ui_streamlit.deps import obter_gateway

st.title("📂 Upload e Download")
st.markdown("Envie um CSV **no formato da API do InfoDengue** (mínimo: `id`, `SE`, `nivel`). As linhas novas se somam aos dados "
            "atuais. Se um `id` já existir, a linha **original** é mantida.")

gw = obter_gateway()
with ui.protegido():
    arquivo = st.file_uploader("Selecione um arquivo CSV", type=["csv"])
    if arquivo is not None:
        try:
            novo = pd.read_csv(arquivo)
        except Exception:
            st.error("⚠️ Não foi possível ler esse arquivo como CSV.")
            st.info("**O que fazer:** confirme que é um CSV separado por vírgulas, salvo em UTF-8, e envie de novo.")
        else:
            st.write("Prévia:")
            st.dataframe(novo.head())
            if st.button("Mesclar com os dados atuais"):
                resumo, canal = gw.enviar_infodengue(novo)
                ui.invalidar_dados()
                st.success(f"Adicionadas: {resumo['adicionadas']} · ignoradas por id repetido: "
                           f"{resumo['ignoradas_por_id_repetido']} · total: {resumo['total']}")
                ui.selo_canal(canal)

with ui.protegido():
    st.divider()
    atual, _ = ui.infodengue_cache(gw, None, None, (), ui.versao_dados())
    st.markdown(f"**Dados atuais:** {len(atual)} linhas.")
    st.download_button("⬇️ Baixar CSV resultante", atual.to_csv(index=False).encode("utf-8"),
                       "infodengue_joinville_atualizado.csv", "text/csv")
    if st.button("↩️ Descartar dados enviados e voltar ao original"):
        gw.resetar_uploads()
        ui.invalidar_dados()
        st.rerun()
