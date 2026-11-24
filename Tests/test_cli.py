"""CLI: sentimentos em lote e medição real do modelo (com o Llama substituído por um falso)."""
import pytest

import cli
from dengue.adapters.outbound.llm_fake import ModeloFake
from dengue.adapters.outbound.llm_llamacpp import ModeloLlamaCpp
from dengue.adapters.inbound.evidencia import coletar_ambiente, renderizar_markdown
from dengue.config import ConfigLlm, Configuracoes
from dengue.container import Container

from fakes import ColetorFalso, ConsultaFalsa, modelo_chat


def llama_falso():
    class L:
        def __init__(self, **kw): pass
        def create_chat_completion(self, **kw):
            return iter({"choices": [{"delta": {"content": t}}]} for t in ("Resumo ", "da ", "notícia."))
    return L


@pytest.fixture
def container_real(raiz):
    """Container 'real' (backend llamacpp) mas com Llama falso: exercita o caminho de medição sem baixar o modelo."""
    arq = raiz / "Models" / "m.gguf"; arq.parent.mkdir(); arq.write_bytes(b"x" * 1000)
    llm = ConfigLlm(caminho_personalizado=arq, timeout_s=5)
    cfg = Configuracoes(raiz=raiz, llm=llm)
    return Container(cfg, modelo=ModeloLlamaCpp(llm, fabrica_llama=llama_falso), coletor=ColetorFalso(), consulta_infodengue=ConsultaFalsa(), ano_atual=lambda: 2026)


def test_status_e_gerar_corpus(container, capsys):
    assert cli.main(["status"], container_factory=lambda: container) == 0 and "Backend: fake" in capsys.readouterr().out
    assert cli.main(["gerar-corpus"], container_factory=lambda: container) == 0 and "2 notícias" in capsys.readouterr().out


def test_coletar_sem_resultados_da_erro_amigavel(container, capsys):
    assert cli.main(["coletar-noticias"], container_factory=lambda: container) == 1
    assert "→" in capsys.readouterr().err


def test_analisar_sentimentos_grava_csv_e_e_idempotente(container, capsys):
    container.processar_noticia._modelo = ModeloFake("NEUTRO. ok")
    assert cli.main(["analisar-sentimentos"], container_factory=lambda: container) == 0
    assert "2 analisadas" in capsys.readouterr().out and len(container.sentimentos.listar()) == 2
    cli.main(["analisar-sentimentos"], container_factory=lambda: container)
    assert "0 analisadas · 2 já analisadas" in capsys.readouterr().out
    cli.main(["analisar-sentimentos", "--todas"], container_factory=lambda: container)
    assert "2 analisadas" in capsys.readouterr().out


def test_analisar_sentimentos_sem_modelo_orienta(raiz, capsys):
    cfg = Configuracoes(raiz=raiz, llm=ConfigLlm(caminho_personalizado=raiz / "nao_existe.gguf"))
    c = Container(cfg, modelo=ModeloLlamaCpp(cfg.llm), coletor=ColetorFalso(), consulta_infodengue=ConsultaFalsa())
    assert cli.main(["analisar-sentimentos"], container_factory=lambda: c) == 1
    assert "baixar-modelo" in capsys.readouterr().err


def test_medir_modelo_recusa_o_backend_simulado_para_nao_gerar_falsa_evidencia(raiz, capsys):
    cfg = Configuracoes.do_ambiente({"DENGUE_LLM_BACKEND": "fake"}, raiz=raiz)
    c = Container(cfg, coletor=ColetorFalso(), consulta_infodengue=ConsultaFalsa())
    assert cli.main(["medir-modelo"], container_factory=lambda: c) == 1
    assert "simulado" in capsys.readouterr().err and not (raiz / "Docs" / "Evidencias").exists()


def test_medir_modelo_gera_o_arquivo_de_evidencia_com_tempos_e_resposta(container_real, capsys):
    assert cli.main(["medir-modelo", "--hardware", "i7-7500U, 24 GB, 4 GB VRAM"], container_factory=lambda: container_real) == 0
    (arq,) = list((container_real.config.raiz / "Docs" / "Evidencias").glob("medicao_*.md"))
    md = arq.read_text(encoding="utf-8")
    assert "i7-7500U, 24 GB, 4 GB VRAM" in md and "1ª execução (inclui carregar o modelo)" in md and "2ª execução (modelo já na memória)" in md
    assert "Resumo da notícia." in md and "Tokens/s" in md and "medidos nesta máquina" in md and "m.gguf" in md
    assert "Evidência salva em" in capsys.readouterr().out


def test_medir_modelo_com_pergunta_mede_tambem_a_conversa(container_real):
    container_real.conversar._modelo = modelo_chat()
    assert cli.main(["medir-modelo", "--pergunta", "Qual foi o ano com mais casos de dengue?"], container_factory=lambda: container_real) == 0
    md = next((container_real.config.raiz / "Docs" / "Evidencias").glob("medicao_*.md")).read_text(encoding="utf-8")
    assert "Conversa com os dados" in md and "etapa `planejamento`" in md and "etapa `consulta_infodengue`" in md


def test_medir_modelo_sem_noticias_orienta(container_real, capsys):
    container_real.repo_noticias.salvar([])
    assert cli.main(["medir-modelo"], container_factory=lambda: container_real) == 1
    assert "coletar-noticias" in capsys.readouterr().err


def test_evidencia_ambiente_e_markdown(raiz):
    cfg = Configuracoes(raiz=raiz, llm=ConfigLlm(caminho_personalizado=raiz / "nao_existe.gguf"))
    amb = coletar_ambiente(cfg)
    assert amb["Hardware informado"].startswith("(não informado") and "arquivo não encontrado" in amb["Modelo"] and amb["Threads lógicas"]
    md = renderizar_markdown(amb, [{"rotulo": "R", "entrada": "E", "resposta": "x", "metricas": None, "tempo_total_s": 1.0}])
    assert "| R | — | — | — | — | 1.0 |" in md
