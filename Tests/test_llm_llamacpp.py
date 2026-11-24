"""Adaptador do modelo real, com a classe Llama substituída por um falso (nenhum modelo é baixado)."""
import threading

import pytest

from dengue.adapters.outbound.llm_fake import ModeloFake, resposta_simulada
from dengue.adapters.outbound.llm_llamacpp import ModeloLlamaCpp
from dengue.adapters.outbound.modelo_download import baixar_modelo
from dengue.config import ConfigLlm
from dengue.core.domain.erros import (
    ErroDeIA, ModeloFalhaError, ModeloIndisponivelError, ModeloOcupadoError, ModeloTimeoutError, RespostaVaziaError,
)


def fabrica(tokens=("Olá", ", ", "mundo"), erro_init=None, erro_geracao=None):
    class LlamaFalso:
        instancias = []

        def __init__(self, **kw):
            if erro_init: raise erro_init
            self.kw, self.chamadas, self.fechado = kw, [], False
            LlamaFalso.instancias.append(self)

        def create_chat_completion(self, **kw):
            self.chamadas.append(kw)
            if erro_geracao: raise erro_geracao
            def gerador():
                for t in tokens:
                    yield {"choices": [{"delta": {"content": t}}]}
            return gerador()
    return LlamaFalso, (lambda: LlamaFalso)


@pytest.fixture
def modelo_arquivo(tmp_path):
    arq = tmp_path / "m.gguf"
    arq.write_bytes(b"x")
    return ConfigLlm(caminho_personalizado=arq, timeout_s=5, n_ctx=2048, n_threads=3, n_gpu_layers=7)


def test_gera_texto_carrega_sob_demanda_e_repassa_parametros(modelo_arquivo):
    Llama, f = fabrica()
    m = ModeloLlamaCpp(modelo_arquivo, fabrica_llama=f)
    assert m.estado().pronto and not m.estado().carregado and not Llama.instancias   # nada carregado ainda
    assert m.gerar("pergunta", max_tokens=99) == "Olá, mundo"
    inst = Llama.instancias[0]
    assert inst.kw["n_ctx"] == 2048 and inst.kw["n_threads"] == 3 and inst.kw["n_gpu_layers"] == 7
    ch = inst.chamadas[0]
    assert ch["max_tokens"] == 99 and ch["stream"] is True and ch["messages"] == [{"role": "user", "content": "pergunta"}]
    assert ch["temperature"] == 0.2 and m.estado().carregado
    m.gerar("outra", max_tokens=5)
    assert len(Llama.instancias) == 1                                               # não recarrega


def test_arquivo_ausente_nao_tenta_carregar_e_orienta(tmp_path):
    m = ModeloLlamaCpp(ConfigLlm(caminho_personalizado=tmp_path / "nao_existe.gguf"), fabrica_llama=fabrica()[1])
    assert not m.estado().pronto and "não encontrado" in m.estado().detalhe
    with pytest.raises(ModeloIndisponivelError) as e:
        m.gerar("x", max_tokens=1)
    assert e.value.motivo == "arquivo_ausente" and "baixar-modelo" in e.value.sugestao and e.value.status_http == 503


def test_biblioteca_ausente_orienta_python_312(modelo_arquivo):
    def sem_lib(): raise ImportError("No module named 'llama_cpp'")
    with pytest.raises(ModeloIndisponivelError) as e:
        ModeloLlamaCpp(modelo_arquivo, fabrica_llama=sem_lib).gerar("x", max_tokens=1)
    assert e.value.motivo == "biblioteca" and "3.12" in e.value.sugestao and "IA" in e.value.mensagem


def test_falha_ao_carregar_modelo(modelo_arquivo):
    with pytest.raises(ModeloIndisponivelError) as e:
        ModeloLlamaCpp(modelo_arquivo, fabrica_llama=fabrica(erro_init=MemoryError("sem RAM"))[1]).gerar("x", max_tokens=1)
    assert e.value.motivo == "carga" and "sem RAM" in e.value.detalhe


def test_excecao_crua_na_inferencia_vira_erro_de_ia(modelo_arquivo):
    with pytest.raises(ModeloFalhaError) as e:
        ModeloLlamaCpp(modelo_arquivo, fabrica_llama=fabrica(erro_geracao=ValueError("contexto estourou"))[1]).gerar("x", max_tokens=1)
    assert isinstance(e.value, ErroDeIA) and "contexto estourou" in e.value.detalhe and e.value.status_http == 502


