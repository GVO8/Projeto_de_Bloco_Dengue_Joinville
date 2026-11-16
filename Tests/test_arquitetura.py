"""Teste de arquitetura: garante a regra de dependência da arquitetura hexagonal."""
import ast
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1] / "Code" / "dengue"
FRAMEWORKS = {"fastapi", "starlette", "uvicorn", "streamlit", "requests", "bs4", "llama_cpp", "huggingface_hub", "plotly", "wordcloud", "matplotlib"}


def importacoes(arquivo: Path) -> set[str]:
    nomes = set()
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.Import):
            nomes |= {a.name for a in no.names}
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            nomes.add(no.module)
    return nomes


def arquivos(pasta: str):
    return sorted((CODE / pasta).rglob("*.py"))


@pytest.mark.parametrize("arquivo", arquivos("core"), ids=lambda p: str(p.relative_to(CODE)))
def test_nucleo_nao_depende_de_adaptadores_nem_de_frameworks(arquivo):
    ruins = {i for i in importacoes(arquivo)
             if i.startswith(("dengue.adapters", "dengue.container", "dengue.config")) or i.split(".")[0] in FRAMEWORKS}
    assert not ruins, f"{arquivo.name} viola a regra de dependência: {ruins}"


@pytest.mark.parametrize("arquivo", arquivos("adapters/outbound"), ids=lambda p: p.name)
def test_adaptadores_de_saida_nao_conhecem_os_de_entrada_nem_o_container(arquivo):
    assert not {i for i in importacoes(arquivo) if i.startswith(("dengue.adapters.inbound", "dengue.container"))}


@pytest.mark.parametrize("arquivo", arquivos("adapters/inbound"), ids=lambda p: str(p.relative_to(CODE / "adapters/inbound")))
def test_adaptadores_de_entrada_so_chegam_as_implementacoes_pelo_container(arquivo):
    imps = importacoes(arquivo)
    assert not {i for i in imps if i.startswith("dengue.adapters.outbound")}
    if "api_fastapi" in arquivo.parts:
        assert not {i for i in imps if "ui_streamlit" in i or i.split(".")[0] == "streamlit"}
    if "ui_streamlit" in arquivo.parts:
        assert not {i for i in imps if "api_fastapi" in i or i.split(".")[0] in {"fastapi", "uvicorn"}}


def test_so_a_raiz_de_composicao_conhece_as_implementacoes():
    assert any(i.startswith("dengue.adapters.outbound") for i in importacoes(CODE / "container.py"))
