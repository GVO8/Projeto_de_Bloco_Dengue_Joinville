"""Contratos HTTP (Pydantic). Request/Response models validam tudo que entra e sai da API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dengue.core.domain.modelos import Operacao


class ErroSchema(BaseModel):
    codigo: str = Field(..., examples=["modelo_indisponivel"])
    categoria: str = Field(..., description="entrada | dados | ia | sistema")
    mensagem: str = Field(..., description="O que aconteceu, em linguagem simples.")
    sugestao: str = Field("", description="O que o usuário pode fazer para resolver.")
    detalhe: Optional[str] = Field(None, description="Informação técnica (para diagnóstico).")


class ProcessarNoticiaRequest(BaseModel):
    operacao: Operacao = Field(..., description="resumo | sentimento | qa | relatorio")
    pergunta: Optional[str] = Field(None, max_length=500, description="Obrigatória apenas para a operação 'qa'.")


class RespostaProcessamentoSchema(BaseModel):
    """Ordem dos campos = ordem de exibição: título, operação, resultado, resumo final, avisos, aviso padrão."""

    noticia_id: int
    titulo: str
    operacao: Operacao
    nome_operacao: str
    resultado: str
    resumo_final: str
    avisos: list[str] = []
    aviso_padrao: str
    modelo: str
    tempo_segundos: float
    metricas: Optional[dict[str, Any]] = Field(None, description="Tempos e tokens medidos pelo adaptador do modelo (quando disponíveis).")
    markdown: str = Field(..., description="Resposta completa já formatada, pronta para exibir.")


class OperacaoSchema(BaseModel):
    operacao: Operacao
    nome: str
    exige_pergunta: bool


class NoticiaSchema(BaseModel):
    id: int
    titulo: str
    data_publicacao: Optional[str] = None
    autor: Optional[str] = None
    url: Optional[str] = None
    resumo: Optional[str] = None


class ListaNoticiasSchema(BaseModel):
    total: int
    noticias: list[NoticiaSchema]


class TextoNoticiasSchema(BaseModel):
    total_noticias: int
    texto: str


class RegistroInfoDengue(BaseModel):
    """Uma linha semanal no formato do InfoDengue. Campos extras são aceitos."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Identificador único da linha (chave de mesclagem).")
    SE: int = Field(..., description="Semana epidemiológica AAAASS, ex.: 202614.")
    nivel: int = Field(..., ge=1, le=4, description="1 verde, 2 amarelo, 3 laranja, 4 vermelho.")
    casos: Optional[int] = None

    @field_validator("id", mode="before")
    @classmethod
    def _id_como_texto(cls, v: Any) -> str:
        return str(v)


class SerieSchema(BaseModel):
    origem: str
    total: int
    dados: list[dict[str, Any]]


class ResultadoMesclagemSchema(BaseModel):
    adicionadas: int
    ignoradas_por_id_repetido: int
    total: int


class EstadoModeloSchema(BaseModel):
    backend: str
    nome: str
    pronto: bool
    carregado: bool
    detalhe: str = ""


class HealthSchema(BaseModel):
    status: str
    modelo_ia: EstadoModeloSchema


# ----------------------------------------------------------- conversa com os dados
class PerguntaChatRequest(BaseModel):
    sessao_id: Optional[str] = Field(None, max_length=64, description="Omitir para iniciar uma nova conversa.")
    pergunta: str = Field(..., min_length=1, max_length=300, description="Pergunta sobre casos de dengue em Joinville.")


class PlanoSchema(BaseModel):
    intencao: str
    ano_inicio: int
    ano_fim: int
    origem: str = Field(..., description="'ia' (plano do modelo) ou 'regras' (alternativa determinística).")


class RequisicaoInfoDengueSchema(BaseModel):
    url: str
    geocode: int
    doenca: str
    ano_inicio: int
    ano_fim: int


class EtapaSchema(BaseModel):
    nome: str
    tempo_segundos: float
    tokens_gerados: Optional[int] = None


class RespostaChatSchema(BaseModel):
    sessao_id: str
    pergunta: str
    tipo: str = Field(..., description="'resposta' ou 'recusa' (pergunta fora do escopo: só dengue em Joinville).")
    resposta: str
    plano: Optional[PlanoSchema] = None
    requisicao: Optional[RequisicaoInfoDengueSchema] = Field(None, description="Requisição feita ao InfoDengue para responder.")
    fatos: Optional[str] = Field(None, description="Fatos calculados (em código) que embasam a resposta.")
    etapas: list[EtapaSchema] = []
    avisos: list[str] = []
    aviso_padrao: str
    modelo: str
    tempo_segundos: float


class TurnoSchema(BaseModel):
    pergunta: str
    resposta: str
    tipo: str


class ConversaSchema(BaseModel):
    sessao_id: str
    turnos: list[TurnoSchema]


class HistoricoInfoDengueSchema(BaseModel):
    requisicao: RequisicaoInfoDengueSchema
    fatos: dict[str, Any]
    serie: list[dict[str, Any]]


class SentimentoSchema(BaseModel):
    noticia_id: int
    titulo: str
    classe: str
    rotulo: str
    justificativa: str
    modelo: str
    tempo_segundos: float
    analisado_em: str
    data_publicacao: Optional[str] = None


class SentimentosSchema(BaseModel):
    total: int
    por_classe: dict[str, int]
    itens: list[SentimentoSchema]
