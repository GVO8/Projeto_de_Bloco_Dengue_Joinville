"""
Erros de domínio com mensagens pensadas para o usuário final.

Cada erro carrega: o que aconteceu (`mensagem`), o que o usuário pode fazer
(`sugestao`), uma categoria (`entrada`, `dados`, `ia`, `sistema`) e o status
HTTP sugerido. Os adaptadores de entrada (API, UI) apenas traduzem isso para
o seu protocolo; não inventam mensagens.
"""

from __future__ import annotations

NOME_MODELO_PADRAO = "Qwen3-4B-Instruct-2507"


class ErroDengue(Exception):
    codigo = "erro_interno"
    categoria = "sistema"
    status_http = 500

    def __init__(self, mensagem: str, sugestao: str = "", *, detalhe: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.sugestao = sugestao
        self.detalhe = detalhe

    def como_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "categoria": self.categoria,
            "mensagem": self.mensagem,
            "sugestao": self.sugestao,
            "detalhe": self.detalhe,
        }


# --------------------------- entrada do usuário ---------------------------
class EntradaInvalidaError(ErroDengue):
    codigo, categoria, status_http = "entrada_invalida", "entrada", 422


class OperacaoInvalidaError(EntradaInvalidaError):
    codigo = "operacao_invalida"

    def __init__(self, operacao: str, validas: list[str]):
        super().__init__(
            f"A operação '{operacao}' não existe.",
            f"Escolha uma destas operações: {', '.join(validas)}.",
        )


class PerguntaObrigatoriaError(EntradaInvalidaError):
    codigo = "pergunta_obrigatoria"

    def __init__(self, maximo: int = 500):
        super().__init__(
            "Para perguntar algo sobre a notícia é preciso escrever a pergunta.",
            f"Digite sua pergunta (até {maximo} caracteres) e clique novamente.",
        )


# --------------------------------- dados ---------------------------------
class NoticiaNaoEncontradaError(ErroDengue):
    codigo, categoria, status_http = "noticia_nao_encontrada", "dados", 404

    def __init__(self, noticia_id: int):
        super().__init__(
            f"Não encontramos a notícia de id {noticia_id}.",
            "Atualize a lista de notícias e escolha uma que apareça nela. "
            "Se a lista estiver vazia, rode: python Code/cli.py coletar-noticias",
        )


class CorpusIndisponivelError(ErroDengue):
    codigo, categoria, status_http = "corpus_indisponivel", "dados", 503

    def __init__(self, detalhe: str | None = None):
        super().__init__(
            "Os textos das notícias ainda não foram preparados para a IA.",
            "Rode no terminal: python Code/cli.py coletar-noticias "
            "(ou, se já tiver as notícias, python Code/cli.py gerar-corpus) e tente de novo.",
            detalhe=detalhe,
        )


class ColetaError(ErroDengue):
    codigo, categoria, status_http = "falha_na_coleta", "dados", 502

    def __init__(self, detalhe: str | None = None):
        super().__init__(
            "Não foi possível coletar as notícias do site agora.",
            "Verifique sua conexão com a internet e tente novamente em alguns minutos. "
            "O site pode estar fora do ar ou ter mudado de estrutura.",
            detalhe=detalhe,
        )


# ------------------------------ IA / modelo ------------------------------
class ErroDeIA(ErroDengue):
    """Qualquer problema com o modelo de linguagem (categoria `ia`)."""

    categoria = "ia"

    def __init__(self, mensagem: str, sugestao: str, *, modelo: str = NOME_MODELO_PADRAO, detalhe: str | None = None):
        super().__init__(
            f"Houve um problema com a IA (modelo {modelo}): {mensagem}", sugestao, detalhe=detalhe
        )
        self.modelo = modelo


class ModeloIndisponivelError(ErroDeIA):
    codigo, status_http = "modelo_indisponivel", 503

    SUGESTOES = {
        "arquivo_ausente": (
            "o arquivo do modelo ainda não foi baixado para este computador.",
            "Rode uma vez, com internet: python Code/cli.py baixar-modelo (≈2,5 GB) e tente novamente.",
        ),
        "biblioteca": (
            "a biblioteca que executa o modelo (llama-cpp-python) não está instalada neste ambiente.",
            "Use um ambiente com Python 3.12 e instale: pip install -r requirements-llm.txt "
            "(no Python 3.14 não existe versão pronta dessa biblioteca).",
        ),
        "carga": (
            "o modelo não pôde ser carregado, provavelmente por falta de memória ou arquivo corrompido.",
            "Feche outros programas e tente de novo. Se persistir, apague o arquivo em Models/ "
            "e rode python Code/cli.py baixar-modelo.",
        ),
        "download": (
            "não foi possível baixar o modelo do Hugging Face.",
            "Verifique a conexão com a internet e o espaço livre em disco (≈2,5 GB) e tente de novo.",
        ),
    }

    def __init__(self, motivo: str, *, modelo: str = NOME_MODELO_PADRAO, detalhe: str | None = None):
        o_que, o_que_fazer = self.SUGESTOES.get(motivo, ("o modelo não está disponível.", "Tente novamente."))
        super().__init__(o_que, o_que_fazer, modelo=modelo, detalhe=detalhe)
        self.motivo = motivo


