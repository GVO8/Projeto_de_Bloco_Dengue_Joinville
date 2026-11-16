import pandas as pd
import pytest

from dengue.adapters.outbound.llm_fake import ModeloFake
from dengue.core.domain.erros import (
    CorpusIndisponivelError, EntradaInvalidaError, ModeloTimeoutError, NoticiaNaoEncontradaError,
    OperacaoInvalidaError, PerguntaObrigatoriaError, ColetaError,
)
from dengue.core.domain.modelos import ArtigoColetado, Noticia, Operacao
from dengue.core.services.corpus import PrepararCorpus, calcular_contexto
from dengue.core.services.noticias import ColetarNoticias, ServicoNoticias
from dengue.core.services.processar_noticia import ProcessarNoticia
from dengue.core.services.serie_infodengue import ServicoSerieInfoDengue, filtrar, mesclar_por_id, validar_linhas

from dados import PARAGRAFO_A, PARAGRAFO_B, RUIDO
from fakes import ColetorFalso, CorpusMemoria, FonteFixa, NoticiasMemoria, UploadsMemoria


def serie_df():
    return pd.DataFrame({"id": [1, 2, 3], "SE": [202601, 202602, 202603], "nivel": [1, 2, 4], "casos": [1, 5, 9]})


# ------------------------------------------------------------- série
def test_mesclar_mantem_original_e_compara_id_como_texto():
    r = mesclar_por_id(serie_df(), pd.DataFrame({"id": ["2", "9"], "SE": [202602, 202609], "nivel": [4, 3]}))
    assert len(r) == 4 and r.loc[r["id"] == "2", "nivel"].iloc[0] == 2


def test_filtrar_por_semana_e_nivel():
    assert list(filtrar(serie_df(), 202602, None, [2, 4])["SE"]) == [202602, 202603]
    assert len(filtrar(serie_df())) == 3


@pytest.mark.parametrize("df,trecho", [
    (pd.DataFrame({"id": [1], "SE": [1]}), "nivel"),
    (pd.DataFrame({"id": [1], "SE": [1], "nivel": [9]}), "1 a 4"),
    (pd.DataFrame({"id": [1], "SE": [1], "nivel": ["x"]}), "1 a 4"),
    (pd.DataFrame({"id": [], "SE": [], "nivel": []}), "nenhuma linha"),
])
def test_validar_linhas_rejeita_com_mensagem_clara(df, trecho):
    with pytest.raises(EntradaInvalidaError) as e:
        validar_linhas(df)
    assert trecho in e.value.mensagem and e.value.sugestao


def test_servico_adicionar_persiste_so_o_que_nao_esta_na_base_e_reseta():
    uploads = UploadsMemoria()
    s = ServicoSerieInfoDengue(FonteFixa(serie_df()), uploads)
    r = s.adicionar(pd.DataFrame({"id": ["1", "novo"], "SE": [202601, 202650], "nivel": [3, 3]}))
    assert r == {"adicionadas": 1, "ignoradas_por_id_repetido": 1, "total": 4}
    assert list(uploads.df["id"]) == ["novo"]
    df, origem = s.obter(se_inicio=202650)
    assert list(df["id"]) == ["novo"] and origem == "api"
    s.resetar()
    assert len(s.obter()[0]) == 3


def test_servico_busca_a_base_uma_vez_so():
    fonte = FonteFixa(serie_df())
    s = ServicoSerieInfoDengue(fonte, UploadsMemoria())
    s.obter(); s.obter(); s.adicionar(pd.DataFrame({"id": ["z"], "SE": [1], "nivel": [1]}))
    assert fonte.chamadas == 1
    s.recarregar_base(); s.obter()
    assert fonte.chamadas == 2


# ------------------------------------------------------------ corpus
def _noticias():
    return NoticiasMemoria({
        1: (Noticia(1, "Título Um", "2026-01-01", "Ana", "u1", "Resumo um"), [PARAGRAFO_A, *RUIDO, PARAGRAFO_B]),
        2: (Noticia(2, "Título Dois", None, None, None, None), [PARAGRAFO_B]),
    })


def _processador(modelo=None, corpus=None, noticias=None, max_chars=8000):
    noticias, corpus = noticias or _noticias(), corpus or CorpusMemoria()
    serie = ServicoSerieInfoDengue(FonteFixa(serie_df(), "amostra_local"), UploadsMemoria())
    return ProcessarNoticia(corpus, PrepararCorpus(noticias, serie, corpus), noticias, modelo or ModeloFake("Resposta. Outra."), max_chars), corpus


def test_preparar_corpus_limpa_ruido_e_calcula_contexto():
    p, corpus = _processador()
    p._preparar.executar()
    texto = "\n".join(t.texto for t in corpus.trechos)
    assert not any(r in texto for r in RUIDO) and PARAGRAFO_A in texto
    assert corpus.contexto.casos_total == 15 and corpus.contexto.semana_pico == {"SE": 202603, "casos": 9}
    assert corpus.trechos[0].resumo == "Resumo um"


def test_calcular_contexto_sem_coluna_casos():
    c = calcular_contexto(pd.DataFrame({"nivel": [1, 1, 2]}), "api")
    assert c.casos_total is None and c.semanas_por_nivel == {"1": 2, "2": 1}


# ------------------------------------------------- ProcessarNoticia
@pytest.mark.parametrize("op,esperado_no_prompt", [
    (Operacao.RESUMO, "Resuma a notícia"), (Operacao.SENTIMENTO, "Classifique o sentimento"),
    (Operacao.RELATORIO, "boletim"),
])
def test_processar_monta_prompt_da_operacao(op, esperado_no_prompt):
    modelo = ModeloFake("Positivo. ok")
    p, _ = _processador(modelo)
    r = p.executar(1, op)
    assert esperado_no_prompt.lower() in modelo.chamadas[0]["prompt"].lower()
    assert modelo.chamadas[0]["max_tokens"] == op.max_tokens
    assert r.titulo == "Título Um" and r.operacao == op and r.modelo == modelo.nome


