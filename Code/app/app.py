"""
Dengue em Múltiplas Dimensões — App Streamlit (TP2)

Executar:
    streamlit run Code/app/app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Setup de paths e imports internos
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "Code" / "utils"))
from infodengue_api import carregar_dados_infodengue, NIVEL_LABELS  # noqa: E402

DATA_RAW = ROOT_DIR / "Data" / "Raw"
SINAN_SAMPLE_PATH = DATA_RAW / "sinan_sample.csv"
NEWS_CSV_PATH = DATA_RAW / "nsc_noticias_joinville_dengue.csv"
NEWS_TXT_PATH = DATA_RAW / "nsc_noticias_texto.txt"

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dengue em Múltiplas Dimensões — Joinville/SC",
    page_icon="🦟",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Funções cacheadas (performance)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Buscando dados do InfoDengue...")
def carregar_infodengue_cache(ey_start: int, ey_end: int):
    return carregar_dados_infodengue(ey_start=ey_start, ey_end=ey_end)


@st.cache_data
def carregar_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data
def carregar_texto(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@st.cache_data
def gerar_wordcloud_png(texto: str) -> bytes:
    """Gera uma nuvem de palavras a partir do texto e retorna PNG em bytes."""
    from io import BytesIO

    import matplotlib.pyplot as plt
    from wordcloud import WordCloud, STOPWORDS

    stopwords_pt = set(STOPWORDS) | {
        "de", "da", "do", "das", "dos", "em", "para", "por", "com", "que",
        "não", "uma", "um", "os", "as", "no", "na", "nos", "nas", "se", "é",
        "foi", "ser", "sua", "seu", "mais", "já", "ainda", "após", "sobre",
        "como", "ao", "aos", "à", "às", "entre", "pela", "pelo",
    }
    wc = WordCloud(
        width=900,
        height=450,
        background_color="white",
        stopwords=stopwords_pt,
        colormap="viridis",
    ).generate(texto)

    buf = BytesIO()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Estado de sessão: inicialização
# ---------------------------------------------------------------------------
if "infodengue_df" not in st.session_state:
    df_inicial, origem_inicial = carregar_infodengue_cache(2026, 2026)
    st.session_state["infodengue_df"] = df_inicial
    st.session_state["infodengue_origem"] = origem_inicial

if "upload_realizado" not in st.session_state:
    st.session_state["upload_realizado"] = False


def mesclar_upload(base_df: pd.DataFrame, upload_df: pd.DataFrame) -> pd.DataFrame:
    """
    Concatena o dataframe base (InfoDengue) com um CSV enviado pelo usuário,
    no mesmo formato (deve conter a coluna 'id').

    Regra pedida: em caso de 'id' repetido entre os dois, mantém a linha
    ORIGINAL (base) e descarta a nova (upload) — ou seja, o id novo é
    substituído pelo antigo.
    """
    if "id" not in upload_df.columns:
        raise ValueError("O CSV enviado precisa ter uma coluna 'id' para o merge.")

    combinado = pd.concat([base_df, upload_df], ignore_index=True)
    combinado = combinado.drop_duplicates(subset="id", keep="first")
    return combinado


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.title("🦟 Dengue em Múltiplas Dimensões — Joinville/SC")
st.caption(
    "TP2 · Projeto de IA Generativa e ESG · alinhado ao ODS 3 (Saúde e Bem-Estar)"
)

tab_sobre, tab_painel, tab_noticias, tab_dados = st.tabs(
    ["📌 Sobre o projeto", "📈 Painel InfoDengue", "📰 Notícias (Web Scraping)", "📂 Dados e Upload"]
)

# ---------------------------------------------------------------------------
# Aba: Sobre o projeto
# ---------------------------------------------------------------------------
with tab_sobre:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            **Problema de negócio:** indicadores públicos de clima, sensoriamento
            remoto (satélite) e densidade populacional para Joinville/SC existem,
            mas estão dispersos em plataformas técnicas distintas — sem uma
            camada única e acessível que os reúna lado a lado com o contexto
            epidemiológico oficial.

            **Objetivo do projeto:** reunir, num único painel, dimensões
            públicas e gratuitas de risco de dengue — epidemiológica
            (SINAN/InfoDengue), climática, ambiental via satélite e
            populacional — complementadas por conteúdo textual obtido via
            *web scraping* de notícias públicas, tornando visíveis fatores de
            risco que vão além da simples contagem de casos notificados.

            **ODS atendidos:** ODS 3 (Saúde e Bem-Estar), ODS 11 (Cidades e
            Comunidades Sustentáveis), ODS 17 (Parcerias e dados abertos).
            """
        )
    with col2:
        st.info(
            "**Público-alvo (fictício)**\n\n"
            "Perfis hipotéticos de gestor de saúde pública e de morador local, "
            "usados apenas para orientar o design do painel — sem contato ou "
            "validação com órgãos públicos reais."
        )

    st.subheader("Links úteis e fontes de inspiração")
    st.markdown(
        """
        - [SINAN / OpenDataSUS](https://opendatasus.saude.gov.br/)
        - [InfoDengue — API pública](https://info.dengue.mat.br/)
        - [NSC Total — notícias sobre Dengue](https://www.nsctotal.com.br/tag/dengue)
        - [Copernicus Climate Change Service](https://climate.copernicus.eu/)
        - [Google Earth Engine](https://earthengine.google.com/)
        - [IBGE — Dados e Estatísticas](https://www.ibge.gov.br/)
        """
    )

