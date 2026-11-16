import streamlit as st

from dengue.adapters.inbound.ui_streamlit import componentes as ui
from dengue.adapters.inbound.ui_streamlit.deps import obter_gateway
from dengue.core.domain.modelos import Operacao

st.title("📰 Notícias — NSC Total (Joinville + Dengue)")
st.caption("Coletadas por web scraping. Use os botões de cada notícia para pedir uma análise à IA local.")

BOTOES = {Operacao.RESUMO: "📝 Resumir", Operacao.SENTIMENTO: "😐 Sentimento",
          Operacao.QA: "❓ Perguntar", Operacao.RELATORIO: "📋 Relatório"}

gw = obter_gateway()
resultados = st.session_state.setdefault("resultados_ia", {})   # id da notícia -> última resposta

with ui.protegido():
    busca = st.text_input("Filtrar por trecho no título")
    df, canal = ui.noticias_cache(gw, busca or None, ui.versao_dados())
    ui.selo_canal(canal)

    if df.empty:
        st.warning("Nenhuma notícia encontrada.")
        st.info("**O que fazer:** ajuste o filtro ou colete notícias com `python Code/cli.py coletar-noticias`.")
        st.stop()

    c1, c2 = st.columns(2)
    c1.metric("Notícias", len(df))
    c2.metric("Autores distintos", int(df["autor"].nunique()) if "autor" in df else 0)

    for n in df.to_dict("records"):
        nid = int(n["id"])
        with st.expander(f"{n['titulo']}", expanded=nid in resultados):
            data = str(n.get("data_publicacao") or "")[:10] or "data não informada"
            st.caption(f"{n.get('autor') or 'autor não informado'} · {data}")
            if n.get("url"):
                st.markdown(f"[Ler a notícia original]({n['url']})")

            pergunta = st.text_input("Pergunta sobre a notícia (para o botão ❓ Perguntar)", key=f"pergunta_{nid}")
            colunas = st.columns(len(BOTOES))
            for coluna, (op, rotulo) in zip(colunas, BOTOES.items()):
                if coluna.button(rotulo, key=f"btn_{op.value}_{nid}"):
                    with ui.protegido():
                        resultados.pop(nid, None)
                        with st.spinner("A IA está lendo a notícia... em computadores sem placa de vídeo isso pode levar alguns minutos."):
                            resultados[nid] = gw.processar_noticia(nid, op.value, pergunta)

            if nid in resultados:
                st.divider()
                st.markdown(resultados[nid]["markdown"])
                st.caption(f"Modelo: {resultados[nid]['modelo']} · {resultados[nid]['tempo_segundos']} s")

    st.divider()
    texto, _ = ui.texto_cache(gw, ui.versao_dados())
    if texto.strip():
        st.markdown("**Nuvem de palavras (texto limpo das notícias)**")
        st.image(ui.nuvem_png(texto))
