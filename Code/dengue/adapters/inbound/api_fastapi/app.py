"""Fábrica da aplicação FastAPI (adaptador de entrada HTTP)."""

from __future__ import annotations

from fastapi import FastAPI

from dengue.adapters.inbound.api_fastapi.erros import registrar_tratadores
from dengue.adapters.inbound.api_fastapi.rotas import router
from dengue.container import Container


def create_app(container: Container | None = None) -> FastAPI:
    app = FastAPI(
        title="API Dengue em Múltiplas Dimensões — Joinville/SC",
        description="Série semanal do InfoDengue, notícias coletadas e processamento de notícias por IA local.",
        version="0.4.0",
    )
    app.state.container = container or Container()
    registrar_tratadores(app)
    app.include_router(router)
    return app


app = create_app()  # usado pelo uvicorn: dengue.adapters.inbound.api_fastapi.app:app
