"""Rotas da conversa com os dados, do histórico do InfoDengue e dos sentimentos (FakeLLM + consulta falsa)."""
import pytest
from fastapi.testclient import TestClient

from dengue.adapters.inbound.api_fastapi.app import create_app
from dengue.adapters.outbound.llm_fake import ModeloFake
from dengue.core.domain.chat import PERGUNTAS_EXEMPLO
from dengue.core.domain.erros import ConsultaSemDadosError, InfoDengueIndisponivelError, ModeloIndisponivelError, ModeloTimeoutError
from dengue.core.domain.modelos import AVISO_PADRAO

from fakes import ConsultaFalsa, modelo_chat


@pytest.fixture
def api(container):
    container.conversar._modelo = container.modelo = modelo_chat(resposta="O ano com mais casos foi 2024, com 5.600 casos.")
    return TestClient(create_app(container), raise_server_exceptions=False)


def perguntar(api, texto, sessao_id=None):
    return api.post("/chat", json={"pergunta": texto, **({"sessao_id": sessao_id} if sessao_id else {})})


# ----------------------------------------------------------------- /chat
def test_chat_responde_com_a_requisicao_ao_infodengue_os_fatos_e_o_aviso(api):
    r = perguntar(api, PERGUNTAS_EXEMPLO[1])
    j = r.json()
    assert r.status_code == 200 and j["tipo"] == "resposta" and j["resposta"].startswith("O ano com mais casos foi 2024")
    assert j["requisicao"]["geocode"] == 4209102 and "ey_start=2017" in j["requisicao"]["url"] and j["plano"]["ano_fim"] == 2026
    assert "2024 (5.600 casos)" in j["fatos"] and j["aviso_padrao"] == AVISO_PADRAO and len(j["sessao_id"]) == 32
    assert [e["nome"] for e in j["etapas"]] == ["planejamento", "consulta_infodengue", "resposta"] and j["tempo_segundos"] >= 0


def test_chat_tem_memoria_por_sessao_e_historico_consultavel(api):
    sessao = perguntar(api, PERGUNTAS_EXEMPLO[0]).json()["sessao_id"]
    j = perguntar(api, "e em 2024?", sessao).json()
    assert j["sessao_id"] == sessao and j["tipo"] == "resposta"
    turnos = api.get(f"/chat/{sessao}").json()["turnos"]
    assert [t["pergunta"] for t in turnos] == [PERGUNTAS_EXEMPLO[0], "e em 2024?"]
    assert api.delete(f"/chat/{sessao}").status_code == 204
    r = api.get(f"/chat/{sessao}")
    assert r.status_code == 404 and r.json()["codigo"] == "sessao_nao_encontrada" and r.json()["sugestao"]
    assert api.delete(f"/chat/{sessao}").status_code == 204                      # idempotente


@pytest.mark.parametrize("pergunta", ["Qual a capital da França?", "Casos de dengue em Curitiba?", "E no Brasil?"])
def test_chat_recusa_fora_do_escopo_com_200_sem_consultar_o_infodengue(api, container, pergunta):
    r = perguntar(api, pergunta)
    j = r.json()
    assert r.status_code == 200 and j["tipo"] == "recusa" and j["plano"] is None and j["requisicao"] is None and j["fatos"] is None
    assert "Joinville" in j["resposta"] and container.consulta_infodengue.chamadas == []


def test_chat_validacao_de_entrada(api):
    assert api.post("/chat", json={"pergunta": ""}).status_code == 422
    r = perguntar(api, "   ")
    assert r.status_code == 422 and r.json()["codigo"] == "pergunta_invalida" and "vazia" in r.json()["mensagem"]
    r = perguntar(api, "x" * 301)
    assert r.status_code == 422 and "texto longo demais" in r.json()["mensagem"]
    assert perguntar(api, PERGUNTAS_EXEMPLO[0], "curto").status_code == 422
    assert api.post("/chat", json={}).json()["codigo"] == "dados_invalidos"


