import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dengue.adapters.inbound.ui_streamlit import componentes as ui
from dengue.adapters.inbound.ui_streamlit.deps import obter_gateway
from dengue.core.domain.modelos import NIVEL_LABELS, ROTULOS_SENTIMENTO

st.title("📊 Dengue em Joinville/SC — do dado ao insight")
st.caption("Dados reais do InfoDengue e notícias reais coletadas na web, interpretados por uma IA local. "
           "Tudo marcado como **calculado** vem de código; o que é **IA** é identificado.")

gw = obter_gateway()
with ui.protegido():
    historico = ui.historico_cache(gw, None, None, ui.versao_dados())
    serie, fatos = historico["serie"].copy(), historico["fatos"]
    ui.selo_canal(historico["canal"])
    anos_do_periodo = f"{fatos['periodo']['ano_inicio']}–{fatos['periodo']['ano_fim']}"

    # ------------------------------------------------------------- KPIs (calculados)
    st.subheader("Situação atual")
    ano = fatos["periodo"]["ano_fim"]
    atual = next(a for a in fatos["por_ano"] if a["ano"] == ano)
    comp, ult = fatos["comparacao"], fatos["ultima_semana"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Casos em {ano} (até a SE {atual['ultima_semana']})", f"{atual['total']:,}".replace(",", "."))
    k2.metric(f"Pico em {ano}", f"{atual['pico']['casos']:,}".replace(",", ".") + " casos", f"SE {atual['pico']['se']}", delta_color="off")
    if comp and comp["variacao_pct"] is not None:
        k3.metric(f"vs. {comp['ano_anterior']} (mesmas semanas)", f"{comp['variacao_pct']:+.1f}%".replace(".", ","),
                  f"{comp['variacao_abs']:+,} casos".replace(",", "."), delta_color="inverse")
    else:
        k3.metric("vs. ano anterior", "—")
    k4.metric("Nível de alerta atual", NIVEL_LABELS.get(ult["nivel"], "—").split(" — ")[-1] if ult["nivel"] else "—", f"SE {ult['se']}", delta_color="off")

    # ------------------------------------------------------------- ciclo de ciência de dados
    with ui.protegido():
        noticias, _ = ui.noticias_cache(gw, None, ui.versao_dados())
        sentimentos = ui.sentimentos_cache(gw, ui.versao_dados())
    n_noticias = 0 if noticias.empty else len(noticias)
    n_sent = 0 if sentimentos.empty else len(sentimentos)
    st.subheader("O ciclo de ciência de dados neste projeto")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f"**1 · Coleta**\n\nInfoDengue (API): **{len(serie)} semanas** de {anos_do_periodo}.\n\nNotícias (scraping): **{n_noticias}**.")
    c2.markdown("**2 · Preparação**\n\nLimpeza do texto das notícias e **cálculo dos fatos** (totais, picos, comparações) *em código*.")
    c3.markdown(f"**3 · IA local (Qwen3-4B)**\n\nPlaneja a consulta, classifica o **sentimento** ({n_sent}/{n_noticias} notícias), resume e responde.")
    c4.markdown("**4 · Insights**\n\nGráficos abaixo: sazonalidade, comparação entre anos e tom da mídia.")
    c5.markdown("**5 · Interação**\n\nPágina **Converse com os dados**: perguntas em linguagem natural.")

    # ------------------------------------------------------------- gráficos da série
    st.subheader("Casos de dengue ao longo dos anos (dados do InfoDengue)")
    anos = sorted(serie["ano"].unique())
    escolhidos = st.multiselect("Anos na comparação", anos, default=anos)
    fig = go.Figure()
    for a in escolhidos:
        d = serie[serie["ano"] == a].sort_values("semana")
        fig.add_trace(go.Scatter(x=d["semana"], y=d["casos"], mode="lines", name=str(a),
                                 line=dict(width=4 if a == anos[-1] else 2)))
    fig.update_layout(xaxis_title="Semana epidemiológica", yaxis_title="Casos notificados", height=380, margin=dict(t=20, b=20), legend_title="Ano")
    st.plotly_chart(fig)
    st.caption("A sazonalidade fica visível ao sobrepor os anos. O ano em andamento (linha mais grossa) termina onde os dados terminam.")

    g1, g2 = st.columns(2)
    por_ano = pd.DataFrame(fatos["por_ano"])
    barras = go.Figure(go.Bar(x=por_ano["ano"].astype(str), y=por_ano["total"],
                              marker_color=["#2980b9" if c else "#aed6f1" for c in por_ano["completo"]],
                              text=por_ano["total"], textposition="outside"))
    barras.update_layout(title="Total de casos por ano (claro = ano em andamento)", height=340, margin=dict(t=50, b=20), yaxis_title="Casos")
    g1.plotly_chart(barras)
    if "nivel" in serie.columns:
        niveis = serie.dropna(subset=["nivel"]).groupby(["ano", "nivel"]).size().unstack(fill_value=0)
        cores = {1: "#2ecc71", 2: "#f1c40f", 3: "#e67e22", 4: "#e74c3c"}
        emp = go.Figure([go.Bar(x=niveis.index.astype(str), y=niveis[n], name=NIVEL_LABELS[int(n)], marker_color=cores[int(n)]) for n in niveis.columns])
        emp.update_layout(barmode="stack", title="Semanas por nível de alerta", height=340, margin=dict(t=50, b=20), yaxis_title="Semanas")
        g2.plotly_chart(emp)

    with st.expander("Fatos calculados (sem IA)"):
        tabela = por_ano.assign(pico_se=por_ano["pico"].map(lambda p: p["se"]), pico_casos=por_ano["pico"].map(lambda p: p["casos"]))
        st.dataframe(tabela[["ano", "total", "semanas", "completo", "pico_se", "pico_casos"]])
        if fatos["ano_mais_casos"]:
            st.write(f"Ano completo com mais casos: **{fatos['ano_mais_casos']['ano']}** · com menos: **{fatos['ano_menos_casos']['ano']}**.")
        st.caption(f"Requisição: {historico['requisicao']['url']}")

    # ------------------------------------------------------------- mídia
    st.subheader("A mídia como termômetro de preocupação (análise de sentimento por IA)")
    if sentimentos.empty:
        st.info("Ainda não há notícias analisadas. **O que fazer:** na página *Notícias e IA*, use o botão **Sentimento** em cada notícia, "
                "ou rode `python Code/cli.py analisar-sentimentos` para analisar todas de uma vez.")
    else:
        contagem = sentimentos["classe"].value_counts()
        m1, m2 = st.columns([1, 2])
        pizza = go.Figure(go.Bar(x=[ROTULOS_SENTIMENTO.get(c, c) for c in contagem.index], y=contagem.values,
                                 marker_color=[ui.COR_SENTIMENTO.get(c, "#bdc3c7") for c in contagem.index]))
        pizza.update_layout(title="Tom das notícias", height=330, margin=dict(t=50, b=20), yaxis_title="Notícias")
        m1.plotly_chart(pizza)
        if "data_iniSE" in serie.columns and "data_publicacao" in sentimentos.columns:
            linha = serie.assign(data=pd.to_datetime(serie["data_iniSE"], errors="coerce")).dropna(subset=["data"]).sort_values("data")
            sent = sentimentos.assign(data=pd.to_datetime(sentimentos["data_publicacao"], errors="coerce", utc=True).dt.tz_localize(None)).dropna(subset=["data"])
            tl = go.Figure(go.Scatter(x=linha["data"], y=linha["casos"], mode="lines", name="Casos semanais", line=dict(color="#2980b9")))
            if not sent.empty:
                topo = float(linha["casos"].max()) * 1.05
                tl.add_trace(go.Scatter(x=sent["data"], y=[topo] * len(sent), mode="markers", name="Notícias",
                                        text=sent["titulo"], hovertemplate="%{text}<extra></extra>",
                                        marker=dict(size=14, symbol="diamond", color=[ui.COR_SENTIMENTO.get(c, "#bdc3c7") for c in sent["classe"]],
                                                    line=dict(width=1, color="#333"))))
            tl.update_layout(title="Casos semanais e notícias (cor = tom)", height=330, margin=dict(t=50, b=20), yaxis_title="Casos")
            m2.plotly_chart(tl)
        st.dataframe(sentimentos[["titulo", "rotulo", "justificativa", "data_publicacao"]])
        st.caption("⚠️ Sentimento gerado por IA (Qwen3-4B local); pode conter erros. O tom da notícia é um **indicador indireto** da preocupação "
                   "veiculada pela mídia, não uma medida direta da opinião da população.")

    st.divider()
    st.markdown("**Quer investigar por conta própria?** Abra **💬 Converse com os dados** no menu e pergunte, por exemplo: "
                "*“Qual foi o ano com mais casos de dengue?”*")
