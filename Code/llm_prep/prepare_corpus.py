"""
Prepara os dados coletados para uso futuro com LLMs (TP3).

Gera em Data/Processed/:
- noticias_corpus.jsonl    -> uma linha por trecho (chunk) de notícia, com metadados
- contexto_infodengue.json -> resumo numérico compacto da série do InfoDengue

Uso:
    python Code/llm_prep/prepare_corpus.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "utils"))
import data_ops  # noqa: E402

MAX_CHARS = 800  # tamanho máximo de um trecho (cabe folgado em qualquer janela de contexto)


def dividir_em_trechos(paragrafos: list[str], max_chars: int = MAX_CHARS) -> list[str]:
    trechos, atual = [], ""
    for p in paragrafos:
        if atual and len(atual) + len(p) + 1 > max_chars:
            trechos.append(atual)
            atual = ""
        atual = f"{atual}\n{p}".strip()
    if atual:
        trechos.append(atual)
    return trechos


def ler_artigos_txt(path: Path) -> dict[str, list[str]]:
    """Lê o TXT do scraper ('### título' seguido dos parágrafos)."""
    artigos, titulo = {}, None
    for linha in path.read_text(encoding="utf-8").splitlines():
        if linha.startswith("### "):
            titulo = linha[4:].strip()
            artigos[titulo] = []
        elif titulo and linha.strip():
            artigos[titulo].append(linha.strip())
    return artigos


def gerar_corpus() -> int:
    df = data_ops.carregar_noticias()
    artigos = ler_artigos_txt(data_ops.NEWS_TXT)
    data_ops.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    saida = data_ops.DATA_PROCESSED / "noticias_corpus.jsonl"
    n = 0
    with open(saida, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            for i, trecho in enumerate(dividir_em_trechos(artigos.get(row["titulo"], []))):
                f.write(json.dumps({
                    "id_noticia": int(row["id"]),
                    "chunk_id": i,
                    "titulo": row["titulo"],
                    "data_publicacao": row.get("data_publicacao"),
                    "url": row.get("url"),
                    "texto": trecho,
                }, ensure_ascii=False) + "\n")
                n += 1
    return n


def gerar_contexto_infodengue() -> dict:
    base, origem = data_ops.carregar_base()
    df = data_ops.dados_completos(base)
    ctx = {
        "municipio": "Joinville/SC (geocode 4209102)",
        "origem_dados": origem,
        "semanas": int(len(df)),
        "semanas_por_nivel": {str(k): int(v) for k, v in df["nivel"].value_counts().sort_index().items()},
    }
    if "casos" in df.columns:
        pico = df.loc[df["casos"].idxmax()]
        ctx["casos_total"] = int(df["casos"].sum())
        ctx["semana_pico"] = {"SE": int(pico["SE"]), "casos": int(pico["casos"])}
    (data_ops.DATA_PROCESSED / "contexto_infodengue.json").write_text(
        json.dumps(ctx, ensure_ascii=False, indent=2), encoding="utf-8")
    return ctx


if __name__ == "__main__":
    print(f"Trechos gerados: {gerar_corpus()}")
    print(json.dumps(gerar_contexto_infodengue(), ensure_ascii=False, indent=2))
