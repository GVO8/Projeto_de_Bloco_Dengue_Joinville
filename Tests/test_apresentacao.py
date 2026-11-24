"""Gerador da apresentação do TP5 (Markdown + PDF a partir de uma fonte única)."""
import sys
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parents[1] / "Docs" / "Apresentacao"
sys.path.insert(0, str(PASTA))

import conteudo  # noqa: E402
import gerar_pdf  # noqa: E402


@pytest.fixture
def blocos():
    return conteudo.construir("Aluno de Teste", ano_atual=2026)


def titulos(blocos, tipo="h1"):
    return [b[1] for b in blocos if b[0] == tipo]


def test_conteudo_cobre_o_que_a_tarefa_4_pede(blocos):
    t = " ".join(titulos(blocos))
    for trecho in ("problema de negócio", "ESG", "ciclo completo", "solução", "dashboard", "IA", "Limitações", "checklist"):
        assert trecho.lower() in t.lower()
    meta = dict(next(b for b in blocos if b[0] == "meta")[1])
    assert meta["Autor"] == "Aluno de Teste" and meta["Repositório"] == conteudo.REPO_URL and "Opção 1" in meta["Caminho escolhido"]


def test_tabela_de_consultas_vem_do_codigo_e_bate_com_as_perguntas_modelo(blocos):
    tabela = next(b for b in blocos if b[0] == "table" and b[1][0] == "Pergunta" and b[1][1] == "Intenção")
    assert [(l[1], l[2]) for l in tabela[2]] == [("pico", "2026 a 2026"), ("ano_mais_casos", "2017 a 2026"),
                                                 ("ano_menos_casos", "2017 a 2026"), ("comparar_anos", "2025 a 2026")]
    assert any("geocode=4209102" in b[1] and "ey_start=2025" in b[1] for b in blocos if b[0] == "code")


def test_nao_inventa_resultados_e_marca_as_pendencias(blocos):
    md = gerar_pdf.para_markdown(blocos)
    assert "não traz números de casos nem respostas da IA inventados" in md
    assert md.count("INSERIR PRINT") == 4 and "Pendente" in md and "_____" in md


def test_markdown_versionado_tem_todas_as_secoes_do_conteudo():
    md = (PASTA / "argumentacao.md").read_text(encoding="utf-8")
    for h in titulos(conteudo.construir("x", ano_atual=2026)):
        assert h in md


def test_pdf_e_gerado_com_nome_acentos_e_paginas(tmp_path, blocos):
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")
    destino = tmp_path / "tp5.pdf"
    gerar_pdf.para_pdf(blocos, destino, "Aluno de Teste")
    leitor = pypdf.PdfReader(str(destino))
    texto = "\n".join(p.extract_text() for p in leitor.pages)
    assert len(leitor.pages) >= 5 and "Aluno de Teste" in texto and "preocupação" in texto and "Página 1" in texto
    assert "ey_start=2017" in texto


def test_print_colocado_na_pasta_entra_no_pdf_e_no_markdown(tmp_path, monkeypatch, blocos):
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")
    PIL = pytest.importorskip("PIL.Image")
    pasta = tmp_path / "prints"; pasta.mkdir()
    PIL.new("RGB", (800, 400), "blue").save(pasta / "dashboard.png")
    monkeypatch.setattr(gerar_pdf, "PRINTS", pasta)
    md = gerar_pdf.para_markdown(blocos)
    assert "![Dashboard completo](prints/dashboard.png)" in md and md.count("INSERIR PRINT") == 3
    destino = tmp_path / "tp5.pdf"
    gerar_pdf.para_pdf(blocos, destino, "x")
    assert "INSERIR PRINT: Dashboard completo" not in "\n".join(p.extract_text() for p in pypdf.PdfReader(str(destino)).pages)
