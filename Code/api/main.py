"""
API FastAPI — Dengue em Múltiplas Dimensões (TP3)

Executar (a partir da raiz do projeto):
    python -m uvicorn main:app --app-dir Code/api --reload --port 8000

Documentação interativa (Swagger): http://127.0.0.1:8000/docs
"""

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "utils"))
import data_ops  # noqa: E402

app = FastAPI(
    title="API Dengue em Múltiplas Dimensões — Joinville/SC",
    description=(
        "Consulta e envio de dados do painel: série semanal do InfoDengue "
        "(com nível de alerta) e notícias coletadas por web scraping."
    ),
    version="0.3.0",
)


@lru_cache(maxsize=1)
def _base() -> tuple[pd.DataFrame, str]:
    """Base do InfoDengue (API pública ou amostra local). Cacheada em memória."""
    return data_ops.carregar_base()


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """DataFrame -> lista de dicts JSON-safe (NaN vira null)."""
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


class RegistroInfoDengue(BaseModel):
    """Uma linha semanal no formato do InfoDengue. Campos extras são aceitos."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Identificador único da linha (usado na mesclagem).")
    SE: int = Field(..., description="Semana epidemiológica no formato AAAASS, ex.: 202614.")
    nivel: int = Field(..., ge=1, le=4, description="Nível de alerta: 1 verde, 2 amarelo, 3 laranja, 4 vermelho.")
    casos: Optional[int] = Field(None, description="Casos notificados na semana (opcional).")

    @field_validator("id", mode="before")
    @classmethod
    def _id_como_texto(cls, v):
        # o InfoDengue devolve ids numéricos; aceitamos número ou texto
        return str(v)


@app.get("/health", tags=["Sistema"], summary="Verifica se a API está no ar")
def health():
    _, origem = _base()
    return {"status": "ok", "origem_dados_infodengue": origem}


@app.get("/infodengue", tags=["InfoDengue"], summary="Consulta a série semanal (base + dados enviados)")
def get_infodengue(
    se_inicio: Optional[int] = Query(None, description="SE inicial (AAAASS), inclusiva."),
    se_fim: Optional[int] = Query(None, description="SE final (AAAASS), inclusiva."),
    nivel: Optional[list[int]] = Query(None, description="Um ou mais níveis (1–4). Ex.: ?nivel=3&nivel=4"),
):
    base, origem = _base()
    df = data_ops.filtrar(data_ops.dados_completos(base), se_inicio, se_fim, nivel)
    return {"origem": origem, "total": len(df), "dados": _records(df)}


@app.post("/infodengue", tags=["InfoDengue"], summary="Envia novas linhas semanais")
def post_infodengue(registros: list[RegistroInfoDengue]):
    """
    Adiciona linhas ao conjunto de dados. Se um `id` já existir, a linha
    ORIGINAL é mantida e a enviada é ignorada (mesma regra do upload no app).
    """
    if not registros:
        raise HTTPException(status_code=422, detail="Envie ao menos um registro.")
    base, _ = _base()
    novo = pd.DataFrame([r.model_dump() for r in registros])
    return data_ops.adicionar_linhas(novo, base)


@app.get("/noticias", tags=["Notícias"], summary="Lista as notícias coletadas (Joinville + Dengue)")
def get_noticias(
    busca: Optional[str] = Query(None, description="Filtra por trecho no título."),
    limit: int = Query(20, ge=1, le=200, description="Máximo de notícias retornadas."),
):
    df = data_ops.carregar_noticias()
    if df.empty:
        return {"total": 0, "noticias": []}
    if busca:
        df = df[df["titulo"].str.contains(busca, case=False, na=False)]
    return {"total": len(df), "noticias": _records(df.head(limit))}
