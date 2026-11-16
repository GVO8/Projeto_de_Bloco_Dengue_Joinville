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
