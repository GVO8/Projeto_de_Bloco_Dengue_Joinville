"""Casos de uso de notícias: listar, obter, texto para nuvem de palavras e coleta."""

from __future__ import annotations

from dengue.core.domain.erros import ColetaError, NoticiaNaoEncontradaError
from dengue.core.domain.modelos import Noticia
from dengue.core.domain.texto import limpar_paragrafos
from dengue.core.ports.repositorios import ColetorNoticias, RepositorioNoticias


class ServicoNoticias:
    def __init__(self, repo: RepositorioNoticias):
        self._repo = repo

    def listar(self, busca: str | None = None, limite: int | None = None) -> list[Noticia]:
        return self._repo.listar(busca, limite)

    def obter(self, noticia_id: int) -> Noticia:
        noticia = self._repo.obter(noticia_id)
        if noticia is None:
            raise NoticiaNaoEncontradaError(noticia_id)
        return noticia

    def texto_para_nuvem(self) -> str:
        partes = []
        for n in self._repo.listar():
            partes += limpar_paragrafos(self._repo.paragrafos(n.id), n.titulo)
        return "\n".join(partes)


class ColetarNoticias:
    """Coleta no site, salva e (via callback) reconstrói o corpus da IA."""

    def __init__(self, coletor: ColetorNoticias, repo: RepositorioNoticias, aposcoleta=None):
        self._coletor, self._repo, self._aposcoleta = coletor, repo, aposcoleta

    def executar(self, max_paginas: int = 3) -> int:
        artigos = self._coletor.coletar(max_paginas)
        if not artigos:
            raise ColetaError("Nenhuma notícia com 'Joinville' e 'dengue' foi encontrada.")
        salvas = self._repo.salvar(artigos)
        if self._aposcoleta:
            self._aposcoleta()
        return len(salvas)
