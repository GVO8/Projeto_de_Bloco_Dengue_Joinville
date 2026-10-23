"""
Camada de acesso a dados usada pelo app Streamlit.

Tenta a API FastAPI; se ela não estiver rodando, usa a mesma lógica
localmente (data_ops). O app, portanto, funciona com ou sem a API no ar,
e informa de qual caminho vieram os dados.
"""

import os

import pandas as pd
import requests

import data_ops

API_URL = os.getenv("DENGUE_API_URL", "http://127.0.0.1:8000")
TIMEOUT = 3


def api_disponivel() -> bool:
    try:
        return requests.get(f"{API_URL}/health", timeout=TIMEOUT).ok
    except requests.RequestException:
        return False


def obter_infodengue(se_inicio=None, se_fim=None, niveis=None) -> tuple[pd.DataFrame, str]:
    """Retorna (df, canal): 'api' se veio da API FastAPI, 'local' caso contrário."""
    try:
        params = {"se_inicio": se_inicio, "se_fim": se_fim, "nivel": niveis}
        r = requests.get(f"{API_URL}/infodengue", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return pd.DataFrame(r.json()["dados"]), "api"
    except requests.RequestException:
        base, _ = data_ops.carregar_base()
        return data_ops.filtrar(data_ops.dados_completos(base), se_inicio, se_fim, niveis), "local"


def enviar_infodengue(novo_df: pd.DataFrame) -> tuple[dict, str]:
    """Envia linhas novas (POST na API ou mesclagem local). Retorna (resumo, canal)."""
    try:
        registros = novo_df.astype(object).where(pd.notna(novo_df), None).to_dict(orient="records")
        r = requests.post(f"{API_URL}/infodengue", json=registros, timeout=TIMEOUT * 3)
        if r.status_code == 422:
            raise ValueError(f"A API rejeitou os dados: {r.json().get('detail')}")
        r.raise_for_status()
        return r.json(), "api"
    except requests.ConnectionError:
        base, _ = data_ops.carregar_base()
        return data_ops.adicionar_linhas(novo_df, base), "local"


def obter_noticias(busca=None, limit=200) -> tuple[pd.DataFrame, str]:
    try:
        r = requests.get(f"{API_URL}/noticias", params={"busca": busca, "limit": limit}, timeout=TIMEOUT)
        r.raise_for_status()
        return pd.DataFrame(r.json()["noticias"]), "api"
    except requests.RequestException:
        df = data_ops.carregar_noticias()
        if busca and not df.empty:
            df = df[df["titulo"].str.contains(busca, case=False, na=False)]
        return df.head(limit), "local"
