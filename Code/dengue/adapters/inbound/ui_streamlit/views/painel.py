import plotly.graph_objects as go
import streamlit as st

from dengue.adapters.inbound.ui_streamlit import componentes as ui
from dengue.adapters.inbound.ui_streamlit.deps import obter_gateway
from dengue.core.domain.modelos import NIVEL_LABELS

st.title("📈 Painel InfoDengue — Joinville/SC, 2026")

with ui.protegido():
    niveis_sel = st.sidebar.multiselect("Níveis de alerta exibidos", list(NIVEL_LABELS), list(NIVEL_LABELS),
                                        format_func=lambda n: NIVEL_LABELS[n])
    completo, canal = ui.infodengue_cache(obter_gateway(), None, None, (), ui.versao_dados())
    ui.selo_canal(canal)

    if completo.empty or not {"SE", "nivel"} <= set(completo.columns):
        st.error("⚠️ Os dados carregados não têm as colunas 'SE' e 'nivel'.")
        st.info("**O que fazer:** use a página Upload e Download para restaurar os dados originais.")
        st.stop()

    se_min, se_max = int(completo["SE"].min()), int(completo["SE"].max())
    faixa = (se_min, se_max) if se_min == se_max else st.slider("Semanas epidemiológicas (SE)", se_min, se_max, (se_min, se_max))
    df = completo[(completo["SE"] >= faixa[0]) & (completo["SE"] <= faixa[1])]

    fig = go.Figure()
    for n in niveis_sel:
        fig.add_trace(go.Scatter(x=df["SE"], y=(df["nivel"] == n).astype(int), mode="lines", name=NIVEL_LABELS[n],
                                 line=dict(shape="hv", width=3, color=ui.COR_NIVEL[n])))
    fig.update_layout(xaxis_title="Semana Epidemiológica (SE)", legend_title="Nível de alerta", height=420,
                      yaxis=dict(title="Nível ativo", tickvals=[0, 1], ticktext=["Não", "Sim"], range=[-0.2, 1.2]),
                      margin=dict(t=20, b=20))
    st.plotly_chart(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Semanas no período", len(df))
    if "casos" in df.columns:
        m2.metric("Casos (soma)", int(df["casos"].sum()))
    m3.metric("Semanas em nível 3 ou 4", int((df["nivel"] >= 3).sum()))
    with st.expander("Tabela de dados do gráfico"):
        st.dataframe(df)
    st.download_button("⬇️ Baixar CSV dos dados", completo.to_csv(index=False).encode("utf-8"),
                       "infodengue_joinville_2026.csv", "text/csv")
