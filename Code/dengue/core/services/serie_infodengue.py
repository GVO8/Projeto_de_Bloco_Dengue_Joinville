"""Caso de uso: série semanal do InfoDengue (base + linhas enviadas pelo usuário)."""

from __future__ import annotations

import pandas as pd

from dengue.core.domain.erros import EntradaInvalidaError
from dengue.core.ports.repositorios import FonteInfoDengue, RepositorioUploads

COLUNAS_OBRIGATORIAS = {"id", "SE", "nivel"}


def mesclar_por_id(base: pd.DataFrame, novo: pd.DataFrame) -> pd.DataFrame:
    """Concatena e remove duplicatas por 'id' mantendo a linha ORIGINAL.
    O id é comparado como texto (123 e "123" são o mesmo id)."""
    base, novo = base.copy(), novo.copy()
    base["id"], novo["id"] = base["id"].astype(str), novo["id"].astype(str)
    return pd.concat([base, novo], ignore_index=True).drop_duplicates(subset="id", keep="first")


def filtrar(df: pd.DataFrame, se_inicio=None, se_fim=None, niveis=None) -> pd.DataFrame:
    if se_inicio is not None and "SE" in df.columns:
        df = df[df["SE"] >= se_inicio]
    if se_fim is not None and "SE" in df.columns:
        df = df[df["SE"] <= se_fim]
    if niveis and "nivel" in df.columns:
        df = df[df["nivel"].isin(niveis)]
    return df


def validar_linhas(df: pd.DataFrame) -> None:
    faltando = COLUNAS_OBRIGATORIAS - set(df.columns)
    if faltando:
        raise EntradaInvalidaError(
            f"O arquivo não tem as colunas obrigatórias: {', '.join(sorted(faltando))}.",
            "Use um CSV no mesmo formato da API do InfoDengue (colunas mínimas: id, SE, nivel).",
        )
    if df.empty:
        raise EntradaInvalidaError("O arquivo enviado não tem nenhuma linha.", "Envie um CSV com ao menos uma linha de dados.")
    niveis = pd.to_numeric(df["nivel"], errors="coerce")
    if niveis.isna().any() or not niveis.between(1, 4).all():
        raise EntradaInvalidaError(
            "A coluna 'nivel' deve conter apenas números de 1 a 4.",
            "Corrija os valores (1 verde, 2 amarelo, 3 laranja, 4 vermelho) e envie novamente.",
        )


class ServicoSerieInfoDengue:
    def __init__(self, fonte: FonteInfoDengue, uploads: RepositorioUploads):
        self._fonte, self._uploads = fonte, uploads
        self._base: tuple[pd.DataFrame, str] | None = None

    def _base_cacheada(self) -> tuple[pd.DataFrame, str]:
        if self._base is None:
            self._base = self._fonte.buscar()
        return self._base

    def recarregar_base(self) -> None:
        self._base = None

    def dados_completos(self) -> tuple[pd.DataFrame, str]:
        base, origem = self._base_cacheada()
        enviados = self._uploads.carregar()
        df = mesclar_por_id(base, enviados) if not enviados.empty else base.copy()
        if "SE" in df.columns:
            df = df.sort_values("SE").reset_index(drop=True)
        return df, origem

    def obter(self, se_inicio=None, se_fim=None, niveis=None) -> tuple[pd.DataFrame, str]:
        df, origem = self.dados_completos()
        return filtrar(df, se_inicio, se_fim, niveis), origem

    def adicionar(self, novo: pd.DataFrame) -> dict:
        validar_linhas(novo)
        base, _ = self._base_cacheada()
        atual, _ = self.dados_completos()
        combinado = mesclar_por_id(atual, novo)
        adicionadas = len(combinado) - len(atual)
        ids_base = set(base["id"].astype(str))
        self._uploads.salvar(combinado[~combinado["id"].isin(ids_base)])
        return {
            "adicionadas": int(adicionadas),
            "ignoradas_por_id_repetido": int(len(novo) - adicionadas),
            "total": int(len(combinado)),
        }

    def resetar(self) -> None:
        self._uploads.limpar()