@pytest.mark.parametrize("erro,status,codigo,categoria", [
    (InfoDengueIndisponivelError("sem rede"), 503, "infodengue_indisponivel", "dados"),
    (ConsultaSemDadosError(2026, 2026), 404, "consulta_sem_dados", "dados"),
])
def test_chat_erros_do_infodengue(container, erro, status, codigo, categoria):
    container.consulta_infodengue.erro = erro
    r = perguntar(TestClient(create_app(container), raise_server_exceptions=False), PERGUNTAS_EXEMPLO[0])
    assert (r.status_code, r.json()["codigo"], r.json()["categoria"]) == (status, codigo, categoria) and r.json()["sugestao"]


@pytest.mark.parametrize("erro,status", [(ModeloIndisponivelError("arquivo_ausente"), 503), (ModeloTimeoutError(30), 504)])
def test_chat_erros_da_ia_sao_identificados_como_da_ia(container, erro, status):
    container.conversar._modelo = ModeloFake(erro=erro)
    j = perguntar(TestClient(create_app(container), raise_server_exceptions=False), PERGUNTAS_EXEMPLO[0])
    assert j.status_code == status and j.json()["categoria"] == "ia" and "problema com a IA" in j.json()["mensagem"]


def test_chat_erro_inesperado_nao_vaza_detalhes(container):
    container.conversar._modelo = ModeloFake(erro=RuntimeError("SEGREDO"))
    r = perguntar(TestClient(create_app(container), raise_server_exceptions=False), PERGUNTAS_EXEMPLO[0])
    assert r.status_code == 500 and "SEGREDO" not in r.text


# ------------------------------------------------ /infodengue/historico
def test_historico_padrao_traz_tres_anos_anteriores_serie_e_fatos(api):
    j = api.get("/infodengue/historico").json()
    assert (j["requisicao"]["ano_inicio"], j["requisicao"]["ano_fim"]) == (2023, 2026) and "geocode=4209102" in j["requisicao"]["url"]
    assert j["fatos"]["ano_mais_casos"]["ano"] == 2024 and j["fatos"]["comparacao"]["variacao_pct"] == 50.0
    linha = j["serie"][0]
    assert {"SE", "casos", "nivel", "ano", "semana", "data_iniSE"} <= set(linha) and linha["ano"] == 2023 and linha["semana"] == 1


def test_historico_periodo_personalizado_e_validacao(api):
    assert api.get("/infodengue/historico?ano_inicio=2024&ano_fim=2025").json()["fatos"]["periodo"]["ano_inicio"] == 2024
    for q in ("ano_fim=2030", "ano_inicio=2026&ano_fim=2025", "ano_inicio=2005&ano_fim=2010", "ano_inicio=abc"):
        r = api.get(f"/infodengue/historico?{q}")
        assert r.status_code == 422 and r.json()["sugestao"], q


def test_historico_erros_da_fonte(container):
    container.consulta_infodengue.erro = InfoDengueIndisponivelError("x")
    r = TestClient(create_app(container), raise_server_exceptions=False).get("/infodengue/historico")
    assert r.status_code == 503 and r.json()["categoria"] == "dados"


# ------------------------------------------------------------- /sentimentos
def test_sentimentos_vazio_e_depois_da_analise_pelo_botao(api, container):
    assert api.get("/sentimentos").json() == {"total": 0, "por_classe": {}, "itens": []}
    container.processar_noticia._modelo = ModeloFake("NEGATIVO. Transmite preocupação.")
    api.post("/noticias/1/processar", json={"operacao": "sentimento"})
    j = api.get("/sentimentos").json()
    assert j["total"] == 1 and j["por_classe"] == {"NEGATIVO": 1}
    assert j["itens"][0]["rotulo"] == "Preocupante" and j["itens"][0]["titulo"] == "Joinville zera mortes por dengue"


def test_resposta_de_processar_inclui_metricas(api, container):
    j = api.post("/noticias/1/processar", json={"operacao": "resumo"}).json()
    assert "metricas" in j and j["metricas"]["tokens_gerados"] > 0


def test_openapi_documenta_as_rotas_novas(api):
    caminhos = api.get("/openapi.json").json()["paths"]
    assert {"/chat", "/chat/{sessao_id}", "/infodengue/historico", "/sentimentos"} <= set(caminhos)
    assert {"200", "422", "503", "504"} <= set(caminhos["/chat"]["post"]["responses"])
