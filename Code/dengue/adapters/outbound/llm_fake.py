"""
Modelo simulado (FakeLLM). Usos: testes automatizados e demonstração sem baixar o modelo real
(DENGUE_LLM_BACKEND=fake). Nunca produz análise real: as respostas padrão são marcadas como simuladas.
"""

from __future__ import annotations

from typing import Callable

from dengue.core.domain.modelos import EstadoModelo
from dengue.core.ports.modelo_linguagem import ModeloLinguagem


def resposta_simulada(prompt: str) -> str:
    if "Converta a pergunta do usuário" in prompt:
        return '{"assunto_valido": true, "cidade": "nao_citada", "intencao": "total", "ano_inicio": null, "ano_fim": null}'
    if "Dados do InfoDengue:" in prompt:
        return "Resposta simulada a partir dos dados do InfoDengue. [resposta simulada, sem IA real]"
    if "Classifique o sentimento" in prompt:
        return "NEUTRO. [resposta simulada, sem IA real]"
    if "boletim" in prompt.lower():
        return "Boletim simulado sobre a dengue em Joinville. [resposta simulada, sem IA real]"
    if "Pergunta:" in prompt:
        return "Resposta simulada à pergunta. [resposta simulada, sem IA real]"
    return "Resumo simulado da notícia. Segunda frase simulada. [resposta simulada, sem IA real]"


class ModeloFake(ModeloLinguagem):
    def __init__(self, resposta: str | Callable[[str], str] | None = None, *, nome: str = "FakeLLM (simulado)",
                 erro: Exception | None = None, pronto: bool = True):
        self._resposta, self._nome, self._erro, self._pronto = resposta, nome, erro, pronto
        self.chamadas: list[dict] = []
        self._ultima: str | None = None

    @property
    def nome(self) -> str:
        return self._nome

    def estado(self) -> EstadoModelo:
        return EstadoModelo("fake", self._nome, pronto=self._pronto, carregado=True, detalhe="modelo simulado")

    def ultimas_metricas(self) -> dict | None:
        return None if self._ultima is None else {"tokens_gerados": len(self._ultima.split()), "simulado": True}

    def gerar(self, prompt: str, *, max_tokens: int, formato_json: bool = False) -> str:
        self.chamadas.append({"prompt": prompt, "max_tokens": max_tokens, "formato_json": formato_json})
        if self._erro:
            raise self._erro
        if callable(self._resposta):
            saida = self._resposta(prompt)
        else:
            saida = self._resposta if self._resposta is not None else resposta_simulada(prompt)
        self._ultima = saida
        return saida
