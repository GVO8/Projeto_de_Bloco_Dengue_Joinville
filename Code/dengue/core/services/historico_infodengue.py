"""Caso de uso: série histórica do InfoDengue e fatos calculados, para o painel."""

from __future__ import annotations

from datetime import date

import pandas as pd

from dengue.core.domain.chat import ANO_MINIMO_VALIDO, RequisicaoInfoDengue
from dengue.core.domain.erros import ConsultaSemDadosError, EntradaInvalidaError
from dengue.core.ports.repositorios import ConsultaInfoDengue
from dengue.core.services.fatos_dengue import FatosDengue, calcular_fatos


class ServicoHistoricoInfoDengue:
    def __init__(self, consulta: ConsultaInfoDengue, ano_atual=lambda: date.today().year):
        self._consulta, self._ano_atual = consulta, ano_atual

    def obter(self, ano_inicio: int | None = None, ano_fim: int | None = None) -> tuple[pd.DataFrame, FatosDengue, RequisicaoInfoDengue]:
        atual = self._ano_atual()
        fim = atual if ano_fim is None else ano_fim
        inicio = fim - 3 if ano_inicio is None else ano_inicio
        if not (ANO_MINIMO_VALIDO <= inicio <= fim <= atual):
            raise EntradaInvalidaError(
                f"O período {inicio}–{fim} não é válido.",
                f"Use anos entre {ANO_MINIMO_VALIDO} e {atual}, com o ano inicial menor ou igual ao final.",
            )
        df, requisicao = self._consulta.consultar(inicio, fim)
        if df.empty:
            raise ConsultaSemDadosError(inicio, fim)
        return df, calcular_fatos(df, atual), requisicao
