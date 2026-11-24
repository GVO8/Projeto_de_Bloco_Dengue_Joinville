import threading

import pandas as pd
import pytest
import requests

from dengue.adapters.outbound.conversas_memoria import ConversasEmMemoria
from dengue.adapters.outbound.infodengue import ConsultaInfoDengueComCache, ConsultaInfoDengueHttp
from dengue.adapters.outbound.llm_llamacpp import ModeloLlamaCpp
from dengue.adapters.outbound.sentimentos_csv import SentimentosCsv
from dengue.config import ConfigLlm
from dengue.core.domain.chat import Turno
from dengue.core.domain.erros import ConsultaSemDadosError, InfoDengueIndisponivelError
from dengue.core.domain.modelos import SentimentoNoticia

CSV = "SE,casos,nivel\n202450,5,1\n202551,7,2\n202601,9,3\n202701,1,1\n"


class Resp:
    def __init__(self, texto="", status=200): self.text, self.status_code = texto, status
    def raise_for_status(self):
        if self.status_code >= 400: raise requests.HTTPError(str(self.status_code))


class HttpFalso:
    def __init__(self, resposta=None, erro=None): self.resposta, self.erro, self.pedidos = resposta or Resp(CSV), erro, []
    def get(self, url, timeout=None):
        self.pedidos.append((url, timeout))
        if self.erro: raise self.erro
        return self.resposta


# -------------------------------------------------- consulta ao InfoDengue
def test_consulta_monta_a_url_de_joinville_dengue_com_semanas_1_a_53_e_filtra_os_anos():
    http = HttpFalso()
    df, req = ConsultaInfoDengueHttp(http=http, timeout_s=7).consultar(2025, 2026)
    url, timeout = http.pedidos[0]
    for trecho in ("geocode=4209102", "disease=dengue", "format=csv", "ew_start=1", "ew_end=53", "ey_start=2025", "ey_end=2026"):
        assert trecho in url
    assert timeout == 7 and req.url == url and (req.ano_inicio, req.ano_fim, req.geocode) == (2025, 2026, 4209102)
    assert list(df["SE"]) == [202551, 202601] and list(df["id"]) == ["202551", "202601"]      # anos fora do pedido saem; cria id


@pytest.mark.parametrize("http", [HttpFalso(erro=requests.ConnectionError("sem rede")), HttpFalso(erro=requests.Timeout()),
                                  HttpFalso(Resp(status=503)), HttpFalso(Resp("<html>erro</html>\n\x00\x00"))])
def test_falhas_de_rede_ou_http_viram_erro_amigavel_sem_dado_sintetico(http):
    with pytest.raises((InfoDengueIndisponivelError, ConsultaSemDadosError)):
        ConsultaInfoDengueHttp(http=http).consultar(2026, 2026)


@pytest.mark.parametrize("texto", ["", "SE,casos\n", "casos,nivel\n1,1\n"])
def test_resposta_vazia_ou_sem_coluna_se_vira_consulta_sem_dados(texto):
    with pytest.raises((ConsultaSemDadosError, InfoDengueIndisponivelError)):
        ConsultaInfoDengueHttp(http=HttpFalso(Resp(texto))).consultar(2026, 2026)


def test_cache_evita_repetir_a_consulta_ate_o_ttl_e_devolve_copias():
    http, agora = HttpFalso(), [0.0]
    c = ConsultaInfoDengueComCache(ConsultaInfoDengueHttp(http=http), ttl_s=100, relogio=lambda: agora[0])
    a, _ = c.consultar(2025, 2026)
    a.loc[:, "casos"] = -1                                        # alterar a cópia não contamina o cache
    b, _ = c.consultar(2025, 2026)
    assert len(http.pedidos) == 1 and (b["casos"] > 0).all()
    c.consultar(2024, 2026)                                       # período diferente = outra chave
    assert len(http.pedidos) == 2
    agora[0] = 101.0
    c.consultar(2025, 2026)
    assert len(http.pedidos) == 3                                 # expirou


def test_cache_nao_guarda_falhas():
    http = HttpFalso(erro=requests.ConnectionError("x"))
    c = ConsultaInfoDengueComCache(ConsultaInfoDengueHttp(http=http))
    for _ in range(2):
        with pytest.raises(InfoDengueIndisponivelError):
            c.consultar(2026, 2026)
    assert len(http.pedidos) == 2


