"""Páginas Dashboard e Converse com os dados (AppTest) + novos métodos dos gateways."""
from pathlib import Path

import pandas as pd
import pytest
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

from dengue.adapters.inbound.ui_streamlit import deps
from dengue.adapters.inbound.ui_streamlit.gateways import ApiGateway, GatewayComAlternativa, LocalGateway
from dengue.core.domain.chat import PERGUNTAS_EXEMPLO
from dengue.core.domain.erros import ApiIndisponivelError, ErroRemoto, InfoDengueIndisponivelError, ModeloIndisponivelError

from fakes_interface import GatewayFalso

VIEWS = Path(__file__).resolve().parents[1] / "Code/dengue/adapters/inbound/ui_streamlit/views"


@pytest.fixture(autouse=True)
def _limpa_cache():
    st.cache_data.clear()


def abrir(pagina, gateway, monkeypatch):
    monkeypatch.setattr(deps, "obter_gateway", lambda: gateway)
    return AppTest.from_file(str(VIEWS / f"{pagina}.py"), default_timeout=60).run()


def texto(at):
    elementos = list(at.markdown) + list(at.error) + list(at.info) + list(at.warning) + list(at.caption) + list(at.success)
    return " ".join(str(e.value) for e in elementos)


def sentimentos():
    return pd.DataFrame([
        {"noticia_id": 1, "titulo": "Joinville zera mortes", "classe": "POSITIVO", "rotulo": "Tranquilizador", "justificativa": "j", "data_publicacao": "2026-02-01T10:00:00+00:00"},
        {"noticia_id": 2, "titulo": "Surto preocupa", "classe": "NEGATIVO", "rotulo": "Preocupante", "justificativa": "j", "data_publicacao": "2026-03-01T10:00:00+00:00"}])


# ------------------------------------------------------------------ dashboard
def test_dashboard_mostra_kpis_calculados_ciclo_e_graficos(monkeypatch):
    at = abrir("dashboard", GatewayFalso(), monkeypatch)
    assert not at.exception
    rotulos = [m.label for m in at.metric]
    assert any("Casos em 2026" in r for r in rotulos) and any("Pico em 2026" in r for r in rotulos)
    assert any("vs. 2025" in r for r in rotulos) and any("Nível de alerta" in r for r in rotulos)
    t = texto(at)
    assert "1 · Coleta" in t and "3 · IA local" in t and "5 · Interação" in t and "InfoDengue" in t
    assert len(at.get("plotly_chart")) == 3                                  # sazonalidade, total por ano, semanas por nível


def test_dashboard_sem_sentimentos_explica_como_gerar(monkeypatch):
    t = texto(abrir("dashboard", GatewayFalso(), monkeypatch))
    assert "Ainda não há notícias analisadas" in t and "analisar-sentimentos" in t


def test_dashboard_com_sentimentos_mostra_graficos_da_midia_e_o_aviso_de_limites(monkeypatch):
    at = abrir("dashboard", GatewayFalso(sentimentos=sentimentos()), monkeypatch)
    assert not at.exception and len(at.get("plotly_chart")) == 5
    assert "indicador indireto" in texto(at) and len(at.dataframe) >= 2


def test_dashboard_filtro_de_anos_e_interativo(monkeypatch):
    at = abrir("dashboard", GatewayFalso(), monkeypatch)
    at.multiselect[0].set_value([2025]).run()
    assert not at.exception and len(at.get("plotly_chart")) == 3


def test_dashboard_sem_infodengue_mostra_erro_amigavel_sem_dado_sintetico(monkeypatch):
    at = abrir("dashboard", GatewayFalso(erro_historico=InfoDengueIndisponivelError("sem rede")), monkeypatch)
    assert not at.exception and any("consultar o InfoDengue" in e.value for e in at.error)
    assert any("conexão" in i.value for i in at.info) and not at.metric


# ----------------------------------------------------------------------- chat
def enviar(at, pergunta):
    at.chat_input[0].set_value(pergunta).run()
    return at


