from dengue.core.domain.modelos import AVISO_PADRAO, ContextoNumerico, Operacao, RespostaProcessamento
from dengue.core.domain.texto import dividir_em_trechos, extrair_resumo_final, limitar_texto, limpar_paragrafos
from dengue.core.prompts import PROMPTS, montar_prompt


def test_limpar_remove_ruido_titulo_repetido_e_manchetes():
    longo = "Esta é uma frase completa e longa o bastante para ser mantida no corpo da notícia, com pontuação final correta e bem mais de cento e quarenta caracteres no total."
    entrada = ["Título", "© 2026 NSC Total. Todos os direitos reservados.", "Este site usa cookies para fornecer serviços",
               "Entre na comunidade exclusiva de colunistas", "Cidade litorânea de SC leiloa terrenos", "A", longo,
               "Frase curta, mas com ponto final.", "Foto legenda (foto: Arquivo Pessoal)"]
    assert limpar_paragrafos(entrada, titulo="Título") == [longo, "Frase curta, mas com ponto final."]


def test_dividir_em_trechos_respeita_limite():
    paragrafos = ["a" * 500, "b" * 500, "c" * 100]
    trechos = dividir_em_trechos(paragrafos, max_chars=800)
    assert len(trechos) == 2 and all(len(t) <= 800 for t in trechos)
    assert dividir_em_trechos([]) == []


def test_limitar_texto_corta_em_fronteira_de_frase():
    texto = "Primeira frase longa. " * 50
    cortado, truncado = limitar_texto(texto, 100)
    assert truncado and cortado.endswith(".") and len(cortado) <= 100
    assert limitar_texto("curto", 100) == ("curto", False)


def test_resumo_final_sentimento_extrai_classe():
    assert extrair_resumo_final(Operacao.SENTIMENTO, "Positivo. A queda de mortes é boa.") == "Sentimento: POSITIVO"
    assert extrair_resumo_final(Operacao.SENTIMENTO, "não sei dizer") == "Sentimento: NÃO CLASSIFICADO"


def test_resumo_final_usa_primeira_frase_e_trunca():
    assert extrair_resumo_final(Operacao.RESUMO, "Primeira frase.  Segunda frase.") == "Primeira frase."
    longo = "palavra " * 100
    r = extrair_resumo_final(Operacao.QA, longo, limite=50)
    assert len(r) <= 50 and r.endswith("…")


def test_markdown_ordem_e_aviso_no_final():
    r = RespostaProcessamento(1, "Título X", Operacao.RESUMO, "Resultado Y.", "Resumo Z.", "modelo", 1.0, ("Aviso W",))
    md = r.para_markdown()
    ordem = [md.index(p) for p in ("Título X", "Operação:", "Resultado Y.", "Resumo final:", "Aviso W", AVISO_PADRAO)]
    assert ordem == sorted(ordem)
    assert md.rstrip().endswith(f"{AVISO_PADRAO}_")


def test_contexto_marca_dados_sinteticos():
    c = ContextoNumerico("Joinville", "amostra_local", 52, {"1": 10, "2": 42}, 100, {"SE": 202610, "casos": 9})
    assert c.como_texto().startswith("ATENÇÃO: dados de exemplo")
    assert "pico na semana 202610" in c.como_texto()
    assert not ContextoNumerico.de_dict({**c.como_dict(), "origem_dados": "api"}).dados_sinteticos


def test_todos_os_prompts_montam_com_seus_campos():
    campos = {"titulo": "T", "texto": "X", "resumo": "R", "contexto_numerico": "C", "trechos": "TR", "pergunta": "P", "titulos": "TT"}
    for chave in PROMPTS:
        assert montar_prompt(chave, **campos)
    assert {o.value for o in Operacao} == set(PROMPTS)
    assert Operacao.QA.exige_pergunta and not Operacao.RESUMO.exige_pergunta
