"""Caso de uso: preparar o corpus (trechos limpos) e o contexto numérico para a IA."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from dengue.core.domain.modelos import ContextoNumerico, TrechoCorpus
from dengue.core.domain.texto import dividir_em_trechos, limpar_paragrafos
from dengue.core.ports.repositorios import ArmazenamentoCorpus, RepositorioNoticias
from dengue.core.services.serie_infodengue import ServicoSerieInfoDengue

MUNICIPIO = "Joinville/SC (geocode 4209102)"


def calcular_contexto(df: pd.DataFrame, origem: str) -> ContextoNumerico:
    por_nivel = {str(k): int(v) for k, v in df["nivel"].value_counts().sort_index().items()} if "nivel" in df else {}
    casos_total, pico = None, None
    if "casos" in df.columns and not df.empty:
        casos_total = int(df["casos"].sum())
        linha = df.loc[df["casos"].idxmax()]
        pico = {"SE": int(linha["SE"]), "casos": int(linha["casos"])}
    return ContextoNumerico(MUNICIPIO, origem, int(len(df)), por_nivel, casos_total, pico)


@dataclass(frozen=True)
class ResumoCorpus:
    noticias: int
    trechos: int


class PrepararCorpus:
    def __init__(self, noticias: RepositorioNoticias, serie: ServicoSerieInfoDengue, armazenamento: ArmazenamentoCorpus):
        self._noticias, self._serie, self._armazenamento = noticias, serie, armazenamento

    def executar(self) -> ResumoCorpus:
        trechos: list[TrechoCorpus] = []
        lista = self._noticias.listar()
        for n in lista:
            paragrafos = limpar_paragrafos(self._noticias.paragrafos(n.id), n.titulo)
            for i, texto in enumerate(dividir_em_trechos(paragrafos)):
                trechos.append(TrechoCorpus(n.id, i, n.titulo, texto, n.data_publicacao, n.autor, n.url, n.resumo))
        df, origem = self._serie.dados_completos()
        self._armazenamento.salvar(trechos, calcular_contexto(df, origem))
        return ResumoCorpus(noticias=len(lista), trechos=len(trechos))
