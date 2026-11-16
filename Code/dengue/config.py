"""Configuração central, lida do ambiente (variáveis DENGUE_*), com padrões seguros."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ConfigLlm:
    backend: str = "llamacpp"                    # "llamacpp" (real) | "fake" (simulado, p/ testes e demonstração)
    repo_id: str = "unsloth/Qwen3-4B-Instruct-2507-GGUF"
    arquivo: str = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    nome_exibicao: str = "Qwen3-4B-Instruct-2507 (Q4_K_M)"
    pasta_modelos: Path = RAIZ / "Models"
    caminho_personalizado: Path | None = None
    n_ctx: int = 4096
    n_threads: int | None = None                 # None = padrão do llama.cpp
    n_gpu_layers: int = 0                        # 0 = só CPU; -1 = tudo na GPU
    temperatura: float = 0.2                     # baixa: resumos fiéis, menos "criatividade"
    top_p: float = 0.8
    timeout_s: float = 600.0                     # CPU antiga: a resposta pode levar minutos

    @property
    def caminho_modelo(self) -> Path:
        return self.caminho_personalizado or (self.pasta_modelos / self.arquivo)


@dataclass(frozen=True)
class Configuracoes:
    raiz: Path = RAIZ
    api_url: str = "http://127.0.0.1:8000"
    max_chars_entrada: int = 8000
    llm: ConfigLlm = ConfigLlm()

    @property
    def data_raw(self) -> Path:
        return self.raiz / "Data" / "Raw"

    @property
    def data_processed(self) -> Path:
        return self.raiz / "Data" / "Processed"

    @classmethod
    def do_ambiente(cls, env=None, raiz: Path | None = None) -> "Configuracoes":
        env = os.environ if env is None else env
        raiz = raiz or RAIZ

        def _num(chave, padrao, tipo):
            try:
                return tipo(env[chave]) if env.get(chave) else padrao
            except ValueError:
                return padrao

        base = ConfigLlm()
        caminho = env.get("DENGUE_LLM_CAMINHO")
        llm = ConfigLlm(
            backend=env.get("DENGUE_LLM_BACKEND", base.backend).lower(),
            repo_id=env.get("DENGUE_LLM_REPO", base.repo_id),
            arquivo=env.get("DENGUE_LLM_ARQUIVO", base.arquivo),
            pasta_modelos=raiz / "Models",
            caminho_personalizado=Path(caminho) if caminho else None,
            n_ctx=_num("DENGUE_LLM_N_CTX", base.n_ctx, int),
            n_threads=_num("DENGUE_LLM_THREADS", None, int),
            n_gpu_layers=_num("DENGUE_LLM_GPU_LAYERS", base.n_gpu_layers, int),
            temperatura=_num("DENGUE_LLM_TEMPERATURA", base.temperatura, float),
            timeout_s=_num("DENGUE_LLM_TIMEOUT_S", base.timeout_s, float),
        )
        return cls(
            raiz=raiz, api_url=env.get("DENGUE_API_URL", "http://127.0.0.1:8000"),
            max_chars_entrada=_num("DENGUE_MAX_CHARS_ENTRADA", 8000, int), llm=llm,
        )
