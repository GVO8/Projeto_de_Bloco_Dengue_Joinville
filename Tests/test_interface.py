"""Páginas Streamlit (AppTest) com gateway falso, e gateways reais com HTTP falso."""
from pathlib import Path

import pandas as pd
import pytest
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

from dengue.adapters.inbound.ui_streamlit import deps
from dengue.adapters.inbound.ui_streamlit.gateways import ApiGateway, GatewayComAlternativa, LocalGateway
from dengue.core.domain.erros import ApiIndisponivelError, ErroRemoto, ModeloIndisponivelError

from fakes_interface import GatewayFalso

VIEWS = Path(__file__).resolve().parents[1] / "Code/dengue/adapters/inbound/ui_streamlit/views"


@pytest.fixture(autouse=True)
def _limpa_cache():
    st.cache_data.clear()


def abrir(pagina, gateway, monkeypatch):
    monkeypatch.setattr(deps, "obter_gateway", lambda: gateway)
    return AppTest.from_file(str(VIEWS / f"{pagina}.py"), default_timeout=60).run()


def textos(at):
    return " ".join(str(e.value) for e in list(at.markdown) + list(at.error) + list(at.info) + list(at.success) + list(at.warning) + list(at.caption))


@pytest.mark.parametrize("pagina", ["inicio", "painel", "noticias", "upload", "api_page", "ia"])
def test_todas_as_paginas_abrem_sem_excecao(pagina, monkeypatch):
    at = abrir(pagina, GatewayFalso(), monkeypatch)
    assert not at.exception


# ----------------------------------------------------- notícias e botões
def test_cada_noticia_tem_um_botao_por_operacao(monkeypatch):
    at = abrir("noticias", GatewayFalso(), monkeypatch)
    assert [b.key for b in at.button] == ["btn_resumo_1", "btn_sentimento_1", "btn_qa_1", "btn_relatorio_1"]


@pytest.mark.parametrize("op", ["resumo", "sentimento", "relatorio"])
def test_clique_chama_a_api_com_a_operacao_e_mostra_a_resposta(op, monkeypatch):
    gw = GatewayFalso()
    at = abrir("noticias", gw, monkeypatch)
    at.button(key=f"btn_{op}_1").click().run()
    assert not at.exception and ("processar", 1, op, "") in gw.chamadas
    t = textos(at)
    assert "Joinville zera mortes por dengue" in t and f"**Operação:** {op}" in t and "gerado por um modelo de IA" in t


def test_botao_perguntar_envia_o_texto_digitado(monkeypatch):
    gw = GatewayFalso()
    at = abrir("noticias", gw, monkeypatch)
    at.text_input(key="pergunta_1").set_value("Quantas mortes?").run()
    at.button(key="btn_qa_1").click().run()
    assert ("processar", 1, "qa", "Quantas mortes?") in gw.chamadas


def test_resultado_persiste_no_estado_da_sessao_entre_interacoes(monkeypatch):
    at = abrir("noticias", GatewayFalso(), monkeypatch)
    at.button(key="btn_resumo_1").click().run()
    at.text_input(key="pergunta_1").set_value("qualquer").run()                      # outra interação
    assert "Texto da IA." in textos(at)


def test_erro_de_ia_mostra_mensagem_amigavel_e_o_que_fazer(monkeypatch):
    gw = GatewayFalso(erro_ia=ModeloIndisponivelError("arquivo_ausente"))
    at = abrir("noticias", gw, monkeypatch)
    at.button(key="btn_resumo_1").click().run()
    assert not at.exception
    assert any("problema com a IA" in e.value and "Qwen3" in e.value for e in at.error)
    assert any("O que fazer" in i.value and "baixar-modelo" in i.value for i in at.info)


def test_api_fora_do_ar_orienta_a_ligar_a_api(monkeypatch):
    at = abrir("noticias", GatewayFalso(erro_ia=ApiIndisponivelError("http://x")), monkeypatch)
    at.button(key="btn_resumo_1").click().run()
    assert any("não conseguiu falar com a API" in e.value for e in at.error)
    assert any("run_api.py" in i.value for i in at.info)


def test_erro_inesperado_na_interface_nao_vaza_traceback(monkeypatch):
    at = abrir("noticias", GatewayFalso(erro_ia=KeyError("segredo")), monkeypatch)
    at.button(key="btn_resumo_1").click().run()
    assert not at.exception and any("inesperado" in e.value for e in at.error) and "segredo" not in textos(at)


def test_lista_vazia_orienta_a_coletar(monkeypatch):
    at = abrir("noticias", GatewayFalso(noticias=[]), monkeypatch)
    assert any("Nenhuma notícia" in w.value for w in at.warning) and any("coletar-noticias" in i.value for i in at.info)


