import pandas as pd
import streamlit as st

import common
import data_ops
import data_service

st.title("📂 Upload e Download")
st.markdown(
    """
    Envie um CSV **no formato da API do InfoDengue** (mínimo: `id`, `SE`, `nivel`).
    As linhas novas são somadas aos dados atuais e passam a aparecer no **Painel**.
    Se um `id` já existir, a linha **original** é mantida e a enviada é ignorada.
    """
)

arquivo = st.file_uploader("Selecione um arquivo CSV", type=["csv"])
if arquivo is not None:
    try:
        novo = pd.read_csv(arquivo)
        faltando = {"id", "SE", "nivel"} - set(novo.columns)
        if faltando:
            st.error(f"Colunas obrigatórias ausentes: {', '.join(sorted(faltando))}")
        else:
            st.write("Prévia:")
            st.dataframe(novo.head())
            if st.button("Mesclar com os dados atuais"):
                resumo, canal = data_service.enviar_infodengue(novo)
                common.invalidar_dados()
                st.success(f"Adicionadas: {resumo['adicionadas']} · ignoradas por id repetido: "
                           f"{resumo['ignoradas_por_id_repetido']} · total: {resumo['total']}")
                common.badge_canal(canal)
    except Exception as exc:
        st.error(f"Não foi possível processar o arquivo: {exc}")

st.divider()
atual, _ = common.infodengue_cache(None, None, (), common.versao_dados())
st.markdown(f"**Dados atuais:** {len(atual)} linhas.")
st.download_button("⬇️ Baixar CSV resultante", atual.to_csv(index=False).encode("utf-8"),
                   "infodengue_joinville_atualizado.csv", "text/csv")

if data_ops.UPLOADS_CSV.exists():
    if st.button("↩️ Descartar dados enviados e voltar ao original"):
        data_ops.resetar_uploads()
        common.invalidar_dados()
        st.rerun()
