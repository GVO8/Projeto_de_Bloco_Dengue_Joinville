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


# ------------------------------------------------------------------ conversa com os dados
def serie_conhecida() -> "pd.DataFrame":
    """2022–2026 (2026 até a SE 40), com respostas conhecidas:
    mais casos = 2024 (5.600), menos = 2023 (104); pico de 2026 = SE 202620 (90 casos);
    2026 x 2025 nas SE 1–40: 1.260 x 840 → +50,0%."""
    linhas = []
    for ano, semanas, base, pico_semana, pico in ((2022, 52, 10, 5, 10), (2023, 52, 2, 3, 2), (2024, 52, 100, 14, 500),
                                                  (2025, 52, 20, 10, 60), (2026, 40, 30, 20, 90)):
        for w in range(1, semanas + 1):
            linhas.append({"SE": ano * 100 + w, "data_iniSE": (pd.Timestamp(f"{ano}-01-01") + pd.Timedelta(weeks=w - 1)).strftime("%Y-%m-%d"),
                           "casos": pico if w == pico_semana else base, "nivel": 1 + w % 4})
    return pd.DataFrame(linhas)


class ConsultaFalsa:
    """Implementa ConsultaInfoDengue sem rede. Recorta a série conhecida ao período pedido."""

    def __init__(self, df=None, erro: Exception | None = None):
        from dengue.adapters.outbound.infodengue import montar_url
        from dengue.core.domain.chat import GEOCODE_JOINVILLE, RequisicaoInfoDengue

        self.df, self.erro, self.chamadas = (df if df is not None else serie_conhecida()), erro, []
        self._montar_url, self._Req, self._geo = montar_url, RequisicaoInfoDengue, GEOCODE_JOINVILLE

    def consultar(self, ano_inicio, ano_fim):
        self.chamadas.append((ano_inicio, ano_fim))
        if self.erro:
            raise self.erro
        d = self.df[(self.df["SE"] // 100 >= ano_inicio) & (self.df["SE"] // 100 <= ano_fim)].reset_index(drop=True)
        url = self._montar_url(geocode=self._geo, ew_start=1, ew_end=53, ey_start=ano_inicio, ey_end=ano_fim)
        return d, self._Req(url, self._geo, "dengue", ano_inicio, ano_fim)


def modelo_chat(plano: str | dict | None = None, resposta: str = "Resposta redigida pela IA."):
    """ModeloFake que devolve `plano` (JSON) ao planejador e `resposta` ao redator. plano=None → JSON padrão válido."""
    import json

    from dengue.adapters.outbound.llm_fake import ModeloFake

    padrao = {"assunto_valido": True, "cidade": "nao_citada", "intencao": "total", "ano_inicio": None, "ano_fim": None}
    saida_plano = plano if isinstance(plano, str) else json.dumps(plano or padrao)

    def responder(prompt: str) -> str:
        return saida_plano if "Converta a pergunta do usuário" in prompt else resposta

    return ModeloFake(responder)
