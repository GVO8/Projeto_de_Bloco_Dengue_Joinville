"""API FastAPI de ponta a ponta, com o FakeLLM injetado pelo container (nenhum modelo real)."""
import re

import pytest
from fastapi.testclient import TestClient

from dengue.adapters.inbound.api_fastapi.app import create_app
from dengue.adapters.outbound.llm_fake import ModeloFake
from dengue.core.domain.erros import (
    ModeloFalhaError, ModeloIndisponivelError, ModeloOcupadoError, ModeloTimeoutError, RespostaVaziaError,
)
from dengue.core.domain.modelos import AVISO_PADRAO

from dados import PARAGRAFO_A


def cliente(container, **kw):
    return TestClient(create_app(container), raise_server_exceptions=False, **kw)


@pytest.fixture
def api(container):
    return cliente(container)


def processar(api, i=1, operacao="resumo", **extra):
    return api.post(f"/noticias/{i}/processar", json={"operacao": operacao, **extra})


# --------------------------------------------------------------- sistema
def test_health_informa_estado_do_modelo(api):
    j = api.get("/health").json()
    assert j["status"] == "ok" and j["modelo_ia"]["backend"] == "fake" and j["modelo_ia"]["pronto"] is True


def test_operacoes_lista_as_quatro_e_quem_exige_pergunta(api):
    ops = {o["operacao"]: o["exige_pergunta"] for o in api.get("/operacoes").json()}
    assert ops == {"resumo": False, "sentimento": False, "qa": True, "relatorio": False}


# --------------------------------------------------- processar: sucesso
def test_processar_resposta_estruturada_e_ordenada(api):
    r = processar(api)
    assert r.status_code == 200
    j = r.json()
    assert list(j)[:6] == ["noticia_id", "titulo", "operacao", "nome_operacao", "resultado", "resumo_final"]  # ordem do contrato
    assert j["titulo"] == "Joinville zera mortes por dengue" and j["nome_operacao"] == "Resumo automático de notícia"
    assert j["aviso_padrao"] == AVISO_PADRAO and j["tempo_segundos"] >= 0 and j["modelo"].startswith("FakeLLM")
    md = j["markdown"]
    pos = [md.index(x) for x in (j["titulo"], "Operação:", j["resultado"], "Resumo final:", AVISO_PADRAO)]
    assert pos == sorted(pos) and md.rstrip().endswith(AVISO_PADRAO + "_")                                  # aviso no fim


def test_processar_sentimento_devolve_classe_como_resumo_final(container):
    c = cliente(container)
    container.processar_noticia._modelo = ModeloFake("POSITIVO. A queda é uma boa notícia.")
    assert processar(c, operacao="sentimento").json()["resumo_final"] == "Sentimento: POSITIVO"


def test_processar_qa_leva_a_pergunta_ao_prompt(container):
    modelo = ModeloFake("Foram 83. Em 2024.")
    container.processar_noticia._modelo = modelo
    j = processar(cliente(container), operacao="qa", pergunta="Quantas mortes em 2024?").json()
    assert "Quantas mortes em 2024?" in modelo.chamadas[0]["prompt"] and PARAGRAFO_A[:40] in modelo.chamadas[0]["prompt"]
    assert j["resumo_final"] == "Foram 83."


def test_processar_relatorio_avisa_que_dados_sao_de_exemplo(api):
    j = processar(api, operacao="relatorio").json()
    assert any("sintéticos" in a for a in j["avisos"]) and "sintéticos" in j["markdown"]


def test_corpus_desatualizado_e_reconstruido_sozinho(container):
    container.preparar_corpus.executar()
    (container.config.data_raw / "nsc_noticias_joinville_dengue.csv").write_text(
        (container.config.data_raw / "nsc_noticias_joinville_dengue.csv").read_text(encoding="utf-8")
        + "3,Joinville tem nova campanha contra a dengue,2026-09-01,Bia,https://e/3,r\n", encoding="utf-8")
    with open(container.config.data_raw / "nsc_noticias_texto.txt", "a", encoding="utf-8") as f:
        f.write("### Joinville tem nova campanha contra a dengue\n" + PARAGRAFO_A + "\n")
    assert processar(cliente(container), 3).status_code == 200


# --------------------------------------------------- processar: entrada
def test_qa_sem_pergunta_e_422_com_orientacao(api):
    r = processar(api, operacao="qa")
    j = r.json()
    assert r.status_code == 422 and j["codigo"] == "pergunta_obrigatoria" and j["categoria"] == "entrada" and "Digite" in j["sugestao"]


def test_operacao_invalida_tem_mensagem_em_portugues(api):
    r = processar(api, operacao="traduzir")
    assert r.status_code == 422 and "campo 'operacao'" in r.json()["mensagem"] and "valor não permitido" in r.json()["mensagem"]


