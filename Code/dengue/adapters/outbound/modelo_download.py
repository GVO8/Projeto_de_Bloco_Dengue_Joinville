"""Download do arquivo GGUF do Hugging Face Hub para a pasta Models/."""

from __future__ import annotations

from pathlib import Path

from dengue.config import ConfigLlm
from dengue.core.domain.erros import ModeloIndisponivelError


def baixar_modelo(config: ConfigLlm) -> Path:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise ModeloIndisponivelError("download", modelo=config.nome_exibicao,
                                      detalhe="instale com: pip install huggingface_hub") from exc
    try:
        config.pasta_modelos.mkdir(parents=True, exist_ok=True)
        caminho = hf_hub_download(repo_id=config.repo_id, filename=config.arquivo, local_dir=str(config.pasta_modelos))
        return Path(caminho)
    except Exception as exc:
        raise ModeloIndisponivelError("download", modelo=config.nome_exibicao, detalhe=str(exc)) from exc
