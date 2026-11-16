"""Componentes visuais reutilizados: tratamento de erros, selo de origem, nuvem de palavras, cache."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from io import BytesIO

import streamlit as st

from dengue.core.domain.erros import ErroDengue

log = logging.getLogger(__name__)
COR_NIVEL = {1: "#2ecc71", 2: "#f1c40f", 3: "#e67e22", 4: "#e74c3c"}
STOPWORDS_PT = {
    "de", "da", "do", "das", "dos", "em", "para", "por", "com", "que", "não", "uma", "um", "os", "as", "no", "na",
    "nos", "nas", "se", "é", "foi", "ser", "sua", "seu", "mais", "já", "ainda", "após", "sobre", "como", "ao",
    "aos", "à", "às", "entre", "pela", "pelo", "dos", "ano", "anos",
}


def exibir_erro(exc: Exception) -> None:
    """Mostra o erro de forma amigável: o que houve + o que fazer. Nunca expõe stack trace."""
    if isinstance(exc, ErroDengue):
        icone = "🤖" if exc.categoria == "ia" else "⚠️"
        st.error(f"{icone} {exc.mensagem}")
        if exc.sugestao:
            st.info(f"**O que fazer:** {exc.sugestao}")
        if exc.detalhe:
            with st.expander("Detalhe técnico"):
                st.code(str(exc.detalhe))
    else:
        log.exception("Erro inesperado na interface")
        st.error("⚠️ Algo inesperado aconteceu no aplicativo.")
        st.info("**O que fazer:** recarregue a página (F5) e tente de novo. Se persistir, reinicie o aplicativo.")


@contextmanager
def protegido():
    """Bloco que captura qualquer erro e o exibe com `exibir_erro` (não captura st.stop/rerun)."""
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - fronteira da interface
        exibir_erro(exc)


def versao_dados() -> int:
    return st.session_state.setdefault("versao_dados", 0)


def invalidar_dados() -> None:
    st.session_state["versao_dados"] = versao_dados() + 1


def selo_canal(canal: str) -> None:
    if canal == "api":
        st.caption("🟢 Dados obtidos pela **API FastAPI**.")
    else:
        st.caption("🟡 API fora do ar — dados lidos **localmente** (mesma lógica, sem a API).")


@st.cache_data
def nuvem_png(texto: str) -> bytes:
    import matplotlib.pyplot as plt
    from wordcloud import STOPWORDS, WordCloud

    wc = WordCloud(width=900, height=450, background_color="white", stopwords=set(STOPWORDS) | STOPWORDS_PT,
                   colormap="viridis").generate(texto)
    buf = BytesIO()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


@st.cache_data(ttl=60, show_spinner="Carregando dados do InfoDengue...")
def infodengue_cache(_gateway, se_inicio, se_fim, niveis: tuple, versao: int):
    """`versao` muda a cada upload/reset e invalida o cache."""
    return _gateway.obter_infodengue(se_inicio, se_fim, list(niveis) or None)


@st.cache_data(ttl=60)
def noticias_cache(_gateway, busca, versao: int):
    return _gateway.listar_noticias(busca)


@st.cache_data(ttl=300)
def texto_cache(_gateway, versao: int):
    return _gateway.texto_noticias()