def test_chat_pergunta_mostra_resposta_requisicao_fatos_e_aviso(monkeypatch):
    gw = GatewayFalso()
    at = enviar(abrir("chat", gw, monkeypatch), PERGUNTAS_EXEMPLO[0])
    assert not at.exception and ("perguntar", None, PERGUNTAS_EXEMPLO[0]) in gw.chamadas
    assert [m.name for m in at.chat_message] == ["user", "assistant"]
    t = texto(at)
    assert "O pico foi na SE 202614 com 120 casos." in t and "alertcity" in " ".join(c.value for c in at.code)
    assert any("Como a resposta foi obtida" in e.label for e in at.expander) and "gerado por um modelo de IA" in t


def test_chat_mantem_a_mesma_sessao_entre_perguntas_e_guarda_o_historico_visivel(monkeypatch):
    gw = GatewayFalso()
    at = enviar(abrir("chat", gw, monkeypatch), "primeira pergunta")
    enviar(at, "segunda pergunta")
    perguntas = [c for c in gw.chamadas if c[0] == "perguntar"]
    assert perguntas[0][1] is None and perguntas[1][1] == "sessao12345678"
    assert [m.name for m in at.chat_message] == ["user", "assistant", "user", "assistant"]


def test_chat_botoes_de_exemplo_fazem_a_pergunta(monkeypatch):
    gw = GatewayFalso()
    at = abrir("chat", gw, monkeypatch)
    at.button(key="exemplo_1").click().run()
    assert ("perguntar", None, PERGUNTAS_EXEMPLO[1]) in gw.chamadas and not at.exception


def test_chat_nova_conversa_limpa_a_tela_e_encerra_a_sessao(monkeypatch):
    gw = GatewayFalso()
    at = enviar(abrir("chat", gw, monkeypatch), "primeira")
    at.button(key="nova_conversa").click().run()
    assert ("encerrar", "sessao12345678") in gw.chamadas and len(at.chat_message) == 0
    enviar(at, "outra")
    assert [c for c in gw.chamadas if c[0] == "perguntar"][-1][1] is None            # sessão nova


def test_chat_recusa_aparece_como_mensagem_sem_o_painel_de_como_foi_obtida(monkeypatch):
    gw = GatewayFalso()
    gw.resposta_chat = lambda s, p: {"sessao_id": "sessao12345678", "tipo": "recusa", "resposta": "Só respondo sobre casos de dengue em Joinville.",
                                      "modelo": "FakeLLM", "tempo_segundos": 0.0, "etapas": [], "avisos": [], "aviso_padrao": "⚠️ aviso", "plano": None, "requisicao": None, "fatos": None}
    at = enviar(abrir("chat", gw, monkeypatch), "Qual a capital da França?")
    assert "Só respondo sobre casos de dengue" in texto(at) and not any("Como a resposta" in e.label for e in at.expander)


@pytest.mark.parametrize("erro,trecho_msg,trecho_sugestao", [
    (ModeloIndisponivelError("arquivo_ausente"), "problema com a IA", "baixar-modelo"),
    (ApiIndisponivelError("http://x"), "falar com a API", "run_api.py"),
    (InfoDengueIndisponivelError("x"), "consultar o InfoDengue", "internet"),
])
def test_chat_erros_sao_amigaveis_e_a_conversa_continua(monkeypatch, erro, trecho_msg, trecho_sugestao):
    gw = GatewayFalso(erro_chat=erro)
    at = enviar(abrir("chat", gw, monkeypatch), "uma pergunta")
    assert not at.exception and any(trecho_msg in e.value for e in at.error) and any(trecho_sugestao in i.value for i in at.info)
    gw.erro_chat = None
    enviar(at, "outra tentativa")
    assert "O pico foi na SE" in texto(at)


def test_chat_erro_inesperado_nao_vaza_detalhes(monkeypatch):
    at = enviar(abrir("chat", GatewayFalso(erro_chat=KeyError("segredo")), monkeypatch), "pergunta")
    assert not at.exception and any("inesperado" in e.value for e in at.error) and "segredo" not in texto(at)


