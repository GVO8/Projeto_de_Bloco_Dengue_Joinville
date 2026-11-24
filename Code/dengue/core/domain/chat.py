"""Entidades da conversa com os dados do InfoDengue (memória conversacional)."""

from __future__ import annotations

from dataclasses import dataclass, field

from dengue.core.domain.modelos import AVISO_PADRAO

GEOCODE_JOINVILLE = 4209102
MUNICIPIO = "Joinville/SC"
ANO_MINIMO_VALIDO = 2010          # nenhuma consulta abaixo disso
JANELA_HISTORICA_ANOS = 10        # janela padrão quando a pergunta pede "todos os anos"
MAX_PERGUNTA = 300

PERGUNTAS_EXEMPLO = (
    "Qual foi o pico de casos de dengue em 2026 em Joinville e quando foi?",
    "Qual foi o ano com mais casos de dengue?",
    "Qual foi o ano com menos casos de dengue?",
    "Os casos de dengue subiram ou diminuíram em relação ao ano passado?",
)


@dataclass(frozen=True)
class PlanoConsulta:
    """Como a pergunta virou uma requisição ao InfoDengue (sempre Joinville, sempre dengue)."""

    intencao: str
    ano_inicio: int
    ano_fim: int
    origem: str = "ia"            # "ia" (plano do modelo) | "regras" (alternativa determinística)


@dataclass(frozen=True)
class RequisicaoInfoDengue:
    url: str
    geocode: int
    doenca: str
    ano_inicio: int
    ano_fim: int


@dataclass(frozen=True)
class Turno:
    pergunta: str
    resposta: str
    tipo: str                     # "resposta" | "recusa"
    ano_inicio: int | None = None
    ano_fim: int | None = None


@dataclass(frozen=True)
class EtapaMedida:
    nome: str                     # "planejamento" | "consulta_infodengue" | "resposta"
    tempo_segundos: float
    tokens_gerados: int | None = None


@dataclass(frozen=True)
class RespostaChat:
    sessao_id: str
    pergunta: str
    tipo: str                     # "resposta" | "recusa"
    resposta: str
    modelo: str
    tempo_segundos: float
    plano: PlanoConsulta | None = None
    requisicao: RequisicaoInfoDengue | None = None
    fatos: str | None = None
    etapas: tuple[EtapaMedida, ...] = ()
    avisos: tuple[str, ...] = field(default_factory=tuple)
    aviso_padrao: str = AVISO_PADRAO
