from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Code"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture
def raiz(tmp_path):
    from dados import escrever_dados
    escrever_dados(tmp_path)
    return tmp_path


@pytest.fixture
def container(raiz):
    """Container real, com dados em pasta temporária, modelo simulado e sem rede."""
    from dengue.adapters.outbound.infodengue import InfoDengueAmostraCsv
    from dengue.adapters.outbound.llm_fake import ModeloFake
    from dengue.config import Configuracoes
    from dengue.container import Container
    from fakes import ColetorFalso

    return Container(Configuracoes(raiz=raiz), modelo=ModeloFake(), coletor=ColetorFalso(),
                     fonte_infodengue=InfoDengueAmostraCsv(raiz / "Data" / "Raw" / "infodengue_sample.csv"))