def test_processar_qa_inclui_pergunta_texto_e_contexto():
    modelo = ModeloFake("A resposta é zero. Mais.")
    p, _ = _processador(modelo)
    r = p.executar(1, "qa", "  Quantas mortes houve?  ")
    prompt = modelo.chamadas[0]["prompt"]
    assert "Quantas mortes houve?" in prompt and "83 óbitos" in prompt and "Contexto numérico" in prompt
    assert r.resumo_final == "A resposta é zero."


def test_processar_sentimento_usa_resumo_da_noticia_ou_inicio_do_texto():
    modelo = ModeloFake("NEGATIVO. x")
    p, _ = _processador(modelo)
    p.executar(1, "sentimento"); p.executar(2, "sentimento")
    assert "Resumo: Resumo um" in modelo.chamadas[0]["prompt"]
    assert "Wolbachia" in modelo.chamadas[1]["prompt"]  # sem resumo: cai no início do texto


def test_relatorio_lista_titulo_atual_primeiro_e_avisa_dados_sinteticos():
    modelo = ModeloFake("Boletim. ok")
    p, _ = _processador(modelo)
    r = p.executar(2, Operacao.RELATORIO)
    assert "Notícias recentes: Título Dois; Título Um" in modelo.chamadas[0]["prompt"]
    assert any("sintéticos" in a for a in r.avisos)
    assert not any("sintéticos" in a for a in p.executar(2, "resumo").avisos)


def test_processar_qa_exige_pergunta():
    p, _ = _processador()
    for vazia in (None, "", "   "):
        with pytest.raises(PerguntaObrigatoriaError):
            p.executar(1, "qa", vazia)


def test_processar_operacao_invalida_e_noticia_inexistente():
    p, _ = _processador()
    with pytest.raises(OperacaoInvalidaError) as e:
        p.executar(1, "traduzir")
    assert "resumo" in e.value.sugestao
    with pytest.raises(NoticiaNaoEncontradaError):
        p.executar(99, "resumo")


def test_processar_reconstroi_corpus_ausente_ou_desatualizado_uma_vez():
    corpus = CorpusMemoria()
    p, corpus = _processador(corpus=corpus)
    p.executar(1, "resumo"); assert corpus.salvamentos == 1          # corpus ausente
    p.executar(2, "resumo"); assert corpus.salvamentos == 1          # já cobre
    p._noticias.dados[3] = (Noticia(3, "Nova", None, None, None, None), [PARAGRAFO_A])
    p.executar(3, "resumo"); assert corpus.salvamentos == 2          # desatualizado


def test_processar_noticia_sem_texto_aproveitavel_vira_erro_de_corpus():
    noticias = NoticiasMemoria({1: (Noticia(1, "Só ruído"), [RUIDO[0], RUIDO[2]])})
    p, _ = _processador(noticias=noticias)
    with pytest.raises(CorpusIndisponivelError):
        p.executar(1, "resumo")


def test_processar_falha_ao_preparar_corpus_vira_erro_amigavel():
    class Quebrado(NoticiasMemoria):
        def paragrafos(self, i): raise OSError("disco cheio")
    p, _ = _processador(noticias=Quebrado(_noticias().dados))
    with pytest.raises(CorpusIndisponivelError) as e:
        p.executar(1, "resumo")
    assert "disco cheio" in e.value.detalhe


def test_processar_trunca_texto_longo_e_avisa():
    longo = ["Frase completa de teste que se repete bastante para ficar grande demais para o modelo. " * 8] * 6
    noticias = NoticiasMemoria({1: (Noticia(1, "Longa"), longo)})
    modelo = ModeloFake("ok. ok")
    p, _ = _processador(modelo, noticias=noticias, max_chars=600)
    r = p.executar(1, "resumo")
    assert any("só o início" in a for a in r.avisos) and len(modelo.chamadas[0]["prompt"]) < 1200


def test_processar_propaga_erros_da_ia_sem_mascarar():
    p, _ = _processador(ModeloFake(erro=ModeloTimeoutError(10)))
    with pytest.raises(ModeloTimeoutError):
        p.executar(1, "resumo")


def test_processar_remove_espacos_do_resultado_e_mede_tempo():
    r = _processador(ModeloFake("  \n Texto limpo.  \n"))[0].executar(1, "resumo")
    assert r.resultado == "Texto limpo." and r.tempo_segundos >= 0


# ------------------------------------------------------- notícias/coleta
def test_servico_noticias_listar_obter_e_nuvem():
    s = ServicoNoticias(_noticias())
    assert [n.id for n in s.listar("um")] == [1] and s.obter(2).titulo == "Título Dois"
    with pytest.raises(NoticiaNaoEncontradaError):
        s.obter(7)
    nuvem = s.texto_para_nuvem()
    assert "Wolbachia" in nuvem and not any(r in nuvem for r in RUIDO)


def test_coletar_noticias_salva_e_dispara_corpus():
    repo, chamadas = NoticiasMemoria(), []
    art = [ArtigoColetado("T", "u", "2026", "A", "R", PARAGRAFO_A)]
    assert ColetarNoticias(ColetorFalso(art), repo, lambda: chamadas.append(1)).executar() == 1
    assert chamadas == [1] and repo.obter(1).titulo == "T"


def test_coletar_sem_resultados_levanta_erro_amigavel():
    with pytest.raises(ColetaError) as e:
        ColetarNoticias(ColetorFalso([]), NoticiasMemoria()).executar()
    assert e.value.sugestao