# --------------------------------------------------------------- gateways
class HttpFalso:
    def __init__(self, status=200, json=None, erro=None): self.status, self.json_, self.erro, self.pedidos = status, json, erro, []
    def request(self, metodo, url, timeout=None, **kw):
        self.pedidos.append((metodo, url, timeout, kw))
        if self.erro: raise self.erro
        o = self
        class R:
            status_code = o.status
            def json(self): return o.json_
        return R()


def test_api_gateway_pergunta_usa_timeout_longo_e_repassa_erros_da_api():
    http = HttpFalso(200, {"sessao_id": "s"})
    ApiGateway("http://x", http=http, timeout_chat_s=111).perguntar("abc12345", "oi")
    m, url, timeout, kw = http.pedidos[0]
    assert (m, url, timeout, kw["json"]) == ("POST", "http://x/chat", 111, {"sessao_id": "abc12345", "pergunta": "oi"})
    erro = {"codigo": "infodengue_indisponivel", "categoria": "dados", "mensagem": "Não foi possível consultar o InfoDengue agora.", "sugestao": "Verifique a internet."}
    with pytest.raises(ErroRemoto) as e:
        ApiGateway("http://x", http=HttpFalso(503, erro)).perguntar(None, "oi")
    assert e.value.categoria == "dados" and e.value.sugestao == "Verifique a internet."


def test_api_gateway_timeout_do_chat_e_erro_de_ia_e_nao_api_fora():
    with pytest.raises(ErroRemoto) as e:
        ApiGateway("http://x", http=HttpFalso(erro=requests.Timeout()), timeout_chat_s=9).perguntar(None, "oi")
    assert e.value.status_http == 504 and e.value.categoria == "ia"
    with pytest.raises(ApiIndisponivelError):
        ApiGateway("http://x", http=HttpFalso(erro=requests.ConnectionError())).perguntar(None, "oi")


def test_api_gateway_historico_sentimentos_e_encerrar():
    http = HttpFalso(200, {"serie": [{"SE": 202601, "casos": 1}], "fatos": {"a": 1}, "requisicao": {"url": "u"}, "itens": [{"noticia_id": 1}]})
    gw = ApiGateway("http://x", http=http)
    h = gw.historico_infodengue(2024, 2026)
    assert list(h["serie"]["SE"]) == [202601] and h["fatos"] == {"a": 1} and h["canal"] == "api"
    assert http.pedidos[0][3]["params"] == {"ano_inicio": 2024, "ano_fim": 2026}
    assert list(gw.sentimentos()["noticia_id"]) == [1]
    gw.encerrar_conversa(None)
    assert len(http.pedidos) == 2                                            # sem sessão, não chama a API
    gw.encerrar_conversa("abc12345")
    assert http.pedidos[-1][:2] == ("DELETE", "http://x/chat/abc12345")


def test_local_gateway_historico_e_sentimentos_pelo_nucleo_e_chat_exige_api(container):
    gw = LocalGateway(container)
    h = gw.historico_infodengue()
    assert h["canal"] == "local" and h["fatos"]["ano_mais_casos"]["ano"] == 2024 and {"ano", "semana"} <= set(h["serie"].columns)
    assert gw.sentimentos().empty
    with pytest.raises(ApiIndisponivelError):
        gw.perguntar(None, "oi")
    assert gw.encerrar_conversa("x") is None


def test_gateway_com_alternativa_usa_local_no_historico_mas_o_chat_exige_a_api(container):
    fora = ApiGateway("http://x", http=HttpFalso(erro=requests.ConnectionError()))
    gw = GatewayComAlternativa(fora, LocalGateway(container))
    assert gw.historico_infodengue()["canal"] == "local" and gw.sentimentos().empty
    gw.encerrar_conversa("abc12345")                                         # API fora: ignora em silêncio
    with pytest.raises(ApiIndisponivelError):
        gw.perguntar(None, "oi")
