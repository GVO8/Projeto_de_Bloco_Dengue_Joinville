"""Tradução de exceções em respostas HTTP amigáveis (todas no formato ErroSchema)."""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from dengue.core.domain.erros import ErroDengue

log = logging.getLogger(__name__)

_TRADUCAO = {
    "missing": "campo obrigatório ausente",
    "enum": "valor não permitido",
    "string_too_long": "texto longo demais",
    "string_too_short": "texto curto demais (escreva algo)",
    "less_than_equal": "valor acima do máximo permitido",
    "greater_than_equal": "valor abaixo do mínimo permitido",
    "int_parsing": "deveria ser um número inteiro",
    "string_type": "deveria ser um texto",
    "json_invalid": "o corpo da requisição não é um JSON válido",
}


def _descrever(erro: dict) -> str:
    partes = []
    for p in erro.get("loc", []):
        if p in ("body", "query", "path"):
            continue
        partes.append(f"registro {p + 1}" if isinstance(p, int) else f"campo '{p}'")
    motivo = _TRADUCAO.get(erro.get("type", ""), erro.get("msg", "valor inválido"))
    return f"{', '.join(partes)}: {motivo}" if partes else motivo


def _resposta(status: int, codigo: str, categoria: str, mensagem: str, sugestao: str, detalhe: str | None = None):
    corpo = {"codigo": codigo, "categoria": categoria, "mensagem": mensagem, "sugestao": sugestao, "detalhe": detalhe}
    return JSONResponse(status_code=status, content=corpo)


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(ErroDengue)
    async def _erro_dominio(_: Request, exc: ErroDengue):
        if exc.status_http >= 500:
            log.warning("%s: %s | %s", exc.codigo, exc.mensagem, exc.detalhe)
        return JSONResponse(status_code=exc.status_http, content=exc.como_dict())

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, exc: RequestValidationError):
        problemas = "; ".join(_descrever(e) for e in exc.errors())
        return _resposta(
            422, "dados_invalidos", "entrada", f"Os dados enviados não são válidos: {problemas}.",
            "Corrija os campos indicados e envie novamente. A documentação está em /docs.",
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return _resposta(404, "rota_inexistente", "entrada", "Esse endereço não existe na API.", "Consulte as rotas disponíveis em /docs.")
        if exc.status_code == 405:
            return _resposta(405, "metodo_nao_permitido", "entrada", "Esse método HTTP não é aceito nesta rota.", "Confira o método correto em /docs.")
        return _resposta(exc.status_code, "erro_http", "sistema", str(exc.detail), "Tente novamente.")

    @app.exception_handler(Exception)
    async def _inesperado(_: Request, exc: Exception):
        protocolo = uuid.uuid4().hex[:8]
        log.exception("Erro inesperado [%s]", protocolo)
        return _resposta(
            500, "erro_interno", "sistema", "Algo inesperado aconteceu no servidor.",
            f"Tente novamente. Se persistir, informe o código {protocolo} ao responsável (consta no log da API).", protocolo,
        )
