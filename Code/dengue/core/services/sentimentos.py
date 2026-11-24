"""Análise de sentimento (preocupação) das notícias em lote, com resultados guardados para o painel."""

from __future__ import annotations

from dataclasses import dataclass, field

from dengue.core.domain.erros import ErroDeIA, ErroDengue, ModeloIndisponivelError, ModeloOcupadoError
from dengue.core.domain.modelos import Operacao
from dengue.core.ports.repositorios import RepositorioNoticias, RepositorioSentimentos
from dengue.core.services.processar_noticia import ProcessarNoticia


@dataclass
class ResumoLote:
    analisadas: int = 0
    ignoradas: int = 0                       # já analisadas antes
    falhas: list[tuple[int, str]] = field(default_factory=list)


class AnalisarSentimentos:
    def __init__(self, processar: ProcessarNoticia, noticias: RepositorioNoticias, repo: RepositorioSentimentos):
        self._processar, self._noticias, self._repo = processar, noticias, repo

    def executar(self, somente_pendentes: bool = True, progresso=None) -> ResumoLote:
        """Roda o sentimento em cada notícia. Falha de uma notícia não derruba o lote; modelo indisponível sim."""
        feitas = {s.noticia_id for s in self._repo.listar()} if somente_pendentes else set()
        resumo = ResumoLote()
        for n in self._noticias.listar():
            if n.id in feitas:
                resumo.ignoradas += 1
                continue
            if progresso:
                progresso(n)
            try:
                self._processar.executar(n.id, Operacao.SENTIMENTO)   # o caso de uso também guarda o resultado
                resumo.analisadas += 1
            except (ModeloIndisponivelError, ModeloOcupadoError):
                raise                                                  # sem modelo, o lote inteiro falharia
            except (ErroDeIA, ErroDengue) as exc:
                resumo.falhas.append((n.id, exc.mensagem))
        return resumo
