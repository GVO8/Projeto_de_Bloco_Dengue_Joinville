"""Adaptadores de saída da série InfoDengue: API HTTP, amostra local e composição com alternativa."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pandas as pd
import requests

from dengue.core.ports.repositorios import FonteInfoDengue, RepositorioUploads

log = logging.getLogger(__name__)
API_URL = "https://info.dengue.mat.br/api/alertcity"


def montar_url(geocode=4209102, disease="dengue", fmt="csv", ew_start=1, ew_end=52, ey_start=2026, ey_end=2026) -> str:
    params = (
        f"&disease={disease}&geocode={geocode}&disease={disease}&format={fmt}"
        f"&ew_start={ew_start}&ew_end={ew_end}&ey_start={ey_start}&ey_end={ey_end}"
    )
    return "?".join([API_URL, params])


class InfoDengueHttp(FonteInfoDengue):
    def __init__(self, url: str | None = None, timeout_s: float = 20):
        self._url, self._timeout = url or montar_url(), timeout_s

    def buscar(self) -> tuple[pd.DataFrame, str]:
        resp = requests.get(self._url, timeout=self._timeout)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        if "id" not in df.columns:
            df["id"] = df["SE"].astype(str) if "SE" in df.columns else df.index.astype(str)
        return df, "api"


class InfoDengueAmostraCsv(FonteInfoDengue):
    def __init__(self, caminho: Path):
        self._caminho = caminho

    def buscar(self) -> tuple[pd.DataFrame, str]:
        return pd.read_csv(self._caminho), "amostra_local"


class InfoDengueComAlternativa(FonteInfoDengue):
    """Tenta a fonte principal; se falhar, usa a alternativa (e registra o motivo)."""

    def __init__(self, principal: FonteInfoDengue, alternativa: FonteInfoDengue):
        self._principal, self._alternativa = principal, alternativa

    def buscar(self) -> tuple[pd.DataFrame, str]:
        try:
            return self._principal.buscar()
        except Exception as exc:
            log.warning("InfoDengue indisponível (%s); usando amostra local.", exc)
            return self._alternativa.buscar()


class UploadsCsv(RepositorioUploads):
    def __init__(self, caminho: Path):
        self._caminho = caminho

    def carregar(self) -> pd.DataFrame:
        return pd.read_csv(self._caminho) if self._caminho.exists() else pd.DataFrame()

    def salvar(self, df: pd.DataFrame) -> None:
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self._caminho, index=False)

    def limpar(self) -> None:
        if self._caminho.exists():
            self._caminho.unlink()
