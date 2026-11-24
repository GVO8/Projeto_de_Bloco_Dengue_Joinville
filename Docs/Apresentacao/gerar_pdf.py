"""
Gera a apresentação do TP5 em Markdown e em PDF a partir de `conteudo.py` (fonte única).

    python Docs/Apresentacao/gerar_pdf.py --nome "Seu Nome" --saida nome_sobrenome_PB_TP5.pdf
    python Docs/Apresentacao/gerar_pdf.py --somente-md       # só atualiza argumentacao.md

Requer: pip install reportlab   (já em requirements-dev.txt). Prints: Docs/Apresentacao/prints/*.png
"""

from __future__ import annotations

import argparse
import html
import os
import re
from pathlib import Path

import conteudo

PASTA = Path(__file__).resolve().parent
PRINTS = PASTA / "prints"


# --------------------------------------------------------------------------- Markdown
def para_markdown(blocos: list[tuple]) -> str:
    saida: list[str] = []
    for b in blocos:
        tipo = b[0]
        if tipo == "title":
            saida.append(f"# {b[1]}\n")
        elif tipo == "subtitle":
            saida.append(f"**{b[1]}**\n")
        elif tipo == "meta":
            saida.append("\n".join(f"- **{k}:** {v}" for k, v in b[1]) + "\n")
        elif tipo == "h1":
            saida.append(f"## {b[1]}\n")
        elif tipo == "h2":
            saida.append(f"### {b[1]}\n")
        elif tipo == "p":
            saida.append(b[1] + "\n")
        elif tipo == "nota":
            saida.append("> " + b[1].replace("\n", "\n> ") + "\n")
        elif tipo == "ul":
            saida.append("\n".join(f"- {i}" for i in b[1]) + "\n")
        elif tipo == "ol":
            saida.append("\n".join(f"{n}. {i}" for n, i in enumerate(b[1], 1)) + "\n")
        elif tipo == "code":
            saida.append(f"```text\n{b[1]}\n```\n")
        elif tipo == "table":
            cab, linhas = b[1], b[2]
            esc = lambda t: str(t).replace("|", "\\|").replace("\n", " ")
            saida.append("| " + " | ".join(cab) + " |\n|" + "---|" * len(cab) + "\n" + "\n".join("| " + " | ".join(esc(c) for c in l) + " |" for l in linhas) + "\n")
        elif tipo == "print":
            arquivo = PRINTS / b[2]
            saida.append(f"![{b[1]}](prints/{b[2]})\n" if arquivo.exists() else f"> 🖼️ **INSERIR PRINT:** {b[1]} (`prints/{b[2]}`). {b[3]}\n")
        elif tipo == "pagebreak":
            saida.append("---\n")
    return "\n".join(saida)


# ------------------------------------------------------------------------------- PDF
def _fontes():
    import matplotlib
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    pasta = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
    for nome, arq in (("Corpo", "DejaVuSans.ttf"), ("Corpo-B", "DejaVuSans-Bold.ttf"), ("Corpo-I", "DejaVuSans-Oblique.ttf"),
                      ("Corpo-BI", "DejaVuSans-BoldOblique.ttf"), ("Mono", "DejaVuSansMono.ttf")):
        pdfmetrics.registerFont(TTFont(nome, str(pasta / arq)))
    pdfmetrics.registerFontFamily("Corpo", normal="Corpo", bold="Corpo-B", italic="Corpo-I", boldItalic="Corpo-BI")


def _inline(texto: str) -> str:
    t = html.escape(str(texto), quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r'<font name="Mono" size="8">\1</font>', t)
    t = re.sub(r"(?<![\w*])\*(.+?)\*(?![\w*])", r"<i>\1</i>", t)
    return t


