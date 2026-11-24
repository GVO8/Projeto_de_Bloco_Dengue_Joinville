"""Portas de saída: o que o núcleo precisa do mundo externo (sem saber como é feito)."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from dengue.core.domain.chat import RequisicaoInfoDengue, Turno
from dengue.core.domain.modelos import (
    ArtigoColetado, ContextoNumerico, Noticia, NoticiaCompleta, SentimentoNoticia, TrechoCorpus,
)


class RepositorioNoticias(ABC):
    @abstractmethod
    def listar(self, busca: str | None = None, limite: int | None = None) -> list[Noticia]: ...

    @abstractmethod
    def obter(self, noticia_id: int) -> Noticia | None: ...

    @abstractmethod
    def paragrafos(self, noticia_id: int) -> list[str]:
        """Parágrafos brutos (sem limpeza) do corpo da notícia."""

    @abstractmethod
    def salvar(self, artigos: list[ArtigoColetado]) -> list[Noticia]: ...


class ColetorNoticias(ABC):
    @abstractmethod
    def coletar(self, max_paginas: int) -> list[ArtigoColetado]: ...


class FonteInfoDengue(ABC):
    @abstractmethod
    def buscar(self) -> tuple[pd.DataFrame, str]:
        """Retorna (dados, origem) onde origem é 'api' ou 'amostra_local'."""


class RepositorioUploads(ABC):
    @abstractmethod
    def carregar(self) -> pd.DataFrame: ...

    @abstractmethod
    def salvar(self, df: pd.DataFrame) -> None: ...

    @abstractmethod
    def limpar(self) -> None: ...


class ArmazenamentoCorpus(ABC):
    @abstractmethod
    def existe(self) -> bool: ...

    @abstractmethod
    def salvar(self, trechos: list[TrechoCorpus], contexto: ContextoNumerico) -> None: ...

    @abstractmethod
    def obter_noticia(self, noticia_id: int) -> NoticiaCompleta | None: ...

    @abstractmethod
    def listar_titulos(self, limite: int = 5) -> list[str]: ...

    @abstractmethod
    def obter_contexto(self) -> ContextoNumerico: ...


class ConsultaInfoDengue(ABC):
    """Consulta o InfoDengue para Joinville (dengue). O município e a doença são fixos por projeto."""

    @abstractmethod
    def consultar(self, ano_inicio: int, ano_fim: int) -> tuple[pd.DataFrame, RequisicaoInfoDengue]:
        """Série semanal (semanas 1–53) de ano_inicio a ano_fim e a requisição que a originou."""


class RepositorioConversas(ABC):
    @abstractmethod
    def obter(self, sessao_id: str) -> list[Turno]: ...

    @abstractmethod
    def existe(self, sessao_id: str) -> bool: ...

    @abstractmethod
    def adicionar(self, sessao_id: str, turno: Turno) -> None: ...

    @abstractmethod
    def limpar(self, sessao_id: str) -> None: ...


class RepositorioSentimentos(ABC):
    @abstractmethod
    def listar(self) -> list[SentimentoNoticia]: ...

    @abstractmethod
    def salvar(self, sentimento: SentimentoNoticia) -> None:
        """Insere ou substitui (pela notícia)."""