class ModeloOcupadoError(ErroDeIA):
    codigo, status_http = "modelo_ocupado", 429

    def __init__(self, *, modelo: str = NOME_MODELO_PADRAO):
        super().__init__(
            "a IA ainda está respondendo a outra solicitação.",
            "Aguarde a resposta atual terminar (em computadores sem placa de vídeo isso pode levar alguns minutos) e clique de novo.",
            modelo=modelo,
        )


class ModeloTimeoutError(ErroDeIA):
    codigo, status_http = "modelo_timeout", 504

    def __init__(self, limite_s: float, *, modelo: str = NOME_MODELO_PADRAO):
        super().__init__(
            f"a resposta passou do tempo limite de {limite_s:.0f} segundos.",
            "Tente uma notícia menor ou uma operação mais curta (como o sentimento). "
            "Se o seu computador for lento, aumente DENGUE_LLM_TIMEOUT_S ou use a placa de vídeo (DENGUE_LLM_GPU_LAYERS).",
            modelo=modelo,
        )


class ModeloFalhaError(ErroDeIA):
    codigo, status_http = "modelo_falhou", 502

    def __init__(self, *, modelo: str = NOME_MODELO_PADRAO, detalhe: str | None = None):
        super().__init__(
            "o modelo falhou ao gerar a resposta.",
            "Tente de novo. Se o erro se repetir, reinicie a API e confira se há memória livre no computador.",
            modelo=modelo,
            detalhe=detalhe,
        )


class RespostaVaziaError(ErroDeIA):
    codigo, status_http = "resposta_vazia", 502

    def __init__(self, *, modelo: str = NOME_MODELO_PADRAO):
        super().__init__(
            "o modelo não devolveu nenhum texto.",
            "Tente novamente; se possível, reformule a pergunta ou escolha outra operação.",
            modelo=modelo,
        )


# --------------------------- conversa com os dados ---------------------------
class PerguntaInvalidaError(EntradaInvalidaError):
    codigo = "pergunta_invalida"

    def __init__(self, motivo: str):
        super().__init__(motivo, "Escreva uma pergunta curta (até 300 caracteres) sobre casos de dengue em Joinville.")


class SessaoNaoEncontradaError(ErroDengue):
    codigo, categoria, status_http = "sessao_nao_encontrada", "dados", 404

    def __init__(self, sessao_id: str):
        super().__init__(
            "Não existe uma conversa com esse identificador (ela pode ter sido encerrada ou a API reiniciada).",
            "Inicie uma nova conversa enviando uma pergunta sem informar o identificador.",
            detalhe=sessao_id,
        )


class InfoDengueIndisponivelError(ErroDengue):
    codigo, categoria, status_http = "infodengue_indisponivel", "dados", 503

    def __init__(self, detalhe: str | None = None):
        super().__init__(
            "Não foi possível consultar o InfoDengue agora.",
            "Verifique sua conexão com a internet e tente de novo em instantes. O serviço do InfoDengue também pode estar fora do ar.",
            detalhe=detalhe,
        )


class ConsultaSemDadosError(ErroDengue):
    codigo, categoria, status_http = "consulta_sem_dados", "dados", 404

    def __init__(self, ano_inicio: int | None = None, ano_fim: int | None = None, detalhe: str | None = None):
        periodo = f" para {ano_inicio}–{ano_fim}" if ano_inicio else ""
        super().__init__(
            f"O InfoDengue não devolveu dados de Joinville{periodo}.",
            "Tente outro período (ex.: o ano atual ou o anterior).",
            detalhe=detalhe,
        )


# --------------------------- cliente da API (UI) ---------------------------
class ApiIndisponivelError(ErroDengue):
    codigo, categoria, status_http = "api_indisponivel", "sistema", 503

    def __init__(self, url: str = ""):
        super().__init__(
            "O aplicativo não conseguiu falar com a API.",
            "Abra outro terminal na pasta do projeto e rode: python Code/run_api.py — depois tente de novo.",
            detalhe=url or None,
        )


class ErroRemoto(ErroDengue):
    """Erro devolvido pela API e repassado à interface sem perder as mensagens."""

    def __init__(self, payload: dict, status_http: int):
        super().__init__(
            payload.get("mensagem", "A API devolveu um erro."),
            payload.get("sugestao", ""),
            detalhe=payload.get("detalhe"),
        )
        self.codigo = payload.get("codigo", "erro_remoto")
        self.categoria = payload.get("categoria", "sistema")
        self.status_http = status_http
