"""Evidência de execução real do modelo: coleta o ambiente e formata o relatório de medição (Markdown)."""

from __future__ import annotations

import os
import platform
from datetime import datetime


def coletar_ambiente(config, hardware: str = "") -> dict:
    try:
        import llama_cpp
        versao_llama = getattr(llama_cpp, "__version__", "instalada (versão desconhecida)")
    except ImportError:
        versao_llama = "não instalada"
    arquivo = config.llm.caminho_modelo
    tamanho = f"{arquivo.stat().st_size / 1e9:.2f} GB" if arquivo.exists() else "arquivo não encontrado"
    return {
        "Data e hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "Hardware informado": hardware or "(não informado — use --hardware ou DENGUE_HARDWARE)",
        "Sistema operacional": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "Processador (SO)": platform.processor() or "desconhecido",
        "Threads lógicas": str(os.cpu_count()),
        "Python": platform.python_version(),
        "llama-cpp-python": versao_llama,
        "Modelo": f"{config.llm.nome_exibicao} — {arquivo.name} ({tamanho})",
        "n_ctx · threads · camadas na GPU": f"{config.llm.n_ctx} · {config.llm.n_threads or 'auto'} · {config.llm.n_gpu_layers}",
    }


def renderizar_markdown(ambiente: dict, execucoes: list[dict]) -> str:
    linhas = [
        "# Evidência de execução real do modelo local", "",
        "> Gerado automaticamente por `python Code/cli.py medir-modelo`. Os tempos foram **medidos nesta máquina**, com o modelo real",
        "> (nenhum FakeLLM). Tokens = trechos devolvidos pelo streaming (≈ 1 token cada).", "",
        "## Ambiente", "", "| Item | Valor |", "|---|---|",
        *[f"| {k} | {v} |" for k, v in ambiente.items()], "",
        "## Medições", "",
        "| Execução | Tokens | Carregar modelo (s) | 1º token (s) | Tokens/s | Tempo total (s) |", "|---|---|---|---|---|---|",
    ]
    for e in execucoes:
        m = e.get("metricas") or {}
        linhas.append(f"| {e['rotulo']} | {m.get('tokens_gerados', '—')} | {m.get('tempo_carga_s', '—')} | {m.get('tempo_primeiro_token_s', '—')} "
                      f"| {m.get('tokens_por_s', '—')} | {e['tempo_total_s']} |")
    linhas += ["", "## Respostas obtidas", ""]
    for e in execucoes:
        linhas += [f"### {e['rotulo']}", f"- **Entrada:** {e['entrada']}", "", "```text", e["resposta"].strip(), "```", ""]
        for etapa in e.get("etapas", []):
            linhas.append(f"- etapa `{etapa['nome']}`: {etapa['tempo_segundos']} s" + (f", {etapa['tokens_gerados']} tokens" if etapa.get("tokens_gerados") else ""))
        linhas.append("")
    return "\n".join(linhas)
