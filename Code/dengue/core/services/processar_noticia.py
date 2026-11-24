"""Caso de uso central da etapa de IA: processar uma notícia com o modelo de linguagem."""

from __future__ import annotations

import time
from datetime import datetime

from dengue.core.domain.erros import (
    CorpusIndisponivelError, NoticiaNaoEncontradaError, OperacaoInvalidaError, PerguntaObrigatoriaError,
)
from dengue.core.domain.modelos import NoticiaCompleta, Operacao, RespostaProcessamento, SentimentoNoticia
from dengue.core.domain.texto import extrair_classe_sentimento, extrair_resumo_final, limitar_texto
from dengue.core.ports.modelo_linguagem import ModeloLinguagem
from dengue.core.ports.repositorios import ArmazenamentoCorpus, RepositorioNoticias, RepositorioSentimentos
from dengue.core.prompts import montar_prompt
from dengue.core.services.corpus import PrepararCorpus

MAX_PERGUNTA = 500


class ProcessarNoticia:
    def __init__(
        self,
        corpus: ArmazenamentoCorpus,
        preparar_corpus: PrepararCorpus,
        noticias: RepositorioNoticias,
        modelo: ModeloLinguagem,
        max_chars_entrada: int = 8000,
        sentimentos: RepositorioSentimentos | None = None,
        agora=datetime.now,
    ):
        self._corpus, self._preparar, self._noticias = corpus, preparar_corpus, noticias
        self._modelo, self._max_chars = modelo, max_chars_entrada
        self._sentimentos, self._agora = sentimentos, agora

    # ------------------------------------------------------------------
    def executar(self, noticia_id: int, operacao: str | Operacao, pergunta: str | None = None) -> RespostaProcessamento:
        op = self._validar_operacao(operacao)
        pergunta = (pergunta or "").strip()
        if op.exige_pergunta and not pergunta:
            raise PerguntaObrigatoriaError(MAX_PERGUNTA)
        if len(pergunta) > MAX_PERGUNTA:
            pergunta = pergunta[:MAX_PERGUNTA]

        noticia = self._obter_noticia_do_corpus(noticia_id)
        contexto = self._corpus.obter_contexto()
        texto, truncado = limitar_texto(noticia.texto, self._max_chars)

        prompt = self._montar(op, noticia, texto, contexto.como_texto(), pergunta)
        inicio = time.perf_counter()
        resultado = self._modelo.gerar(prompt, max_tokens=op.max_tokens).strip()
        tempo = time.perf_counter() - inicio

        avisos = []
        if truncado:
            avisos.append("A notícia era longa e só o início foi enviado à IA.")
        if contexto.dados_sinteticos and op in (Operacao.QA, Operacao.RELATORIO):
            avisos.append("Os números do InfoDengue usados aqui são dados de exemplo (sintéticos), não oficiais.")

        if op == Operacao.SENTIMENTO and self._sentimentos is not None:
            self._sentimentos.salvar(SentimentoNoticia(
                noticia_id=noticia.id, titulo=noticia.titulo, classe=extrair_classe_sentimento(resultado), justificativa=resultado,
                modelo=self._modelo.nome, tempo_segundos=round(tempo, 2), analisado_em=self._agora().isoformat(timespec="seconds"),
                data_publicacao=noticia.data_publicacao,
            ))
        return RespostaProcessamento(
            noticia_id=noticia.id, titulo=noticia.titulo, operacao=op, resultado=resultado,
            resumo_final=extrair_resumo_final(op, resultado), modelo=self._modelo.nome,
            tempo_segundos=round(tempo, 2), avisos=tuple(avisos), metricas=self._modelo.ultimas_metricas(),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _validar_operacao(operacao: str | Operacao) -> Operacao:
        try:
            return Operacao(operacao)
        except ValueError:
            raise OperacaoInvalidaError(str(operacao), [o.value for o in Operacao]) from None

    def _obter_noticia_do_corpus(self, noticia_id: int) -> NoticiaCompleta:
        """Busca no corpus; se o corpus não existe ou está desatualizado, reconstrói uma vez."""
        if self._corpus.existe():
            achada = self._corpus.obter_noticia(noticia_id)
            if achada:
                return achada
        if self._noticias.obter(noticia_id) is None:
            raise NoticiaNaoEncontradaError(noticia_id)
        try:
            self._preparar.executar()
        except Exception as exc:  # falha de leitura/escrita dos arquivos
            raise CorpusIndisponivelError(detalhe=str(exc)) from exc
        achada = self._corpus.obter_noticia(noticia_id)
        if achada is None:
            raise CorpusIndisponivelError(detalhe=f"notícia {noticia_id} sem texto aproveitável após a limpeza")
        return achada

    def _montar(self, op: Operacao, n: NoticiaCompleta, texto: str, contexto_txt: str, pergunta: str) -> str:
        if op == Operacao.RESUMO:
            return montar_prompt("resumo", titulo=n.titulo, texto=texto)
        if op == Operacao.SENTIMENTO:
            resumo = n.resumo or texto[:400]
            return montar_prompt("sentimento", titulo=n.titulo, resumo=resumo)
        if op == Operacao.QA:
            return montar_prompt("qa", contexto_numerico=contexto_txt, trechos=f"{n.titulo}\n{texto}", pergunta=pergunta)
        outros = [t for t in self._corpus.listar_titulos(limite=6) if t != n.titulo][:5]
        return montar_prompt("relatorio", contexto_numerico=contexto_txt, titulos="; ".join([n.titulo] + outros))