def test_resposta_vazia(modelo_arquivo):
    with pytest.raises(RespostaVaziaError):
        ModeloLlamaCpp(modelo_arquivo, fabrica_llama=fabrica(tokens=("  ", "\n"))[1]).gerar("x", max_tokens=1)


def test_timeout_interrompe_a_geracao_com_relogio_falso(modelo_arquivo):
    tempos = iter([0, 1, 2, 99, 100])
    m = ModeloLlamaCpp(ConfigLlm(caminho_personalizado=modelo_arquivo.caminho_personalizado, timeout_s=10),
                       fabrica_llama=fabrica(tokens=("a",) * 10)[1], relogio=lambda: next(tempos))
    with pytest.raises(ModeloTimeoutError) as e:
        m.gerar("x", max_tokens=5)
    assert e.value.status_http == 504 and "10 segundos" in e.value.mensagem


def test_chamada_concorrente_recebe_modelo_ocupado(modelo_arquivo):
    m = ModeloLlamaCpp(ConfigLlm(caminho_personalizado=modelo_arquivo.caminho_personalizado, timeout_s=0.05), fabrica_llama=fabrica()[1])
    m._lock.acquire()                                    # outra inferência em andamento
    try:
        with pytest.raises(ModeloOcupadoError) as e:
            m.gerar("x", max_tokens=1)
        assert e.value.status_http == 429
    finally:
        m._lock.release()
    assert m.gerar("x", max_tokens=1)                    # liberado, volta a funcionar


def test_inferencias_simultaneas_sao_serializadas(modelo_arquivo):
    ativos, pico = [0], [0]
    class Lento:
        def __init__(self, **kw): pass
        def create_chat_completion(self, **kw):
            ativos[0] += 1; pico[0] = max(pico[0], ativos[0])
            yield {"choices": [{"delta": {"content": "ok"}}]}
            ativos[0] -= 1
    m = ModeloLlamaCpp(modelo_arquivo, fabrica_llama=lambda: Lento)
    ts = [threading.Thread(target=m.gerar, args=("x",), kwargs={"max_tokens": 1}) for _ in range(5)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert pico[0] == 1


# ------------------------------------------------------------- FakeLLM
def test_fake_registra_chamadas_e_aceita_resposta_fixa_ou_funcao():
    assert ModeloFake("fixa").gerar("p", max_tokens=3) == "fixa"
    f = ModeloFake(lambda p: p.upper())
    assert f.gerar("abc", max_tokens=7) == "ABC" and f.chamadas == [{"prompt": "abc", "max_tokens": 7, "formato_json": False}]


def test_fake_padrao_marca_resposta_como_simulada():
    for prompt in ("Classifique o sentimento", "escreva um boletim", "Pergunta: x", "Resuma"):
        assert "simulada" in resposta_simulada(prompt)


def test_fake_pode_simular_falha_e_indisponibilidade():
    with pytest.raises(ModeloFalhaError):
        ModeloFake(erro=ModeloFalhaError()).gerar("x", max_tokens=1)
    assert not ModeloFake(pronto=False).estado().pronto


# ------------------------------------------------------------ download
def test_download_sem_biblioteca_ou_com_falha_de_rede(monkeypatch, tmp_path):
    import builtins, sys, types
    cfg = ConfigLlm(pasta_modelos=tmp_path / "Models")
    real = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", lambda n, *a, **k: (_ for _ in ()).throw(ImportError("x")) if n == "huggingface_hub" else real(n, *a, **k))
    with pytest.raises(ModeloIndisponivelError) as e:
        baixar_modelo(cfg)
    assert e.value.motivo == "download"
    monkeypatch.setattr(builtins, "__import__", real)
    falso = types.ModuleType("huggingface_hub")
    falso.hf_hub_download = lambda **kw: (_ for _ in ()).throw(ConnectionError("sem rede"))
    monkeypatch.setitem(sys.modules, "huggingface_hub", falso)
    with pytest.raises(ModeloIndisponivelError) as e:
        baixar_modelo(cfg)
    assert "sem rede" in e.value.detalhe
    falso.hf_hub_download = lambda **kw: str(tmp_path / "ok.gguf")
    assert baixar_modelo(cfg).name == "ok.gguf"
