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
    def gerar(self, prompt: str, *, max_tokens: int) -> str:
        """Gera texto. Deve levantar ErroDeIA (nunca exceções cruas) em caso de falha."""
