"""Utilidades compartilhadas pelas páginas do app (paths, cache, componentes)."""

import sys
from io import BytesIO
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
for sub in ("utils", "llm_prep"):
    p = str(ROOT_DIR / "Code" / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

import data_service  # noqa: E402
from infodengue_api import NIVEL_LABELS  # noqa: E402

COR_NIVEL = {1: "#2ecc71", 2: "#f1c40f", 3: "#e67e22", 4: "#e74c3c"}
STOPWORDS_PT = {
    "de", "da", "do", "das", "dos", "em", "para", "por", "com", "que", "não", "uma", "um",
    "os", "as", "no", "na", "nos", "nas", "se", "é", "foi", "ser", "sua", "seu", "mais",
    "já", "ainda", "após", "sobre", "como", "ao", "aos", "à", "às", "entre", "pela", "pelo",
}


@st.cache_data(ttl=300, show_spinner="Carregando dados do InfoDengue...")
def infodengue_cache(se_inicio, se_fim, niveis: tuple, versao: int):
    """`versao` muda a cada upload/reset e invalida o cache."""
    return data_service.obter_infodengue(se_inicio, se_fim, list(niveis) or None)


@st.cache_data(ttl=300)
def noticias_cache(busca, versao: int = 0):
    return data_service.obter_noticias(busca)


@st.cache_data
def wordcloud_png(texto: str) -> bytes:
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud, STOPWORDS

    wc = WordCloud(width=900, height=450, background_color="white",
                   stopwords=set(STOPWORDS) | STOPWORDS_PT, colormap="viridis").generate(texto)
    buf = BytesIO()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def versao_dados() -> int:
    return st.session_state.setdefault("versao_dados", 0)


def invalidar_dados():
    st.session_state["versao_dados"] = versao_dados() + 1


def badge_canal(canal: str):
    if canal == "api":
        st.caption("🟢 Dados obtidos pela **API FastAPI** (rota GET).")
    else:
        st.caption("🟡 API fora do ar — dados lidos **localmente** (mesma lógica, sem a API).")
