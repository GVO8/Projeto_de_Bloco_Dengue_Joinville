"""
Raiz de composição: o ÚNICO lugar que conhece as implementações concretas.
Núcleo e adaptadores recebem suas dependências já montadas (injeção de dependência).
Testes passam suas próprias implementações (ex.: ModeloFake) pelos parâmetros.
"""

from __future__ import annotations

from dengue.adapters.outbound.infodengue import InfoDengueAmostraCsv, InfoDengueComAlternativa, InfoDengueHttp, UploadsCsv
from dengue.adapters.outbound.llm_fake import ModeloFake
from dengue.adapters.outbound.llm_llamacpp import ModeloLlamaCpp
from dengue.adapters.outbound.noticias_arquivos import CorpusJsonl, NoticiasCsvTxt
from dengue.adapters.outbound.nsc_scraper import ColetorNscTotal
from dengue.config import Configuracoes
from dengue.core.ports.modelo_linguagem import ModeloLinguagem
from dengue.core.ports.repositorios import ColetorNoticias, FonteInfoDengue
from dengue.core.services.corpus import PrepararCorpus
from dengue.core.services.noticias import ColetarNoticias, ServicoNoticias
from dengue.core.services.processar_noticia import ProcessarNoticia
from dengue.core.services.serie_infodengue import ServicoSerieInfoDengue


class Container:
    def __init__(
        self,
        config: Configuracoes | None = None,
        *,
        modelo: ModeloLinguagem | None = None,
        fonte_infodengue: FonteInfoDengue | None = None,
        coletor: ColetorNoticias | None = None,
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
        self.processar_noticia = ProcessarNoticia(
            self.armazenamento_corpus, self.preparar_corpus, self.repo_noticias, self.modelo, self.config.max_chars_entrada,
        )

    def _criar_modelo(self) -> ModeloLinguagem:
        if self.config.llm.backend == "fake":
            return ModeloFake()
        return ModeloLlamaCpp(self.config.llm)
