"""Rotas HTTP. Finas por design: validam entrada, chamam um caso de uso e formatam a saída."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query, Request

from dengue.container import Container
from dengue.core.domain.chat import RespostaChat
from dengue.core.domain.erros import EntradaInvalidaError, SessaoNaoEncontradaError
from dengue.core.domain.modelos import Operacao, RespostaProcessamento
from dengue.adapters.inbound.api_fastapi.schemas import (
    EstadoModeloSchema, ErroSchema, HealthSchema, ListaNoticiasSchema, NoticiaSchema, OperacaoSchema,
    ProcessarNoticiaRequest, RegistroInfoDengue, ResultadoMesclagemSchema, RespostaProcessamentoSchema,
    SerieSchema, TextoNoticiasSchema, ConversaSchema, EtapaSchema, HistoricoInfoDengueSchema, PerguntaChatRequest, PlanoSchema,
    RequisicaoInfoDengueSchema, RespostaChatSchema, SentimentoSchema, SentimentosSchema, TurnoSchema,
)

router = APIRouter()


def obter_container(request: Request) -> Container:
    return request.app.state.container


def _registros(df: pd.DataFrame) -> list[dict]:
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


def _para_schema(r: RespostaProcessamento) -> RespostaProcessamentoSchema:
    return RespostaProcessamentoSchema(
        noticia_id=r.noticia_id, titulo=r.titulo, operacao=r.operacao, nome_operacao=r.nome_operacao,
        resultado=r.resultado, resumo_final=r.resumo_final, avisos=list(r.avisos), aviso_padrao=r.aviso_padrao,
        modelo=r.modelo, tempo_segundos=r.tempo_segundos, metricas=r.metricas, markdown=r.para_markdown(),
    )


# ----------------------------------------------------------------- sistema
@router.get("/health", response_model=HealthSchema, tags=["Sistema"], summary="API no ar e estado do modelo de IA")
def health(c: Container = Depends(obter_container)):
    e = c.modelo.estado()
    return HealthSchema(status="ok", modelo_ia=EstadoModeloSchema(**e.__dict__))


@router.get("/operacoes", response_model=list[OperacaoSchema], tags=["IA"], summary="Operações de IA disponíveis")
def operacoes():
    return [OperacaoSchema(operacao=o, nome=o.nome, exige_pergunta=o.exige_pergunta) for o in Operacao]


# --------------------------------------------------------------- InfoDengue
@router.get("/infodengue", response_model=SerieSchema, tags=["InfoDengue"], summary="Série semanal (base + dados enviados)")
def get_infodengue(
    se_inicio: Optional[int] = Query(None, description="SE inicial (AAAASS), inclusiva."),
    se_fim: Optional[int] = Query(None, description="SE final (AAAASS), inclusiva."),
    nivel: Optional[list[int]] = Query(None, description="Um ou mais níveis (1–4): ?nivel=3&nivel=4"),
    c: Container = Depends(obter_container),
):
    df, origem = c.serie.obter(se_inicio, se_fim, nivel)
    return SerieSchema(origem=origem, total=len(df), dados=_registros(df))


@router.post("/infodengue", response_model=ResultadoMesclagemSchema, tags=["InfoDengue"], summary="Envia novas linhas semanais",
             responses={422: {"model": ErroSchema}})
def post_infodengue(registros: list[RegistroInfoDengue], c: Container = Depends(obter_container)):
    """Se um `id` já existir, a linha ORIGINAL é mantida e a enviada é ignorada."""
    if not registros:
        raise EntradaInvalidaError("Nenhum registro foi enviado.", "Envie uma lista com ao menos um registro.")
    return c.serie.adicionar(pd.DataFrame([r.model_dump() for r in registros]))


@router.delete("/infodengue/uploads", status_code=204, tags=["InfoDengue"], summary="Descarta os dados enviados")
def delete_uploads(c: Container = Depends(obter_container)):
    c.serie.resetar()


# ----------------------------------------------------------------- notícias
@router.get("/noticias", response_model=ListaNoticiasSchema, tags=["Notícias"], summary="Lista as notícias coletadas")
def get_noticias(
    busca: Optional[str] = Query(None, description="Filtra por trecho no título."),
    limit: int = Query(20, ge=1, le=200, description="Máximo de notícias."),
    c: Container = Depends(obter_container),
):
    itens = c.noticias.listar(busca, limit)
    return ListaNoticiasSchema(total=len(itens), noticias=[NoticiaSchema(**n.__dict__) for n in itens])


@router.get("/noticias/texto", response_model=TextoNoticiasSchema, tags=["Notícias"], summary="Texto limpo de todas as notícias (nuvem de palavras)")
def get_texto(c: Container = Depends(obter_container)):
    return TextoNoticiasSchema(total_noticias=len(c.noticias.listar()), texto=c.noticias.texto_para_nuvem())


@router.get("/noticias/{noticia_id}", response_model=NoticiaSchema, tags=["Notícias"], summary="Uma notícia",
            responses={404: {"model": ErroSchema}})
def get_noticia(noticia_id: int, c: Container = Depends(obter_container)):
    return NoticiaSchema(**c.noticias.obter(noticia_id).__dict__)


# ---------------------------------------------------------------------- IA
@router.post(
    "/noticias/{noticia_id}/processar", response_model=RespostaProcessamentoSchema, tags=["IA"],
    summary="Processa uma notícia com o modelo de linguagem local",
    responses={404: {"model": ErroSchema}, 422: {"model": ErroSchema}, 429: {"model": ErroSchema},
               502: {"model": ErroSchema}, 503: {"model": ErroSchema}, 504: {"model": ErroSchema}},
)
def processar_noticia(noticia_id: int, corpo: ProcessarNoticiaRequest, c: Container = Depends(obter_container)):
    """Busca a notícia completa no corpus, monta o prompt da operação e devolve a resposta do modelo."""
    return _para_schema(c.processar_noticia.executar(noticia_id, corpo.operacao, corpo.pergunta))


# ------------------------------------------------- conversa com os dados do InfoDengue
def _chat_schema(r: RespostaChat) -> RespostaChatSchema:
    return RespostaChatSchema(
        sessao_id=r.sessao_id, pergunta=r.pergunta, tipo=r.tipo, resposta=r.resposta,
        plano=PlanoSchema(**r.plano.__dict__) if r.plano else None,
        requisicao=RequisicaoInfoDengueSchema(**r.requisicao.__dict__) if r.requisicao else None,
        fatos=r.fatos, etapas=[EtapaSchema(**e.__dict__) for e in r.etapas], avisos=list(r.avisos),
        aviso_padrao=r.aviso_padrao, modelo=r.modelo, tempo_segundos=r.tempo_segundos,
    )


@router.post(
    "/chat", response_model=RespostaChatSchema, tags=["Conversa"],
    summary="Pergunta em linguagem natural sobre casos de dengue em Joinville",
    responses={422: {"model": ErroSchema}, 429: {"model": ErroSchema}, 502: {"model": ErroSchema},
               503: {"model": ErroSchema}, 504: {"model": ErroSchema}},
)
def post_chat(corpo: PerguntaChatRequest, c: Container = Depends(obter_container)):
    """
    A IA converte a pergunta em uma requisição ao InfoDengue (sempre Joinville, sempre dengue), os números são
    calculados em código e a IA redige a resposta só a partir deles. A conversa tem memória por `sessao_id`.
    Perguntas de outras cidades ou assuntos recebem `tipo: "recusa"` (HTTP 200) com exemplos do que perguntar.
    """
    return _chat_schema(c.conversar.executar(corpo.sessao_id, corpo.pergunta))


@router.get("/chat/{sessao_id}", response_model=ConversaSchema, tags=["Conversa"], summary="Histórico de uma conversa",
            responses={404: {"model": ErroSchema}})
def get_chat(sessao_id: str, c: Container = Depends(obter_container)):
    if not c.conversas.existe(sessao_id):
        raise SessaoNaoEncontradaError(sessao_id)
    return ConversaSchema(sessao_id=sessao_id, turnos=[TurnoSchema(pergunta=t.pergunta, resposta=t.resposta, tipo=t.tipo)
                                                      for t in c.conversas.obter(sessao_id)])


@router.delete("/chat/{sessao_id}", status_code=204, tags=["Conversa"], summary="Encerra uma conversa (apaga a memória)")
def delete_chat(sessao_id: str, c: Container = Depends(obter_container)):
    c.conversas.limpar(sessao_id)


# ------------------------------------------------------- histórico e sentimentos
@router.get("/infodengue/historico", response_model=HistoricoInfoDengueSchema, tags=["InfoDengue"],
            summary="Série semanal de vários anos + fatos calculados (dados reais, sem alternativa sintética)",
            responses={422: {"model": ErroSchema}, 503: {"model": ErroSchema}})
def get_historico(
    ano_inicio: Optional[int] = Query(None, description="Padrão: três anos antes do final."),
    ano_fim: Optional[int] = Query(None, description="Padrão: ano atual."),
    c: Container = Depends(obter_container),
):
    df, fatos, req = c.historico_infodengue.obter(ano_inicio, ano_fim)
    colunas = [x for x in ("SE", "data_iniSE", "casos", "casos_est", "nivel", "Rt", "tempmed", "umidmed") if x in df.columns]
    serie = df[colunas].copy()
    serie["ano"], serie["semana"] = serie["SE"] // 100, serie["SE"] % 100
    return HistoricoInfoDengueSchema(requisicao=RequisicaoInfoDengueSchema(**req.__dict__), fatos=fatos.estruturado, serie=_registros(serie))


@router.get("/sentimentos", response_model=SentimentosSchema, tags=["Notícias"],
            summary="Sentimento (preocupação) das notícias já analisadas pela IA")
def get_sentimentos(c: Container = Depends(obter_container)):
    itens = c.sentimentos.listar()
    por_classe: dict[str, int] = {}
    for s in itens:
        por_classe[s.classe] = por_classe.get(s.classe, 0) + 1
    return SentimentosSchema(total=len(itens), por_classe=por_classe,
                             itens=[SentimentoSchema(**{**s.__dict__, "rotulo": s.rotulo}) for s in itens])