def para_pdf(blocos: list[tuple], destino: Path, nome: str) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)

    _fontes()
    azul, cinza = colors.HexColor("#1f4e79"), colors.HexColor("#f2f5f9")
    est = {
        "corpo": ParagraphStyle("corpo", fontName="Corpo", fontSize=9.5, leading=13.5, alignment=TA_LEFT, spaceAfter=5),
        "celula": ParagraphStyle("celula", fontName="Corpo", fontSize=8.3, leading=11),
        "cab": ParagraphStyle("cab", fontName="Corpo-B", fontSize=8.5, leading=11, textColor=colors.white),
        "title": ParagraphStyle("title", fontName="Corpo-B", fontSize=21, leading=26, textColor=azul, spaceAfter=6),
        "subtitle": ParagraphStyle("subtitle", fontName="Corpo", fontSize=11, leading=15, textColor=colors.HexColor("#555555"), spaceAfter=10),
        "h1": ParagraphStyle("h1", fontName="Corpo-B", fontSize=14, leading=18, textColor=azul, spaceBefore=12, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName="Corpo-B", fontSize=11, leading=15, textColor=colors.HexColor("#2e75b6"), spaceBefore=8, spaceAfter=4),
        "nota": ParagraphStyle("nota", fontName="Corpo", fontSize=9.3, leading=13, backColor=colors.HexColor("#eaf2fb"), borderPadding=(6, 8, 6, 8),
                               borderColor=colors.HexColor("#9dc3e6"), borderWidth=0.6, spaceBefore=6, spaceAfter=10, leftIndent=6, rightIndent=6),
    }
    largura = A4[0] - 4 * cm
    historia: list = []

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Corpo", 7.5)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(2 * cm, 1.2 * cm, f"{nome} · Projeto de Bloco · TP5")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
        canvas.restoreState()

    for b in blocos:
        tipo = b[0]
        if tipo in ("title", "subtitle", "h1", "h2", "p"):
            historia.append(Paragraph(_inline(b[1]), est["corpo" if tipo == "p" else tipo]))
        elif tipo == "nota":
            historia.append(Paragraph(_inline(b[1]).replace("\n", "<br/>"), est["nota"]))
        elif tipo == "meta":
            t = Table([[Paragraph(f"<b>{html.escape(k)}</b>", est["celula"]), Paragraph(_inline(v), est["celula"])] for k, v in b[1]],
                      colWidths=[3.2 * cm, largura - 3.2 * cm])
            t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey)]))
            historia += [t, Spacer(1, 8)]
        elif tipo in ("ul", "ol"):
            itens = [ListItem(Paragraph(_inline(i), est["corpo"]), leftIndent=14) for i in b[1]]
            historia.append(ListFlowable(itens, bulletType="1" if tipo == "ol" else "bullet", bulletFontName="Corpo", bulletFontSize=9,
                                         leftIndent=14, start=1 if tipo == "ol" else "•"))
            historia.append(Spacer(1, 4))
        elif tipo == "code":
            historia.append(Preformatted(b[1], ParagraphStyle("code", fontName="Mono", fontSize=6.6, leading=8.5, backColor=cinza,
                                                              borderPadding=5, spaceAfter=8, leftIndent=4)))
        elif tipo == "table":
            cab, linhas, pesos = b[1], b[2], b[3]
            larguras = [largura * p / 100 for p in pesos]
            dados = [[Paragraph(_inline(c), est["cab"]) for c in cab]] + [[Paragraph(_inline(c), est["celula"]) for c in l] for l in linhas]
            t = Table(dados, colWidths=larguras, repeatRows=1)
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), azul), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, cinza]), ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                                   ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
            historia += [t, Spacer(1, 8)]
        elif tipo == "print":
            _, rotulo, arquivo, instrucao = b
            caminho = PRINTS / arquivo
            if caminho.exists():
                from reportlab.lib.utils import ImageReader
                w, h = ImageReader(str(caminho)).getSize()
                escala = min(largura / w, 11 * cm / h)
                historia.append(KeepTogether([Image(str(caminho), width=w * escala, height=h * escala),
                                              Paragraph(f"<i>{html.escape(rotulo)}</i>", est["celula"]), Spacer(1, 8)]))
            else:
                caixa = Table([[Paragraph(f"<b>INSERIR PRINT:</b> {_inline(rotulo)}<br/><font size='7.5'>{_inline(instrucao)}<br/>"
                                          f"Arquivo esperado: prints/{html.escape(arquivo)}</font>", est["celula"])]], colWidths=[largura], rowHeights=[2.6 * cm])
                caixa.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#c0504d")), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdf1f0")),
                                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
                historia += [caixa, Spacer(1, 8)]
        elif tipo == "pagebreak":
            historia.append(PageBreak())

    doc = SimpleDocTemplate(str(destino), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=2 * cm,
                            title="Dengue em Joinville — TP5", author=nome)
    doc.build(historia, onFirstPage=rodape, onLaterPages=rodape)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--nome", default="[Seu nome]")
    p.add_argument("--saida", default=str(PASTA / "TP5_apresentacao.pdf"))
    p.add_argument("--somente-md", action="store_true")
    args = p.parse_args()
    blocos = conteudo.construir(args.nome)
    (PASTA / "argumentacao.md").write_text(para_markdown(blocos), encoding="utf-8")
    print(f"✔ {PASTA / 'argumentacao.md'}")
    if not args.somente_md:
        para_pdf(blocos, Path(args.saida), args.nome)
        print(f"✔ {args.saida}")


if __name__ == "__main__":
    main()
