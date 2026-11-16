"""Implementações em memória das portas, usadas nos testes (FakeLLM está em dengue.adapters.outbound.llm_fake)."""

from __future__ import annotations

import pandas as pd

from dengue.core.domain.modelos import ArtigoColetado, ContextoNumerico, Noticia, NoticiaCompleta, TrechoCorpus
from dengue.core.ports.repositorios import ArmazenamentoCorpus, ColetorNoticias, FonteInfoDengue, RepositorioNoticias, RepositorioUploads


class NoticiasMemoria(RepositorioNoticias):
    def __init__(self, noticias: dict[int, tuple[Noticia, list[str]]] | None = None):
        self.dados = noticias or {}

    def listar(self, busca=None, limite=None):
        itens = [n for n, _ in self.dados.values() if not busca or busca.lower() in n.titulo.lower()]
        return itens[:limite] if limite else itens

    def obter(self, noticia_id):
        return self.dados[noticia_id][0] if noticia_id in self.dados else None

    def paragrafos(self, noticia_id):
        return list(self.dados[noticia_id][1]) if noticia_id in self.dados else []

    def salvar(self, artigos):
        self.dados = {i: (Noticia(i, a.titulo, a.data_publicacao, a.autor, a.url, a.resumo), a.corpo.split("\n"))
                      for i, a in enumerate(artigos, 1)}
        return [n for n, _ in self.dados.values()]


class CorpusMemoria(ArmazenamentoCorpus):
    def __init__(self):
        self.trechos: list[TrechoCorpus] = []
        self.contexto: ContextoNumerico | None = None
        self.salvamentos = 0

    def existe(self):
        return self.contexto is not None

    def salvar(self, trechos, contexto):
        self.trechos, self.contexto, self.salvamentos = list(trechos), contexto, self.salvamentos + 1

    def obter_noticia(self, noticia_id):
        ts = sorted((t for t in self.trechos if t.id_noticia == noticia_id), key=lambda t: t.chunk_id)
        if not ts:
            return None
        return NoticiaCompleta(noticia_id, ts[0].titulo, "\n".join(t.texto for t in ts), ts[0].data_publicacao,
                               ts[0].autor, ts[0].url, ts[0].resumo)

    def listar_titulos(self, limite=5):
        return list(dict.fromkeys(t.titulo for t in self.trechos))[:limite]

    def obter_contexto(self):
        return self.contexto


class FonteFixa(FonteInfoDengue):
    def __init__(self, df: pd.DataFrame, origem: str = "api"):
        self.df, self.origem, self.chamadas = df, origem, 0

    def buscar(self):
        self.chamadas += 1
        return self.df.copy(), self.origem


class UploadsMemoria(RepositorioUploads):
    def __init__(self):
        self.df = pd.DataFrame()

    def carregar(self):
        return self.df.copy()

    def salvar(self, df):
        self.df = df.copy()

    def limpar(self):
        self.df = pd.DataFrame()


class ColetorFalso(ColetorNoticias):
    def __init__(self, artigos=None):
        self.artigos = artigos if artigos is not None else []

    def coletar(self, max_paginas):
        return self.artigos