def test_pergunta_longa_demais_e_corpo_invalido(api):
    assert processar(api, operacao="qa", pergunta="x" * 501).status_code == 422
    r = api.post("/noticias/1/processar", content=b"{nao e json", headers={"content-type": "application/json"})
    assert r.status_code == 422 and r.json()["categoria"] == "entrada"
    assert api.post("/noticias/abc/processar", json={"operacao": "resumo"}).status_code == 422


def test_noticia_inexistente_e_404_com_sugestao(api):
    r = processar(api, 999)
    assert r.status_code == 404 and r.json()["codigo"] == "noticia_nao_encontrada" and r.json()["sugestao"]


# ------------------------------------------------ processar: erros da IA
@pytest.mark.parametrize("erro,status,codigo", [
    (ModeloIndisponivelError("arquivo_ausente"), 503, "modelo_indisponivel"),
    (ModeloIndisponivelError("biblioteca"), 503, "modelo_indisponivel"),
    (ModeloTimeoutError(30), 504, "modelo_timeout"),
    (ModeloOcupadoError(), 429, "modelo_ocupado"),
    (ModeloFalhaError(detalhe="x"), 502, "modelo_falhou"),
    (RespostaVaziaError(), 502, "resposta_vazia"),
])
def test_erros_da_ia_viram_http_adequado_e_dizem_que_e_a_ia(container, erro, status, codigo):
    container.processar_noticia._modelo = ModeloFake(erro=erro)
    r = processar(cliente(container))
    j = r.json()
    assert r.status_code == status and j["codigo"] == codigo and j["categoria"] == "ia"
    assert "IA" in j["mensagem"] and "Qwen3-4B-Instruct-2507" in j["mensagem"] and j["sugestao"]


def test_erro_inesperado_vira_500_amigavel_sem_vazar_detalhes(container):
    container.processar_noticia._modelo = ModeloFake(erro=RuntimeError("SEGREDO interno /home/x"))
    r = processar(cliente(container))
    j = r.json()
    assert r.status_code == 500 and j["codigo"] == "erro_interno" and "SEGREDO" not in r.text and "Traceback" not in r.text
    assert re.fullmatch(r"[0-9a-f]{8}", j["detalhe"]) and j["detalhe"] in j["sugestao"]


# --------------------------------------------------------------- demais rotas
def test_infodengue_get_com_filtros(api):
    j = api.get("/infodengue").json()
    assert j["origem"] == "amostra_local" and j["total"] == 6   # o container de teste usa a amostra local
    assert api.get("/infodengue?se_inicio=202604&nivel=3&nivel=4").json()["total"] == 2
    assert api.get("/infodengue?se_inicio=abc").status_code == 422


def test_infodengue_post_adiciona_ignora_repetidos_e_valida(api):
    primeiro = api.get("/infodengue").json()["dados"][0]["id"]
    r = api.post("/infodengue", json=[{"id": 99, "SE": 202699, "nivel": 4, "extra": "ok"}, {"id": primeiro, "SE": 1, "nivel": 1}])
    assert r.json() == {"adicionadas": 1, "ignoradas_por_id_repetido": 1, "total": 7}
    assert api.get("/infodengue?nivel=4").json()["total"] == 2
    ruim = api.post("/infodengue", json=[{"id": "z", "SE": 1, "nivel": 9}])
    assert ruim.status_code == 422 and "registro 1, campo 'nivel'" in ruim.json()["mensagem"]
    assert api.post("/infodengue", json=[]).status_code == 422
    assert api.post("/infodengue", json=[{"SE": 1, "nivel": 1}]).json()["mensagem"].count("obrigatório") == 1


def test_infodengue_delete_descarta_o_que_foi_enviado(api):
    api.post("/infodengue", json=[{"id": "n1", "SE": 202650, "nivel": 3}])
    assert api.delete("/infodengue/uploads").status_code == 204
    assert api.get("/infodengue").json()["total"] == 6


def test_noticias_lista_busca_texto_e_detalhe(api):
    assert api.get("/noticias").json()["total"] == 2
    assert api.get("/noticias?busca=zera").json()["noticias"][0]["id"] == 1
    assert api.get("/noticias?limit=0").status_code == 422
    t = api.get("/noticias/texto").json()
    assert t["total_noticias"] == 2 and "Wolbachia" in t["texto"] and "cookies" not in t["texto"]
    assert api.get("/noticias/1").json()["autor"] == "Ana" and api.get("/noticias/9").status_code == 404


def test_rota_inexistente_e_metodo_errado_sao_amigaveis(api):
    r = api.get("/nada")
    assert r.status_code == 404 and r.json()["codigo"] == "rota_inexistente" and "/docs" in r.json()["sugestao"]
    assert api.put("/noticias").json()["codigo"] == "metodo_nao_permitido"


def test_openapi_documenta_rota_de_ia_e_erros(api):
    op = api.get("/openapi.json").json()["paths"]["/noticias/{noticia_id}/processar"]["post"]
    assert {"200", "404", "422", "429", "502", "503", "504"} <= set(op["responses"])
