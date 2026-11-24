"""Adaptadores de saída da série InfoDengue: API HTTP, amostra local e composição com alternativa."""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import pandas as pd
import requests

from dengue.core.domain.chat import GEOCODE_JOINVILLE, RequisicaoInfoDengue
from dengue.core.domain.erros import ConsultaSemDadosError, InfoDengueIndisponivelError
from dengue.core.ports.repositorios import ConsultaInfoDengue, FonteInfoDengue, RepositorioUploads

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


class ConsultaInfoDengueHttp(ConsultaInfoDengue):
    """Consulta multi-ano ao InfoDengue (Joinville, dengue). Sem alternativa sintética: sem API, sem resposta."""

    def __init__(self, geocode: int = GEOCODE_JOINVILLE, doenca: str = "dengue", timeout_s: float = 30, http=requests):
        self._geocode, self._doenca, self._timeout, self._http = geocode, doenca, timeout_s, http

    def consultar(self, ano_inicio: int, ano_fim: int):
        url = montar_url(geocode=self._geocode, disease=self._doenca, ew_start=1, ew_end=53, ey_start=ano_inicio, ey_end=ano_fim)
        try:
            resp = self._http.get(url, timeout=self._timeout)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
        except (requests.RequestException, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            raise InfoDengueIndisponivelError(str(exc)) from exc
        if df.empty or "SE" not in df.columns:
            raise ConsultaSemDadosError(ano_inicio, ano_fim)
        if "id" not in df.columns:
            df["id"] = df["SE"].astype(str)
        df = df[(df["SE"] // 100 >= ano_inicio) & (df["SE"] // 100 <= ano_fim)]
        if df.empty:
            raise ConsultaSemDadosError(ano_inicio, ano_fim)
        return df.reset_index(drop=True), RequisicaoInfoDengue(url, self._geocode, self._doenca, ano_inicio, ano_fim)


class ConsultaInfoDengueComCache(ConsultaInfoDengue):
    """Evita repetir a mesma consulta em curto intervalo (o InfoDengue é um serviço público e compartilhado)."""

    def __init__(self, interna: ConsultaInfoDengue, ttl_s: float = 900, relogio=time.monotonic):
        self._interna, self._ttl, self._relogio = interna, ttl_s, relogio
        self._cache: dict[tuple[int, int], tuple[float, tuple]] = {}

    def consultar(self, ano_inicio: int, ano_fim: int):
        chave, agora = (ano_inicio, ano_fim), self._relogio()
        guardado = self._cache.get(chave)
        if guardado and agora - guardado[0] < self._ttl:
            df, req = guardado[1]
            return df.copy(), req
        resultado = self._interna.consultar(ano_inicio, ano_fim)
        self._cache[chave] = (agora, resultado)
        return resultado[0].copy(), resultado[1]
