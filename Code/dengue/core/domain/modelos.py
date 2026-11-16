"""Entidades e objetos de valor do domínio. Sem dependências de I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from dengue.core.prompts import PROMPTS

AVISO_PADRAO = (
    "⚠️ Este conteúdo foi gerado por um modelo de IA e pode conter erros ou imprecisões. "
    "Confira as informações na notícia original antes de usá-las."
)

NIVEL_LABELS = {1: "1 — Verde", 2: "2 — Amarelo", 3: "3 — Laranja", 4: "4 — Vermelho"}


class Operacao(str, Enum):
    RESUMO = "resumo"
    SENTIMENTO = "sentimento"
    QA = "qa"
    RELATORIO = "relatorio"

    @property
    def nome(self) -> str:
        return PROMPTS[self.value]["titulo"]

    @property
    def max_tokens(self) -> int:
        return PROMPTS[self.value]["max_tokens"]

    @property
    def exige_pergunta(self) -> bool:
        return PROMPTS[self.value]["exige_pergunta"]


@dataclass(frozen=True)
class Noticia:
    id: int
    titulo: str
    data_publicacao: str | None = None
    autor: str | None = None
    url: str | None = None
    resumo: str | None = None


@dataclass(frozen=True)
class ArtigoColetado:
    titulo: str
    url: str
    data_publicacao: str = ""
    autor: str = ""
    resumo: str = ""
    corpo: str = ""


@dataclass(frozen=True)
class TrechoCorpus:
    id_noticia: int
    chunk_id: int
    titulo: str
    texto: str
    data_publicacao: str | None = None
    autor: str | None = None
    url: str | None = None
    resumo: str | None = None


@dataclass(frozen=True)
class NoticiaCompleta:
    id: int
    titulo: str
    texto: str
    data_publicacao: str | None = None
    autor: str | None = None
    url: str | None = None
    resumo: str | None = None


@dataclass(frozen=True)
class ContextoNumerico:
    municipio: str
    origem_dados: str
    semanas: int
    semanas_por_nivel: dict[str, int] = field(default_factory=dict)
    casos_total: int | None = None
    semana_pico: dict | None = None

    @property
    def dados_sinteticos(self) -> bool:
        return self.origem_dados == "amostra_local"

    def como_texto(self) -> str:
        niveis = ", ".join(f"nível {k}: {v} semanas" for k, v in sorted(self.semanas_por_nivel.items()))
        partes = [f"{self.municipio}; {self.semanas} semanas analisadas; {niveis}"]
        if self.casos_total is not None:
            partes.append(f"total de {self.casos_total} casos")
        if self.semana_pico:
            partes.append(f"pico na semana {self.semana_pico.get('SE')} com {self.semana_pico.get('casos')} casos")
        texto = "; ".join(partes) + "."
        if self.dados_sinteticos:
            texto = "ATENÇÃO: dados de exemplo (sintéticos), não oficiais. " + texto
        return texto

    def como_dict(self) -> dict:
        return {
            "municipio": self.municipio, "origem_dados": self.origem_dados, "semanas": self.semanas,
            "semanas_por_nivel": self.semanas_por_nivel, "casos_total": self.casos_total,
            "semana_pico": self.semana_pico,
        }

    @classmethod
    def de_dict(cls, d: dict) -> "ContextoNumerico":
        return cls(
            municipio=d.get("municipio", "Joinville/SC"), origem_dados=d.get("origem_dados", "desconhecida"),
            semanas=int(d.get("semanas", 0)), semanas_por_nivel=dict(d.get("semanas_por_nivel", {})),
            casos_total=d.get("casos_total"), semana_pico=d.get("semana_pico"),
        )


@dataclass(frozen=True)
class EstadoModelo:
    backend: str
    nome: str
    pronto: bool          # arquivo e biblioteca disponíveis (ou backend simulado)
    carregado: bool       # já está na memória
    detalhe: str = ""


@dataclass(frozen=True)
class RespostaProcessamento:
    """Resposta padronizada. Ordem de exibição: título, operação, resultado,
    resumo final, avisos e, por último, o aviso padrão sobre erros da IA."""

    noticia_id: int
    titulo: str
    operacao: Operacao
    resultado: str
    resumo_final: str
    modelo: str
    tempo_segundos: float
    avisos: tuple[str, ...] = ()
    aviso_padrao: str = AVISO_PADRAO

    @property
    def nome_operacao(self) -> str:
        return self.operacao.nome

    def para_markdown(self) -> str:
        blocos = [
            f"### {self.titulo}",
            f"**Operação:** {self.nome_operacao}",
            f"**Resultado:**\n\n{self.resultado}",
            f"**Resumo final:** {self.resumo_final}",
        ]
        blocos += [f"ℹ️ {a}" for a in self.avisos]
        blocos.append(f"_{self.aviso_padrao}_")
        return "\n\n".join(blocos)
