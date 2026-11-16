"""Coletor de notícias do NSC Total (BeautifulSoup). Parsing separado do I/O para ser testável."""

from __future__ import annotations

import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from dengue.core.domain.erros import ColetaError
from dengue.core.domain.modelos import ArtigoColetado
from dengue.core.ports.repositorios import ColetorNoticias

BASE_URL = "https://www.nsctotal.com.br"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DengueESG-Scraper/1.0; +educational-project)"}


def extrair_candidatos(html: str, base_url: str = BASE_URL, palavra: str = "joinville") -> list[tuple[str, str]]:
    """Cabeçalhos <h2>/<h3> com link cujo título contém a palavra (padrão estável do site)."""
    soup = BeautifulSoup(html, "html.parser")
    achados, vistos = [], set()
    for h in soup.find_all(["h2", "h3"]):
        a = h.find("a", href=True)
        if not a:
            continue
        titulo, link = a.get_text(strip=True), urljoin(base_url, a["href"])
        if link not in vistos and palavra in titulo.lower():
            vistos.add(link)
            achados.append((titulo, link))
    return achados


def extrair_artigo(html: str, url: str) -> ArtigoColetado:
    soup = BeautifulSoup(html, "html.parser")

    def meta(nome: str) -> str:
        tag = soup.find("meta", attrs={"property": nome}) or soup.find("meta", attrs={"name": nome})
        return tag["content"].strip() if tag and tag.get("content") else ""

    titulo = meta("og:title") or (soup.title.get_text(strip=True) if soup.title else "")
    autor_tag = soup.find("a", href=re.compile(r"/autor/"))
    paragrafos = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    corpo = "\n".join(p for p in paragrafos if len(p) > 40)
    return ArtigoColetado(
        titulo=titulo, url=url, data_publicacao=meta("article:published_time"),
        autor=autor_tag.get_text(strip=True) if autor_tag else "",
        resumo=meta("og:description") or meta("description"), corpo=corpo,
    )


class ColetorNscTotal(ColetorNoticias):
    def __init__(self, base_url: str = BASE_URL, pausa_s: float = 1.0, http=requests, dormir=time.sleep):
        self._base, self._pausa, self._http, self._dormir = base_url, pausa_s, http, dormir

    def _baixar(self, url: str) -> str:
        resp = self._http.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text

    def coletar(self, max_paginas: int) -> list[ArtigoColetado]:
        candidatos: list[tuple[str, str]] = []
        for pagina in range(1, max_paginas + 1):
            url = f"{self._base}/tag/dengue" + ("" if pagina == 1 else f"/page/{pagina}")
            try:
                candidatos += extrair_candidatos(self._baixar(url), self._base)
            except requests.RequestException as exc:
                if pagina == 1:
                    raise ColetaError(str(exc)) from exc
                break  # páginas seguintes são opcionais
            self._dormir(self._pausa)
        artigos = []
        for link in dict.fromkeys(l for _, l in candidatos):  # sem repetidos, mantendo a ordem
            try:
                artigos.append(extrair_artigo(self._baixar(link), link))
            except requests.RequestException:
                continue  # um artigo com falha não derruba a coleta toda
            self._dormir(self._pausa)
        return artigos