# ---------------------------------------------------------------------------
# Aba: Painel InfoDengue (gráfico de linha temporal por nível + upload/download)
# ---------------------------------------------------------------------------
with tab_painel:
    st.subheader("Nível de alerta de dengue por semana epidemiológica — Joinville/SC, 2026")

    origem = st.session_state["infodengue_origem"]
    if origem == "api":
        st.success("Dados carregados em tempo real da API do InfoDengue.")
    else:
        st.warning(
            "Não foi possível acessar a API do InfoDengue neste momento — "
            "exibindo uma amostra local no mesmo formato, apenas para "
            "manter a demo funcional offline."
        )

    df_ativo = st.session_state["infodengue_df"].copy()

    if st.session_state["upload_realizado"]:
        st.caption("📌 Gráfico atualizado com dados enviados por upload (ver aba 'Dados e Upload').")

    # --- Filtro dinâmico de intervalo de semanas ---
    if "SE" in df_ativo.columns:
        df_ativo = df_ativo.sort_values("SE")
        se_min, se_max = int(df_ativo["SE"].min()), int(df_ativo["SE"].max())
        se_range = st.slider(
            "Intervalo de semanas epidemiológicas (SE)",
            min_value=se_min,
            max_value=se_max,
            value=(se_min, se_max),
        )
        df_filtrado = df_ativo[(df_ativo["SE"] >= se_range[0]) & (df_ativo["SE"] <= se_range[1])]
    else:
        df_filtrado = df_ativo

    # --- Gráfico de linha: uma linha por nível de alerta ---
    if "nivel" in df_filtrado.columns and "SE" in df_filtrado.columns:
        fig = go.Figure()
        cores = {1: "#2ecc71", 2: "#f1c40f", 3: "#e67e22", 4: "#e74c3c"}

        for nivel_valor, label in NIVEL_LABELS.items():
            serie = (df_filtrado["nivel"] == nivel_valor).astype(int)
            fig.add_trace(
                go.Scatter(
                    x=df_filtrado["SE"],
                    y=serie,
                    mode="lines",
                    name=label,
                    line=dict(shape="hv", width=3, color=cores.get(nivel_valor)),
                )
            )

        fig.update_layout(
            xaxis_title="Semana Epidemiológica (SE)",
            yaxis=dict(
                title="Nível ativo",
                tickvals=[0, 1],
                ticktext=["Não", "Sim"],
                range=[-0.2, 1.2],
            ),
            legend_title="Nível de alerta",
            height=420,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Colunas 'SE' e/ou 'nivel' não encontradas nos dados carregados.")

    # --- Estatísticas básicas ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Semanas no período filtrado", len(df_filtrado))
    if "casos" in df_filtrado.columns:
        c2.metric("Casos (soma no período)", int(df_filtrado["casos"].sum()))
    if "nivel" in df_filtrado.columns:
        c3.metric("Semanas em nível 3 ou 4", int((df_filtrado["nivel"] >= 3).sum()))

    with st.expander("Ver tabela de dados usada no gráfico"):
        st.dataframe(df_filtrado, use_container_width=True)

    # --- Download do CSV resultante (antes ou depois de upload) ---
    csv_download = df_ativo.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Baixar CSV com os dados atuais do gráfico",
        data=csv_download,
        file_name="infodengue_joinville_2026_atualizado.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# Aba: Notícias (Web Scraping)
# ---------------------------------------------------------------------------
with tab_noticias:
    st.subheader("Notícias — NSC Total (filtro: Joinville + Dengue)")
    st.caption(
        "Dados obtidos via *web scraping* com BeautifulSoup (script separado: "
        "`Code/scraping/scrape_nsc_dengue.py`), salvos em `Data/Raw/`."
    )

    try:
        df_noticias = carregar_csv(NEWS_CSV_PATH)
        texto_completo = carregar_texto(NEWS_TXT_PATH)

        c1, c2 = st.columns(2)
        c1.metric("Notícias coletadas", len(df_noticias))
        if "autor" in df_noticias.columns:
            c2.metric("Autores distintos", df_noticias["autor"].nunique())

        st.markdown("**Tabela de notícias**")
        st.dataframe(
            df_noticias[["titulo", "data_publicacao", "autor", "url"]],
            use_container_width=True,
            column_config={"url": st.column_config.LinkColumn("Link")},
        )

        st.markdown("**Nuvem de palavras (corpo das notícias)**")
        png_bytes = gerar_wordcloud_png(texto_completo)
        st.image(png_bytes, use_container_width=True)

    except FileNotFoundError:
        st.error(
            "Arquivos de notícias não encontrados em Data/Raw/. Rode primeiro "
            "`python Code/scraping/scrape_nsc_dengue.py`."
        )

# ---------------------------------------------------------------------------
# Aba: Dados e Upload
# ---------------------------------------------------------------------------
with tab_dados:
    st.subheader("Amostra de dados — dimensão epidemiológica (SINAN)")
    try:
        df_sinan = carregar_csv(SINAN_SAMPLE_PATH)
        st.dataframe(df_sinan, use_container_width=True)
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {SINAN_SAMPLE_PATH}")

    st.divider()
    st.subheader("📤 Upload de dados complementares (InfoDengue)")
    st.markdown(
        """
        Envie um CSV **no mesmo formato retornado pela API do InfoDengue**
        (deve conter, no mínimo, as colunas `id`, `SE` e `nivel`). Os dados
        serão combinados com os já carregados e usados para atualizar o
        gráfico de linha temporal na aba **Painel InfoDengue**.

        Regra de mesclagem: se um `id` do arquivo enviado já existir na base
        atual, a linha **original** é mantida (o registro novo é descartado).
        """
    )

    arquivo = st.file_uploader("Selecione um arquivo CSV", type=["csv"])

    if arquivo is not None:
        try:
            df_upload = pd.read_csv(arquivo)
            st.write("Prévia do arquivo enviado:")
            st.dataframe(df_upload.head(), use_container_width=True)

            if st.button("Mesclar com os dados atuais"):
                combinado = mesclar_upload(st.session_state["infodengue_df"], df_upload)
                st.session_state["infodengue_df"] = combinado
                st.session_state["upload_realizado"] = True
                st.success(
                    f"Upload mesclado com sucesso! Total de linhas após mesclagem: {len(combinado)}. "
                    "Veja o gráfico atualizado na aba 'Painel InfoDengue'."
                )
        except Exception as exc:
            st.error(f"Erro ao processar o CSV enviado: {exc}")

    if st.session_state["upload_realizado"]:
        if st.button("↩️ Descartar upload e voltar aos dados originais"):
            df_original, origem_original = carregar_infodengue_cache(2026, 2026)
            st.session_state["infodengue_df"] = df_original
            st.session_state["infodengue_origem"] = origem_original
            st.session_state["upload_realizado"] = False
            st.rerun()

st.caption(
    "Fontes: SINAN/DATASUS, API pública do InfoDengue, NSC Total (web scraping). "
    "Ver `Docs/DataReport/data_summary_report.md` para detalhes completos."
)
