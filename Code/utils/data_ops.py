"""
Operações de dados compartilhadas entre a API (FastAPI) e o app (Streamlit).

Concentra a lógica de negócio num só lugar: mesclagem por id, filtros e
decomposição do nível de alerta. Não depende de Streamlit nem de FastAPI.
"""

from pathlib import Path

import pandas as pd

from infodengue_api import carregar_dados_infodengue

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT_DIR / "Data" / "Raw"
DATA_PROCESSED = ROOT_DIR / "Data" / "Processed"
UPLOADS_CSV = DATA_PROCESSED / "infodengue_uploads.csv"
NEWS_CSV = DATA_RAW / "nsc_noticias_joinville_dengue.csv"
NEWS_TXT = DATA_RAW / "nsc_noticias_texto.txt"


def mesclar_por_id(base_df: pd.DataFrame, novo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Concatena base + novo e remove duplicatas por 'id', mantendo a linha
    ORIGINAL (a nova é descartada em caso de conflito).
    O id é comparado como texto, para que 123 e "123" sejam o mesmo id.
    """
    if "id" not in novo_df.columns:
        raise ValueError("Os dados enviados precisam ter a coluna 'id'.")
    base = base_df.copy()
    novo = novo_df.copy()
    base["id"] = base["id"].astype(str)
    novo["id"] = novo["id"].astype(str)
    combinado = pd.concat([base, novo], ignore_index=True)
    return combinado.drop_duplicates(subset="id", keep="first")


def carregar_base() -> tuple[pd.DataFrame, str]:
    """Dados do InfoDengue (API pública, com fallback para a amostra local)."""
    return carregar_dados_infodengue()


def carregar_uploads() -> pd.DataFrame:
    """Linhas adicionadas pelo usuário (upload ou POST na API), persistidas em CSV."""
    if UPLOADS_CSV.exists():
        return pd.read_csv(UPLOADS_CSV)
    return pd.DataFrame()


def adicionar_linhas(novo_df: pd.DataFrame, base_df: pd.DataFrame) -> dict:
    """
    Mescla novas linhas ao que já existe (base + uploads anteriores) e
    persiste o resultado em Data/Processed. Retorna um resumo da operação.
    """
    uploads = carregar_uploads()
    existente = mesclar_por_id(base_df, uploads) if not uploads.empty else base_df
    antes = len(existente)
    combinado = mesclar_por_id(existente, novo_df)
    adicionadas = len(combinado) - antes
    ignoradas = len(novo_df) - adicionadas

    # persiste apenas o que NÃO está na base original
    base_ids = set(base_df["id"].astype(str))
    so_uploads = combinado[~combinado["id"].isin(base_ids)]
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    so_uploads.to_csv(UPLOADS_CSV, index=False)
    return {"adicionadas": int(adicionadas), "ignoradas_por_id_repetido": int(ignoradas), "total": int(len(combinado))}


def resetar_uploads() -> None:
    if UPLOADS_CSV.exists():
        UPLOADS_CSV.unlink()


def dados_completos(base_df: pd.DataFrame) -> pd.DataFrame:
    """Base + uploads persistidos, ordenados por SE."""
    up = carregar_uploads()
    df = mesclar_por_id(base_df, up) if not up.empty else base_df.copy()
    if "SE" in df.columns:
        df = df.sort_values("SE").reset_index(drop=True)
    return df


def filtrar(df: pd.DataFrame, se_inicio=None, se_fim=None, niveis=None) -> pd.DataFrame:
    out = df
    if se_inicio is not None and "SE" in out.columns:
        out = out[out["SE"] >= se_inicio]
    if se_fim is not None and "SE" in out.columns:
        out = out[out["SE"] <= se_fim]
    if niveis and "nivel" in out.columns:
        out = out[out["nivel"].isin(niveis)]
    return out


def carregar_noticias() -> pd.DataFrame:
    return pd.read_csv(NEWS_CSV) if NEWS_CSV.exists() else pd.DataFrame()
