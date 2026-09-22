"""
Cliente da API do InfoDengue para Joinville/SC (TP2).

Baseado na chamada oficial:
https://info.dengue.mat.br/api/alertcity?geocode=4209102&disease=dengue&format=csv&ew_start=1&ew_end=52&ey_start=2026&ey_end=2026
"""

from pathlib import Path

import pandas as pd

API_URL = "https://info.dengue.mat.br/api/alertcity"

ROOT_DIR = Path(__file__).resolve().parents[2]
FALLBACK_CSV = ROOT_DIR / "Data" / "Raw" / "infodengue_sample.csv"

NIVEL_LABELS = {
    1: "1 — Verde",
    2: "2 — Amarelo",
    3: "3 — Laranja",
    4: "4 — Vermelho",
}


def montar_url(
    geocode: int = 4209102,
    disease: str = "dengue",
    fmt: str = "csv",
    ew_start: int = 1,
    ew_end: int = 52,
    ey_start: int = 2026,
    ey_end: int = 2026,
) -> str:
    """Monta a URL da API do InfoDengue seguindo o padrão de parâmetros oficial."""
    params = (
        "&disease=" + f"{disease}"
        + "&geocode=" + f"{geocode}"
        + "&disease=" + f"{disease}"
        + "&format=" + f"{fmt}"
        + "&ew_start=" + f"{ew_start}"
        + "&ew_end=" + f"{ew_end}"
        + "&ey_start=" + f"{ey_start}"
        + "&ey_end=" + f"{ey_end}"
    )
    return "?".join([API_URL, params])


def carregar_dados_infodengue(
    geocode: int = 4209102,
    ey_start: int = 2026,
    ey_end: int = 2026,
) -> tuple[pd.DataFrame, str]:
    """
    Busca os dados da API do InfoDengue para Joinville/SC (geocode 4209102).

    Retorna (dataframe, origem), onde origem é "api" quando os dados vieram
    da API em tempo real, ou "amostra_local" quando foi necessário usar o
    fallback local (ex.: sem conexão com a internet).
    """
    url = montar_url(geocode=geocode, ey_start=ey_start, ey_end=ey_end)
    try:
        dados = pd.read_csv(url)
        if "id" not in dados.columns:
            dados["id"] = dados.get("SE", pd.RangeIndex(len(dados))).astype(str)
        return dados, "api"
    except Exception:
        # Sem internet ou API indisponível: usa amostra local para a demo
        # não quebrar (mesmo formato de colunas esperado da API real).
        dados = pd.read_csv(FALLBACK_CSV)
        return dados, "amostra_local"
