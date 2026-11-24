"""
Guarda de escopo da conversa: só casos de dengue, só Joinville.

Camada 1 (esta, determinística e sem custo): bloqueia o que é claramente de fora — outras cidades,
outros territórios, assuntos sem relação com dengue e tentativas de alterar as regras.
Camada 2: o plano gerado pelo modelo também sinaliza assunto/cidade (ver ConversarComDados).
Camada 3: a resposta é construída só a partir dos dados do InfoDengue de Joinville.
"""

from __future__ import annotations

import re
import unicodedata
from enum import Enum

from dengue.core.domain.chat import MUNICIPIO, PERGUNTAS_EXEMPLO


class MotivoRecusa(str, Enum):
    OUTRA_CIDADE = "outra_cidade"
    OUTRO_TERRITORIO = "outro_territorio"
    OUTRO_ASSUNTO = "outro_assunto"
    TENTATIVA_DE_ALTERAR_REGRAS = "tentativa_de_alterar_regras"
    PERIODO_SEM_DADOS = "periodo_sem_dados"


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")


_CIDADES = (
    "sao paulo|rio de janeiro|belo horizonte|brasilia|salvador|fortaleza|recife|porto alegre|curitiba|manaus|belem|"
    "goiania|florianopolis|blumenau|itajai|chapeco|criciuma|jaragua do sul|sao jose|palhoca|balneario camboriu|"
    "camboriu|lages|brusque|sao bento do sul|gaspar|indaial|navegantes|tubarao|rio do sul|mafra|canoinhas|"
    "sao francisco do sul|guaramirim|schroeder|araquari|itapoa|campinas|santos|guarulhos|niteroi|vitoria|natal|"
    "joao pessoa|maceio|aracaju|teresina|sao luis|cuiaba|campo grande|porto velho|rio branco|macapa|boa vista|"
    "palmas|londrina|maringa|cascavel|ribeirao preto|uberlandia|sorocaba|osasco|foz do iguacu|ponta grossa"
)
_RE_CIDADES = re.compile(rf"\b({_CIDADES})\b")
_RE_TERRITORIOS = re.compile(r"\b(brasil|pais|mundo|mundial|nacional|estadual|estados|santa catarina|regiao sul|america|europa)\b")
_RE_INJECAO = re.compile(
    r"(ignore (as|todas|tudo|suas)|esqueca (as|tudo|suas)|desconsidere (as|tudo)|system prompt|prompt do sistema|"
    r"voce agora e|finja (que|ser)|aja como|novas instrucoes|jailbreak)"
)
_STEMS_DOMINIO = (
    "dengue", "caso", "pico", "ano", "semana", "epidem", "surto", "alerta", "nivel", "incidencia", "aument", "dimin",
    "subi", "cai", "cresc", "reduz", "maior", "menor", "mais", "menos", "total", "media", "notific", "joinville",
    "mosquito", "aedes", "numero", "quant", "quando", "compar", "passado", "anterior", "tendencia", "situacao",
    "obito", "morte", "mes", "recorde", "pior", "melhor",
)
_RE_ANO = re.compile(r"\b(20\d{2})\b")
_RE_CONTINUACAO = re.compile(r"\b(tambem|mesmo|mesma|isso|esse|essa|entao|anterior|passado|antes|depois)\b")


def avaliar_escopo(pergunta: str, tem_historico: bool = False) -> MotivoRecusa | None:
    """Devolve o motivo da recusa, ou None se a pergunta pode seguir para a próxima camada."""
    t = normalizar(pergunta)
    if _RE_INJECAO.search(t):
        return MotivoRecusa.TENTATIVA_DE_ALTERAR_REGRAS
    if _RE_CIDADES.search(t):
        return MotivoRecusa.OUTRA_CIDADE
    if _RE_TERRITORIOS.search(t):
        return MotivoRecusa.OUTRO_TERRITORIO
    palavras = t.split()
    if _RE_ANO.search(t) or any(p.startswith(s) for p in palavras for s in _STEMS_DOMINIO):
        return None
    if tem_historico and len(palavras) <= 10 and (palavras[0] == "e" or _RE_CONTINUACAO.search(t)):
        return None                                # continuação de uma conversa ("e em 2024?")
    return MotivoRecusa.OUTRO_ASSUNTO


_EXPLICACOES = {
    MotivoRecusa.OUTRA_CIDADE: "Esta conversa trata apenas de Joinville; não posso consultar outras cidades.",
    MotivoRecusa.OUTRO_TERRITORIO: "Esta conversa trata apenas de Joinville; não tenho dados do estado, do país ou de outras regiões.",
    MotivoRecusa.OUTRO_ASSUNTO: "Só respondo sobre casos de dengue; não posso ajudar com outros assuntos.",
    MotivoRecusa.TENTATIVA_DE_ALTERAR_REGRAS: "Não posso alterar as regras desta conversa: só trato de casos de dengue em Joinville.",
    MotivoRecusa.PERIODO_SEM_DADOS: "Não tenho dados para esse período.",
}


def mensagem_recusa(motivo: MotivoRecusa, detalhe: str = "") -> str:
    exemplos = "\n".join(f"- {e}" for e in PERGUNTAS_EXEMPLO)
    extra = f" {detalhe}" if detalhe else ""
    return (
        f"{_EXPLICACOES[motivo]}{extra}\n\n"
        f"Posso responder perguntas sobre **casos de dengue em {MUNICIPIO}**, usando os dados do InfoDengue. Por exemplo:\n{exemplos}"
    )
