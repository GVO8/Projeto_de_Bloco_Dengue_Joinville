"""
Raiz de composição: o ÚNICO lugar que conhece as implementações concretas.
Núcleo e adaptadores recebem suas dependências já montadas (injeção de dependência).
Testes passam suas próprias implementações (ex.: ModeloFake) pelos parâmetros.
"""

from __future__ import annotations

from dengue.adapters.outbound.conversas_memoria import ConversasEmMemoria
from dengue.adapters.outbound.infodengue import (
    ConsultaInfoDengueComCache, ConsultaInfoDengueHttp, InfoDengueAmostraCsv, InfoDengueComAlternativa, InfoDengueHttp, UploadsCsv,
)
from dengue.adapters.outbound.llm_fake import ModeloFake
from dengue.adapters.outbound.llm_llamacpp import ModeloLlamaCpp
from dengue.adapters.outbound.noticias_arquivos import CorpusJsonl, NoticiasCsvTxt
from dengue.adapters.outbound.nsc_scraper import ColetorNscTotal
from dengue.adapters.outbound.sentimentos_csv import SentimentosCsv
from dengue.config import Configuracoes
from dengue.core.ports.modelo_linguagem import ModeloLinguagem
from dengue.core.ports.repositorios import ColetorNoticias, ConsultaInfoDengue, FonteInfoDengue
from dengue.core.services.conversar_com_dados import ConversarComDados
from dengue.core.services.corpus import PrepararCorpus
from dengue.core.services.historico_infodengue import ServicoHistoricoInfoDengue
from dengue.core.services.noticias import ColetarNoticias, ServicoNoticias
from dengue.core.services.processar_noticia import ProcessarNoticia
from dengue.core.services.sentimentos import AnalisarSentimentos
from dengue.core.services.serie_infodengue import ServicoSerieInfoDengue


class Container:
    def __init__(
        self,
        config: Configuracoes | None = None,
        *,
        modelo: ModeloLinguagem | None = None,
        fonte_infodengue: FonteInfoDengue | None = None,
        coletor: ColetorNoticias | None = None,
        consulta_infodengue: ConsultaInfoDengue | None = None,
        ano_atual=None,
    ):
        self.config = config or Configuracoes.do_ambiente()
        raw, proc = self.config.data_raw, self.config.data_processed

        self.repo_noticias = NoticiasCsvTxt(raw / "nsc_noticias_joinville_dengue.csv", raw / "nsc_noticias_texto.txt")
        self.armazenamento_corpus = CorpusJsonl(proc / "noticias_corpus.jsonl", proc / "contexto_infodengue.json")
        fonte = fonte_infodengue or InfoDengueComAlternativa(InfoDengueHttp(), InfoDengueAmostraCsv(raw / "infodengue_sample.csv"))
        self.serie = ServicoSerieInfoDengue(fonte, UploadsCsv(proc / "infodengue_uploads.csv"))

        self.modelo: ModeloLinguagem = modelo or self._criar_modelo()
        self.noticias = ServicoNoticias(self.repo_noticias)
        self.preparar_corpus = PrepararCorpus(self.repo_noticias, self.serie, self.armazenamento_corpus)
        self.coletar_noticias = ColetarNoticias(coletor or ColetorNscTotal(), self.repo_noticias, self.preparar_corpus.executar)
        self.sentimentos = SentimentosCsv(proc / "sentimentos_noticias.csv")
        self.processar_noticia = ProcessarNoticia(
            self.armazenamento_corpus, self.preparar_corpus, self.repo_noticias, self.modelo, self.config.max_chars_entrada,
            sentimentos=self.sentimentos,
        )
        self.analisar_sentimentos = AnalisarSentimentos(self.processar_noticia, self.repo_noticias, self.sentimentos)

        # conversa com os dados do InfoDengue (memória por sessão) e série histórica para o painel
        self.consulta_infodengue = consulta_infodengue or ConsultaInfoDengueComCache(ConsultaInfoDengueHttp())
        self.conversas = ConversasEmMemoria()
        extra = {} if ano_atual is None else {"ano_atual": ano_atual}
        self.conversar = ConversarComDados(self.modelo, self.consulta_infodengue, self.conversas, **extra)
        self.historico_infodengue = ServicoHistoricoInfoDengue(self.consulta_infodengue, **extra)

    def _criar_modelo(self) -> ModeloLinguagem:
        if self.config.llm.backend == "fake":
            return ModeloFake()
        return ModeloLlamaCpp(self.config.llm)
