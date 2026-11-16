"""Repositório de notícias em CSV (metadados) + TXT (corpo), e armazenamento do corpus (JSONL + JSON)."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from dengue.core.domain.modelos import ArtigoColetado, ContextoNumerico, Noticia, NoticiaCompleta, TrechoCorpus
from dengue.core.ports.repositorios import ArmazenamentoCorpus, RepositorioNoticias


def _txt(valor) -> str | None:
    return None if pd.isna(valor) else str(valor)


def ler_artigos_txt(caminho: Path) -> dict[str, list[str]]:
    """Lê o TXT do scraper ('### título' seguido dos parágrafos)."""
    artigos: dict[str, list[str]] = {}
    titulo = None
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if linha.startswith("### "):
            titulo = linha[4:].strip()
            artigos[titulo] = []
        elif titulo and linha.strip():
            artigos[titulo].append(linha.strip())
    return artigos


class NoticiasCsvTxt(RepositorioNoticias):
    def __init__(self, csv_path: Path, txt_path: Path):
        self._csv, self._txt = csv_path, txt_path

    def _todas(self) -> list[Noticia]:
        if not self._csv.exists():
            return []
        df = pd.read_csv(self._csv)
        return [
            Noticia(int(r["id"]), str(r["titulo"]), _txt(r.get("data_publicacao")), _txt(r.get("autor")),
                    _txt(r.get("url")), _txt(r.get("resumo")))
            for _, r in df.iterrows()
        ]

    def listar(self, busca: str | None = None, limite: int | None = None) -> list[Noticia]:
        itens = self._todas()
        if busca:
            itens = [n for n in itens if busca.lower() in n.titulo.lower()]
        return itens[:limite] if limite else itens

    def obter(self, noticia_id: int) -> Noticia | None:
        return next((n for n in self._todas() if n.id == noticia_id), None)

    def paragrafos(self, noticia_id: int) -> list[str]:
        noticia = self.obter(noticia_id)
        if noticia is None or not self._txt.exists():
            return []
        return ler_artigos_txt(self._txt).get(noticia.titulo, [])

    def salvar(self, artigos: list[ArtigoColetado]) -> list[Noticia]:
        self._csv.parent.mkdir(parents=True, exist_ok=True)
        noticias = [Noticia(i, a.titulo, a.data_publicacao, a.autor, a.url, a.resumo) for i, a in enumerate(artigos, 1)]
        with open(self._csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["id", "titulo", "data_publicacao", "autor", "url", "resumo"])
            w.writeheader()
            for n in noticias:
                w.writerow(asdict(n))
        with open(self._txt, "w", encoding="utf-8") as f:
            for a in artigos:
                f.write(f"### {a.titulo}\n{a.corpo}\n\n")
        return noticias


class CorpusJsonl(ArmazenamentoCorpus):
    def __init__(self, jsonl_path: Path, contexto_path: Path):
        self._jsonl, self._contexto = jsonl_path, contexto_path

    def existe(self) -> bool:
        return self._jsonl.exists() and self._contexto.exists()

    def salvar(self, trechos: list[TrechoCorpus], contexto: ContextoNumerico) -> None:
        self._jsonl.parent.mkdir(parents=True, exist_ok=True)
        with open(self._jsonl, "w", encoding="utf-8") as f:
            for t in trechos:
                f.write(json.dumps(asdict(t), ensure_ascii=False) + "\n")
        self._contexto.write_text(json.dumps(contexto.como_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def _trechos(self) -> list[dict]:
        if not self._jsonl.exists():
            return []
        return [json.loads(l) for l in self._jsonl.read_text(encoding="utf-8").splitlines() if l.strip()]

    def obter_noticia(self, noticia_id: int) -> NoticiaCompleta | None:
        trechos = sorted((t for t in self._trechos() if t["id_noticia"] == noticia_id), key=lambda t: t["chunk_id"])
        if not trechos:
            return None

        def meta(campo):  # primeiro valor preenchido entre os trechos (todos repetem os metadados)
            return next((t[campo] for t in trechos if t.get(campo)), None)

        return NoticiaCompleta(
            id=noticia_id, titulo=trechos[0]["titulo"], texto="\n".join(t["texto"] for t in trechos),
            data_publicacao=meta("data_publicacao"), autor=meta("autor"), url=meta("url"), resumo=meta("resumo"),
        )

    def listar_titulos(self, limite: int = 5) -> list[str]:
        vistos: list[str] = []
        for t in self._trechos():
            if t["titulo"] not in vistos:
                vistos.append(t["titulo"])
        return vistos[:limite]

    def obter_contexto(self) -> ContextoNumerico:
        return ContextoNumerico.de_dict(json.loads(self._contexto.read_text(encoding="utf-8")))
