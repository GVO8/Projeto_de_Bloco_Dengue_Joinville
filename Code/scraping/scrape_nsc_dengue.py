"""
Scraper de notícias do NSC Total — Joinville + Dengue (TP2)

Este script é executado SEPARADAMENTE do app Streamlit (conforme pedido no
enunciado). Ele varre a página de tag "dengue" do NSC Total
(https://www.nsctotal.com.br/tag/dengue), que já filtra por dengue, e
seleciona apenas as notícias cujo título também contenha "Joinville".

Para cada notícia encontrada, o script visita a página do artigo e extrai
metadados confiáveis a partir das meta tags (título, data de publicação,
autor, resumo) e o corpo do texto (parágrafos), salvando:

- Data/Raw/nsc_noticias_joinville_dengue.csv  → metadados tabulares
- Data/Raw/nsc_noticias_texto.txt             → corpus de texto completo
                                                 (usado depois para nuvem de
                                                 palavras no app Streamlit)

Uso:
    python Code/scraping/scrape_nsc_dengue.py [--max-paginas 3] [--min-artigos 15]

Observação: este script depende de acesso à internet (nsctotal.com.br).
Execute-o localmente antes de rodar o app Streamlit.
"""

import argparse
import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.nsctotal.com.br"
TAG_URL = f"{BASE_URL}/tag/dengue"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DengueESG-TP2-Scraper/1.0; "
        "+educational-project)"
    )
}
REQUEST_DELAY_SECONDS = 1.0  # boa prática: não sobrecarregar o site

ROOT_DIR = Path(__file__).resolve().parents[2]
OUT_CSV = ROOT_DIR / "Data" / "Raw" / "nsc_noticias_joinville_dengue.csv"
OUT_TXT = ROOT_DIR / "Data" / "Raw" / "nsc_noticias_texto.txt"


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def listar_candidatos(max_paginas: int) -> list[dict]:
    """
    Varre a(s) página(s) de listagem da tag 'dengue' e retorna candidatos
    (título + link) cujo título contenha 'joinville'.

    A extração usa os títulos das notícias, que no NSC Total aparecem como
    cabeçalhos <h2> contendo um link para o artigo — um padrão estável no
    tema do site, independente de nomes de classes CSS específicos.
    """
    candidatos = []
    vistos = set()

    for pagina in range(1, max_paginas + 1):
        url = TAG_URL if pagina == 1 else f"{TAG_URL}/page/{pagina}"
        try:
            soup = get_soup(url)
        except requests.RequestException as exc:
            print(f"  Aviso: falha ao acessar {url}: {exc}")
            break

        headlines = soup.find_all(["h2", "h3"])
        encontrados_na_pagina = 0

        for h in headlines:
            a = h.find("a", href=True)
            if not a:
                continue
            titulo = a.get_text(strip=True)
            link = urljoin(BASE_URL, a["href"])

            if link in vistos:
                continue
            if "joinville" not in titulo.lower():
                continue

            vistos.add(link)
            candidatos.append({"titulo": titulo, "url": link})
            encontrados_na_pagina += 1

        print(f"  Página {pagina}: {encontrados_na_pagina} candidato(s) Joinville+Dengue")
        time.sleep(REQUEST_DELAY_SECONDS)

        if encontrados_na_pagina == 0 and pagina > 1:
            # heurística simples: se páginas seguidas não trazem nada novo,
            # provavelmente já passamos do conteúdo relevante recente
            continue

    return candidatos


def extrair_artigo(url: str) -> dict | None:
    """Extrai metadados e corpo de texto de uma notícia via meta tags e <p>."""
    try:
        soup = get_soup(url)
    except requests.RequestException as exc:
        print(f"  Aviso: falha ao acessar artigo {url}: {exc}")
        return None

    def meta(name: str) -> str:
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        return tag["content"].strip() if tag and tag.get("content") else ""

    titulo = meta("og:title") or (soup.title.get_text(strip=True) if soup.title else "")
    resumo = meta("og:description") or meta("description")
    data_pub = meta("article:published_time")  # ISO 8601, ex: 2026-01-09T23:02:31+00:00

    autor_tag = soup.find("a", href=re.compile(r"/autor/"))
    autor = autor_tag.get_text(strip=True) if autor_tag else ""

    # Corpo do texto: parágrafos dentro do conteúdo do artigo, ignorando
    # legendas de imagem (geralmente em <em>/<i> isolados) e textos muito
    # curtos (menus, botões de compartilhamento etc.)
    paragrafos = []
    for p in soup.find_all("p"):
        texto = p.get_text(" ", strip=True)
        if len(texto) > 40 and "compartilhe" not in texto.lower():
            paragrafos.append(texto)
    corpo = "\n".join(paragrafos)

    return {
        "titulo": titulo,
        "url": url,
        "data_publicacao": data_pub,
        "autor": autor,
        "resumo": resumo,
        "corpo": corpo,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-paginas", type=int, default=3, help="Nº de páginas da tag 'dengue' a varrer")
    args = parser.parse_args()

    print(f"Buscando notícias em {TAG_URL} (Joinville + Dengue)...")
    candidatos = listar_candidatos(args.max_paginas)
    print(f"Total de candidatos encontrados: {len(candidatos)}")

    artigos = []
    for i, cand in enumerate(candidatos, start=1):
        print(f"  [{i}/{len(candidatos)}] Extraindo: {cand['titulo'][:70]}...")
        artigo = extrair_artigo(cand["url"])
        if artigo:
            artigos.append(artigo)
        time.sleep(REQUEST_DELAY_SECONDS)

    if not artigos:
        print("Nenhum artigo extraído. Verifique a conexão ou a estrutura do site.")
        return

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # CSV de metadados (id sequencial + campos tabulares, sem o corpo longo)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "titulo", "data_publicacao", "autor", "url", "resumo"]
        )
        writer.writeheader()
        for i, art in enumerate(artigos, start=1):
            writer.writerow(
                {
                    "id": i,
                    "titulo": art["titulo"],
                    "data_publicacao": art["data_publicacao"],
                    "autor": art["autor"],
                    "url": art["url"],
                    "resumo": art["resumo"],
                }
            )
    print(f"CSV salvo em: {OUT_CSV}")

    # TXT com o corpo de todas as notícias, para nuvem de palavras
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        for art in artigos:
            f.write(f"### {art['titulo']}\n")
            f.write(art["corpo"])
            f.write("\n\n")
    print(f"TXT salvo em: {OUT_TXT}")


if __name__ == "__main__":
    main()