# ------------------------------------------------------------ painel/upload
def test_painel_filtra_niveis_pela_barra_lateral(monkeypatch):
    at = abrir("painel", GatewayFalso(), monkeypatch)
    at.sidebar.multiselect[0].set_value([3]).run()
    assert not at.exception and at.metric[0].value == "3"


def test_painel_com_dados_invalidos_mostra_erro_amigavel(monkeypatch):
    gw = GatewayFalso()
    gw.serie = pd.DataFrame({"x": [1]})
    at = abrir("painel", gw, monkeypatch)
    assert any("colunas 'SE' e 'nivel'" in e.value for e in at.error)


def test_api_page_sem_api_mostra_erro_amigavel(monkeypatch):
    class Fora(GatewayFalso):
        def estado(self): raise ApiIndisponivelError("http://x")
    assert any("API" in e.value for e in abrir("api_page", Fora(), monkeypatch).error)


# ------------------------------------------------------------- gateways
class HttpFalso:
    def __init__(self, status=200, json=None, erro=None): self.status, self.json_, self.erro, self.pedidos = status, json, erro, []
    def request(self, metodo, url, timeout=None, **kw):
        self.pedidos.append((metodo, url, timeout, kw))
        if self.erro: raise self.erro
        outer = self
        class R:
            status_code = outer.status
            def json(self):
                if outer.json_ is None: raise ValueError("sem json")
                return outer.json_
        return R()


def test_api_gateway_repassa_erro_da_api_sem_perder_mensagens():
    payload = {"codigo": "modelo_indisponivel", "categoria": "ia", "mensagem": "Houve um problema com a IA", "sugestao": "baixe o modelo"}
    with pytest.raises(ErroRemoto) as e:
        ApiGateway("http://x", http=HttpFalso(503, payload)).processar_noticia(1, "resumo")
    assert (e.value.mensagem, e.value.sugestao, e.value.categoria, e.value.status_http) == ("Houve um problema com a IA", "baixe o modelo", "ia", 503)


def test_api_gateway_erro_sem_json_e_conexao_recusada():
    with pytest.raises(ErroRemoto) as e:
        ApiGateway("http://x", http=HttpFalso(500)).obter_infodengue()
    assert "500" in e.value.mensagem and e.value.sugestao
    with pytest.raises(ApiIndisponivelError):
        ApiGateway("http://x", http=HttpFalso(erro=requests.ConnectionError())).obter_infodengue()


def test_api_gateway_timeout_da_ia_e_erro_de_ia_e_nao_de_api_fora():
    gw = ApiGateway("http://x", http=HttpFalso(erro=requests.Timeout()), timeout_ia_s=7)
    with pytest.raises(ErroRemoto) as e:
        gw.processar_noticia(1, "resumo")
    assert e.value.categoria == "ia" and e.value.status_http == 504
    with pytest.raises(ApiIndisponivelError):
        gw.obter_infodengue()                                  # timeout curto = API fora


def test_api_gateway_monta_requisicoes_corretas():
    http = HttpFalso(200, {"dados": [{"id": "a"}], "origem": "api", "adicionadas": 1})
    gw = ApiGateway("http://x/", http=http, timeout_ia_s=123)
    df, canal = gw.obter_infodengue(202601, None, [3])
    assert canal == "api" and list(df["id"]) == ["a"]
    assert http.pedidos[0][:2] == ("GET", "http://x/infodengue") and http.pedidos[0][3]["params"]["nivel"] == [3]
    HttpFalso_json = HttpFalso(200, {"x": 1})
    ApiGateway("http://x", http=HttpFalso_json, timeout_ia_s=123).processar_noticia(5, "qa", "p")
    m, url, timeout, kw = HttpFalso_json.pedidos[0]
    assert (m, url, timeout, kw["json"]) == ("POST", "http://x/noticias/5/processar", 123, {"operacao": "qa", "pergunta": "p"})


def test_gateway_com_alternativa_usa_local_quando_api_fora_mas_ia_exige_api(container):
    fora = ApiGateway("http://x", http=HttpFalso(erro=requests.ConnectionError()))
    gw = GatewayComAlternativa(fora, LocalGateway(container))
    df, canal = gw.obter_infodengue()
    assert canal == "local" and len(df) == 6
    assert gw.listar_noticias()[1] == "local" and gw.texto_noticias()[1] == "local"
    resumo, canal = gw.enviar_infodengue(pd.DataFrame({"id": ["n"], "SE": [202650], "nivel": [2]}))
    assert canal == "local" and resumo["adicionadas"] == 1 and gw.resetar_uploads() == "local"
    with pytest.raises(ApiIndisponivelError):
        gw.processar_noticia(1, "resumo")
    with pytest.raises(ApiIndisponivelError):
        gw.estado()
