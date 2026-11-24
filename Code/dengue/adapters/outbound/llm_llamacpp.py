"""
Adaptador do modelo local via llama.cpp (llama-cpp-python) + arquivo GGUF do Hugging Face.

Decisões de robustez:
- O modelo é carregado sob demanda (a API sobe rápido e o /health não gasta memória).
- Uma inferência por vez (CPU/GPU pequenas): chamadas concorrentes esperam, e se a espera
  estourar o limite viram ModeloOcupadoError.
- A geração usa streaming para poder interromper no limite de tempo (timeout real).
- Nenhuma exceção crua escapa: tudo vira ErroDeIA com mensagem amigável.
"""

from __future__ import annotations

import logging
import threading
import time

from dengue.config import ConfigLlm
from dengue.core.domain.erros import (
    ErroDeIA, ModeloFalhaError, ModeloIndisponivelError, ModeloOcupadoError, ModeloTimeoutError, RespostaVaziaError,
)
from dengue.core.domain.modelos import EstadoModelo
from dengue.core.ports.modelo_linguagem import ModeloLinguagem

log = logging.getLogger(__name__)


def _importar_llama():
    from llama_cpp import Llama  # import tardio: a biblioteca é opcional
    return Llama


class ModeloLlamaCpp(ModeloLinguagem):
    def __init__(self, config: ConfigLlm, fabrica_llama=_importar_llama, relogio=time.monotonic, medidor=time.perf_counter):
        self._cfg, self._fabrica, self._relogio, self._medir = config, fabrica_llama, relogio, medidor
        self._llm = None
        self._metricas: dict | None = None
        self._tempo_carga = 0.0
        self._lock = threading.Lock()

    @property
    def nome(self) -> str:
        return self._cfg.nome_exibicao

    def estado(self) -> EstadoModelo:
        existe = self._cfg.caminho_modelo.exists()
        detalhe = "" if existe else f"arquivo não encontrado: {self._cfg.caminho_modelo}"
        return EstadoModelo("llamacpp", self.nome, pronto=existe, carregado=self._llm is not None, detalhe=detalhe)

    def ultimas_metricas(self) -> dict | None:
        return self._metricas

    # ------------------------------------------------------------------
    def _carregar(self):
        if self._llm is not None:
            return
        caminho = self._cfg.caminho_modelo
        if not caminho.exists():
            raise ModeloIndisponivelError("arquivo_ausente", modelo=self.nome, detalhe=str(caminho))
        try:
            Llama = self._fabrica()
        except ImportError as exc:
            raise ModeloIndisponivelError("biblioteca", modelo=self.nome, detalhe=str(exc)) from exc
        inicio = self._medir()
        try:
            self._llm = Llama(
                model_path=str(caminho), n_ctx=self._cfg.n_ctx, n_threads=self._cfg.n_threads,
                n_gpu_layers=self._cfg.n_gpu_layers, verbose=False,
            )
            self._tempo_carga = self._medir() - inicio
        except Exception as exc:
            log.exception("Falha ao carregar o modelo")
            raise ModeloIndisponivelError("carga", modelo=self.nome, detalhe=str(exc)) from exc

    def gerar(self, prompt: str, *, max_tokens: int, formato_json: bool = False) -> str:
        if not self._lock.acquire(timeout=self._cfg.timeout_s):
            raise ModeloOcupadoError(modelo=self.nome)
        try:
            self._tempo_carga = 0.0
            self._carregar()
            return self._gerar_com_prazo(prompt, max_tokens, formato_json)
        except ErroDeIA:
            raise
        except Exception as exc:
            log.exception("Falha na inferência")
            raise ModeloFalhaError(modelo=self.nome, detalhe=str(exc)) from exc
        finally:
            self._lock.release()

    def _gerar_com_prazo(self, prompt: str, max_tokens: int, formato_json: bool = False) -> str:
        limite = self._relogio() + self._cfg.timeout_s
        extras = {"response_format": {"type": "json_object"}} if formato_json else {}
        inicio = self._medir()
        fluxo = self._llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens,
            temperature=self._cfg.temperatura, top_p=self._cfg.top_p, stream=True, **extras,
        )
        pedacos: list[str] = []
        primeiro: float | None = None
        try:
            for chunk in fluxo:
                pedaco = chunk["choices"][0].get("delta", {}).get("content") or ""
                if pedaco and primeiro is None:
                    primeiro = self._medir() - inicio
                pedacos.append(pedaco)
                if self._relogio() > limite:
                    raise ModeloTimeoutError(self._cfg.timeout_s, modelo=self.nome)
        finally:
            fechar = getattr(fluxo, "close", None)
            if fechar:
                fechar()
        texto = "".join(pedacos).strip()
        if not texto:
            raise RespostaVaziaError(modelo=self.nome)
        total = self._medir() - inicio
        tokens = sum(1 for p in pedacos if p)                     # cada trecho do streaming ≈ 1 token
        geracao = max(total - (primeiro or 0.0), 1e-9)
        self._metricas = {
            "tempo_carga_s": round(self._tempo_carga, 2), "tempo_primeiro_token_s": round(primeiro or 0.0, 2),
            "tokens_gerados": tokens, "tempo_geracao_s": round(geracao, 2),
            "tokens_por_s": round(max(tokens - 1, 0) / geracao, 2), "tempo_total_s": round(total + self._tempo_carga, 2),
        }
        return texto
