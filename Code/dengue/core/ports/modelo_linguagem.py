from __future__ import annotations

from abc import ABC, abstractmethod

from dengue.core.domain.modelos import EstadoModelo


class ModeloLinguagem(ABC):
    """Porta para qualquer LLM (llama.cpp, Transformers, simulado...)."""

    @property
    @abstractmethod
    def nome(self) -> str: ...

    @abstractmethod
    def estado(self) -> EstadoModelo:
        """Informa se o modelo está pronto, sem carregá-lo na memória."""

    @abstractmethod
    def gerar(self, prompt: str, *, max_tokens: int, formato_json: bool = False) -> str:
        """Gera texto (ou um objeto JSON, se `formato_json`). Deve levantar ErroDeIA, nunca exceções cruas."""

    def ultimas_metricas(self) -> dict | None:
        """Métricas da última geração (tempos, tokens), se o adaptador as medir."""
        return None