# --------------------------------------------------------------- memória
def turno(n): return Turno(f"p{n}", f"r{n}", "resposta")


def test_memoria_guarda_ordem_limita_turnos_e_limpa():
    m = ConversasEmMemoria(max_turnos=3)
    assert m.obter("s") == [] and not m.existe("s")
    for i in range(5):
        m.adicionar("s", turno(i))
    assert [t.pergunta for t in m.obter("s")] == ["p2", "p3", "p4"] and m.existe("s")
    m.obter("s").clear()                                          # a lista devolvida é cópia
    assert len(m.obter("s")) == 3
    m.limpar("s"); m.limpar("s")
    assert not m.existe("s")


def test_memoria_descarta_a_sessao_menos_recente():
    m = ConversasEmMemoria(max_sessoes=2)
    m.adicionar("a", turno(1)); m.adicionar("b", turno(1)); m.adicionar("a", turno(2)); m.adicionar("c", turno(1))
    assert m.existe("a") and m.existe("c") and not m.existe("b")


def test_memoria_e_segura_com_threads():
    m = ConversasEmMemoria(max_sessoes=50, max_turnos=1000)
    ts = [threading.Thread(target=lambda i=i: [m.adicionar(f"s{i % 5}", turno(j)) for j in range(100)]) for i in range(10)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert sum(len(m.obter(f"s{i}")) for i in range(5)) == 1000


# ------------------------------------------------------------ sentimentos
def sent(i, classe="NEUTRO", data="2026-01-09T10:00:00+00:00"):
    return SentimentoNoticia(i, f"Título {i}", classe, "porque sim, com vírgula", "FakeLLM", 1.5, "2026-11-22T10:00:00", data)


def test_sentimentos_csv_upsert_ordenacao_e_valores_vazios(tmp_path):
    r = SentimentosCsv(tmp_path / "pasta" / "s.csv")
    assert r.listar() == []
    r.salvar(sent(2)); r.salvar(sent(1, data=None)); r.salvar(sent(2, "NEGATIVO"))      # 2 é substituído
    itens = r.listar()
    assert [(s.noticia_id, s.classe) for s in itens] == [(1, "NEUTRO"), (2, "NEGATIVO")]
    assert itens[0].data_publicacao is None and itens[1].justificativa == "porque sim, com vírgula" and itens[1].tempo_segundos == 1.5
    assert itens[1].rotulo == "Preocupante"


# ------------------------------------------- llama.cpp: modo JSON e métricas
def llama(tokens=("a", "b", "c")):
    class L:
        instancias = []
        def __init__(self, **kw): L.instancias.append(self); self.chamadas = []
        def create_chat_completion(self, **kw):
            self.chamadas.append(kw)
            return iter([{"choices": [{"delta": {"content": t}}]} for t in tokens])
    return L


@pytest.fixture
def cfg(tmp_path):
    arq = tmp_path / "m.gguf"; arq.write_bytes(b"x")
    return ConfigLlm(caminho_personalizado=arq, timeout_s=5)


def relogio():
    t = [0.0]
    def agora():
        t[0] += 1.0
        return t[0]
    return agora


def test_modo_json_pede_response_format_ao_llama_cpp(cfg):
    L = llama()
    m = ModeloLlamaCpp(cfg, fabrica_llama=lambda: L)
    m.gerar("p", max_tokens=10)
    m.gerar("p", max_tokens=10, formato_json=True)
    normal, json_ = L.instancias[0].chamadas
    assert "response_format" not in normal and json_["response_format"] == {"type": "json_object"}


def test_metricas_de_tempo_e_tokens_sao_medidas_e_carga_so_na_primeira_vez(cfg):
    m = ModeloLlamaCpp(cfg, fabrica_llama=lambda: llama(("x",) * 6), medidor=relogio())
    assert m.ultimas_metricas() is None
    m.gerar("p", max_tokens=5)
    a = m.ultimas_metricas()
    assert a["tokens_gerados"] == 6 and a["tempo_carga_s"] > 0 and a["tempo_primeiro_token_s"] > 0
    assert a["tokens_por_s"] > 0 and a["tempo_total_s"] >= a["tempo_carga_s"] + a["tempo_geracao_s"] - 1e-6
    m.gerar("p", max_tokens=5)
    assert m.ultimas_metricas()["tempo_carga_s"] == 0.0                  # modelo já estava na memória
