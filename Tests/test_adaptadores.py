import json

import pandas as pd
import pytest
import requests

from dengue.adapters.outbound.infodengue import (
    InfoDengueAmostraCsv, InfoDengueComAlternativa, InfoDengueHttp, UploadsCsv, montar_url,
)
from dengue.adapters.outbound.noticias_arquivos import CorpusJsonl, NoticiasCsvTxt
from dengue.adapters.outbound.nsc_scraper import ColetorNscTotal, extrair_artigo, extrair_candidatos
from dengue.config import Configuracoes
from dengue.core.domain.erros import ColetaError
from dengue.core.domain.modelos import ArtigoColetado, ContextoNumerico, TrechoCorpus

from dados import PARAGRAFO_A
from fakes import FonteFixa


# ---------------------------------------------------------- InfoDengue
def test_montar_url_identica_ao_exemplo_do_enunciado():
    assert montar_url() == ("https://info.dengue.mat.br/api/alertcity?&disease=dengue&geocode=4209102&disease=dengue"
                            "&format=csv&ew_start=1&ew_end=52&ey_start=2026&ey_end=2026")


class RespostaFalsa:
    def __init__(self, texto="", status=200): self.text, self.status_code = texto, status
    def raise_for_status(self):
        if self.status_code >= 400: raise requests.HTTPError(str(self.status_code))


def test_infodengue_http_le_csv_e_cria_id_quando_ausente(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, timeout: RespostaFalsa("SE,nivel\n202601,1\n202602,2\n"))
    df, origem = InfoDengueHttp().buscar()
    assert origem == "api" and list(df["id"]) == ["202601", "202602"]


def test_infodengue_http_erro_http_propaga(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, timeout: RespostaFalsa(status=503))
    with pytest.raises(requests.HTTPError):
        InfoDengueHttp().buscar()


def test_alternativa_entra_quando_a_principal_falha(raiz, monkeypatch):
    def cai(url, timeout): raise requests.ConnectionError("sem internet")
    monkeypatch.setattr(requests, "get", cai)
    fonte = InfoDengueComAlternativa(InfoDengueHttp(), InfoDengueAmostraCsv(raiz / "Data" / "Raw" / "infodengue_sample.csv"))
    df, origem = fonte.buscar()
    assert origem == "amostra_local" and len(df) == 6


def test_alternativa_nao_e_usada_quando_a_principal_funciona():
    principal, nunca = FonteFixa(pd.DataFrame({"id": [1]}), "api"), FonteFixa(pd.DataFrame(), "amostra_local")
    assert InfoDengueComAlternativa(principal, nunca).buscar()[1] == "api" and nunca.chamadas == 0


def test_uploads_csv_ida_e_volta_e_limpar(tmp_path):
    u = UploadsCsv(tmp_path / "pasta" / "up.csv")
    assert u.carregar().empty
    u.salvar(pd.DataFrame({"id": ["a"], "SE": [1]}))
    assert list(u.carregar()["id"]) == ["a"]
    u.limpar(); u.limpar()  # idempotente
    assert u.carregar().empty


# ------------------------------------------------------------ arquivos
def test_repositorio_noticias_le_csv_e_txt(raiz):
    repo = NoticiasCsvTxt(raiz / "Data/Raw/nsc_noticias_joinville_dengue.csv", raiz / "Data/Raw/nsc_noticias_texto.txt")
    assert [n.id for n in repo.listar()] == [1, 2]
    n2 = repo.obter(2)
    assert n2.autor is None and n2.resumo is None          # NaN do CSV vira None
    assert [n.id for n in repo.listar("MOSQUITOS")] == [2] and len(repo.listar(limite=1)) == 1
    assert repo.obter(99) is None and repo.paragrafos(99) == []
    assert PARAGRAFO_A in repo.paragrafos(1)


def test_repositorio_noticias_sem_arquivos_nao_quebra(tmp_path):
    repo = NoticiasCsvTxt(tmp_path / "x.csv", tmp_path / "x.txt")
    assert repo.listar() == [] and repo.paragrafos(1) == []


def test_repositorio_noticias_salvar_atribui_ids_e_relê(tmp_path):
    repo = NoticiasCsvTxt(tmp_path / "d" / "n.csv", tmp_path / "d" / "n.txt")
    salvas = repo.salvar([ArtigoColetado("A", "u1", "2026", "X", "r", PARAGRAFO_A), ArtigoColetado("B", "u2", corpo="b b b")])
    assert [n.id for n in salvas] == [1, 2]
    assert repo.obter(1).titulo == "A" and repo.paragrafos(1) == [PARAGRAFO_A]


def test_corpus_jsonl_ida_e_volta(tmp_path):
    c = CorpusJsonl(tmp_path / "c.jsonl", tmp_path / "ctx.json")
    assert not c.existe() and c.obter_noticia(1) is None and c.listar_titulos() == []
    trechos = [TrechoCorpus(1, 1, "T1", "segundo", resumo="R"), TrechoCorpus(1, 0, "T1", "primeiro"), TrechoCorpus(2, 0, "T2", "x")]
    c.salvar(trechos, ContextoNumerico("Joinville", "api", 3, {"1": 3}, 7, {"SE": 1, "casos": 7}))
    assert c.existe()
    n = c.obter_noticia(1)
    assert n.texto == "primeiro\nsegundo" and n.resumo == "R"   # reordena por chunk_id
    assert c.listar_titulos(limite=1) == ["T1"] and c.obter_contexto().casos_total == 7
    assert json.loads((tmp_path / "ctx.json").read_text(encoding="utf-8"))["origem_dados"] == "api"


