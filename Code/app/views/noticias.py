import streamlit as st

import common
import data_ops

st.title("📰 Notícias — NSC Total (Joinville + Dengue)")
st.caption("Coletadas por web scraping com BeautifulSoup: `Code/scraping/scrape_nsc_dengue.py`.")

busca = st.text_input("Filtrar por trecho no título", key="busca_noticias")
df, canal = common.noticias_cache(busca or None, common.versao_dados())
common.badge_canal(canal)

if df.empty:
    st.warning("Nenhuma notícia encontrada. Rode o scraper ou ajuste o filtro.")
    st.stop()

c1, c2 = st.columns(2)
c1.metric("Notícias", len(df))
c2.metric("Autores distintos", df["autor"].nunique() if "autor" in df else 0)

st.dataframe(df[["titulo", "data_publicacao", "autor", "url"]],
             column_config={"url": st.column_config.LinkColumn("Link")})

if "data_publicacao" in df:
    meses = df["data_publicacao"].astype(str).str[:7].value_counts().sort_index()
    st.markdown("**Notícias por mês**")
    st.bar_chart(meses)

if data_ops.NEWS_TXT.exists():
    st.markdown("**Nuvem de palavras (corpo das notícias)**")
    st.image(common.wordcloud_png(data_ops.NEWS_TXT.read_text(encoding="utf-8")))
