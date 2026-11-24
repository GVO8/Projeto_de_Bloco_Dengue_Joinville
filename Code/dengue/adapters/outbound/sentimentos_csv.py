"""Resultados da análise de sentimento das notícias, em CSV (Data/Processed)."""

from __future__ import annotations

import csv
from dataclasses import asdict, fields
from pathlib import Path

from dengue.core.domain.modelos import SentimentoNoticia
from dengue.core.ports.repositorios import RepositorioSentimentos

_CAMPOS = [f.name for f in fields(SentimentoNoticia)]


class SentimentosCsv(RepositorioSentimentos):
    def __init__(self, caminho: Path):
        self._caminho = caminho

    def listar(self) -> list[SentimentoNoticia]:
        if not self._caminho.exists():
            return []
        with open(self._caminho, newline="", encoding="utf-8") as f:
            linhas = [
                SentimentoNoticia(
                    noticia_id=int(r["noticia_id"]), titulo=r["titulo"], classe=r["classe"], justificativa=r["justificativa"],
                    modelo=r["modelo"], tempo_segundos=float(r["tempo_segundos"] or 0), analisado_em=r["analisado_em"],
                    data_publicacao=r.get("data_publicacao") or None,
                )
                for r in csv.DictReader(f)
            ]
        return sorted(linhas, key=lambda s: s.noticia_id)

    def salvar(self, sentimento: SentimentoNoticia) -> None:
        todos = {s.noticia_id: s for s in self.listar()}
        todos[sentimento.noticia_id] = sentimento
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(self._caminho, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=_CAMPOS)
            w.writeheader()
            for s in sorted(todos.values(), key=lambda s: s.noticia_id):
                w.writerow(asdict(s))
