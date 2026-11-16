"""Portas de saída: o que o núcleo precisa do mundo externo (sem saber como é feito)."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from dengue.core.domain.modelos import (
    ArtigoColetado, ContextoNumerico, Noticia, NoticiaCompleta, TrechoCorpus,
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