# ------------------------------------------------------------- scraper
LISTAGEM = """<html><body>
<h2><a href="/saude/mosquitos-joinville">Mosquitos em Joinville</a></h2>
<h2><a href="/saude/outra-cidade">Dengue em Blumenau</a></h2>
<h3><a href="https://www.nsctotal.com.br/saude/joinville-zera">Joinville zera mortes</a></h3>
<h2><a href="/saude/mosquitos-joinville">Mosquitos em Joinville</a></h2><h2>Sem link Joinville</h2></body></html>"""
ARTIGO = """<html><head><meta property="og:title" content="Título OG"><meta property="og:description" content="Resumo OG">
<meta property="article:published_time" content="2026-01-09T23:02:31+00:00"></head><body>
<a href="/autor/ana/">Ana Souza</a><p>curto</p><p>Este parágrafo é comprido o bastante para entrar no corpo do artigo coletado.</p></body></html>"""


def test_extrair_candidatos_filtra_joinville_e_remove_repetidos():
    achados = extrair_candidatos(LISTAGEM)
    assert [t for t, _ in achados] == ["Mosquitos em Joinville", "Joinville zera mortes"]
    assert achados[0][1] == "https://www.nsctotal.com.br/saude/mosquitos-joinville"


def test_extrair_artigo_le_metatags_autor_e_corpo():
    a = extrair_artigo(ARTIGO, "u")
    assert (a.titulo, a.resumo, a.autor) == ("Título OG", "Resumo OG", "Ana Souza")
    assert a.data_publicacao.startswith("2026-01-09") and a.corpo.startswith("Este parágrafo") and "curto" not in a.corpo


class HttpFalso:
    def __init__(self, paginas): self.paginas, self.pedidos = paginas, []
    def get(self, url, headers=None, timeout=None):
        self.pedidos.append(url)
        r = self.paginas.get(url)
        if isinstance(r, Exception): raise r
        return RespostaFalsa(r if r is not None else "", 200 if r is not None else 404)


def test_coletor_percorre_paginas_e_artigos_sem_dormir_de_verdade():
    base = "https://www.nsctotal.com.br"
    http = HttpFalso({f"{base}/tag/dengue": LISTAGEM, f"{base}/tag/dengue/page/2": "<html></html>",
                      f"{base}/saude/mosquitos-joinville": ARTIGO, f"{base}/saude/joinville-zera": requests.ConnectionError("x")})
    pausas = []
    artigos = ColetorNscTotal(pausa_s=0.5, http=http, dormir=pausas.append).coletar(2)
    assert len(artigos) == 1 and artigos[0].titulo == "Título OG"        # artigo com falha é pulado
    assert pausas and all(p == 0.5 for p in pausas)


def test_coletor_falha_na_primeira_pagina_vira_erro_amigavel():
    http = HttpFalso({"https://www.nsctotal.com.br/tag/dengue": requests.ConnectionError("sem rede")})
    with pytest.raises(ColetaError) as e:
        ColetorNscTotal(http=http, dormir=lambda s: None).coletar(2)
    assert "conexão" in e.value.sugestao


def test_coletor_falha_em_pagina_posterior_mantem_o_que_ja_coletou():
    base = "https://www.nsctotal.com.br"
    http = HttpFalso({f"{base}/tag/dengue": LISTAGEM, f"{base}/tag/dengue/page/2": requests.ConnectionError("x"),
                      f"{base}/saude/mosquitos-joinville": ARTIGO, f"{base}/saude/joinville-zera": ARTIGO})
    assert len(ColetorNscTotal(http=http, dormir=lambda s: None).coletar(3)) == 2


# -------------------------------------------------------------- config
def test_config_le_ambiente_e_ignora_valores_invalidos(tmp_path):
    cfg = Configuracoes.do_ambiente({"DENGUE_LLM_BACKEND": "FAKE", "DENGUE_LLM_N_CTX": "2048", "DENGUE_LLM_TIMEOUT_S": "abc",
                                     "DENGUE_LLM_GPU_LAYERS": "-1", "DENGUE_API_URL": "http://x:1"}, raiz=tmp_path)
    assert (cfg.llm.backend, cfg.llm.n_ctx, cfg.llm.n_gpu_layers, cfg.api_url) == ("fake", 2048, -1, "http://x:1")
    assert cfg.llm.timeout_s == 600.0                                     # inválido -> padrão
    assert cfg.llm.caminho_modelo == tmp_path / "Models" / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    assert Configuracoes.do_ambiente({"DENGUE_LLM_CAMINHO": "/m.gguf"}).llm.caminho_modelo.as_posix() == "/m.gguf"
