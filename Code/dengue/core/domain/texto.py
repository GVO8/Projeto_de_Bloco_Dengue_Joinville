"""Regras puras de tratamento de texto (limpeza, trechos, resumo final)."""

from __future__ import annotations

import re

from dengue.core.domain.modelos import Operacao

# Linhas típicas de rodapé/menu/cookies que o scraper captura junto com o corpo
_RUIDO = re.compile(
    r"(©|todos os direitos|política de privacidade|este site usa cookies|"
    r"entre na comunidade|leia também|veja também|compartilhe|siga o nsc|"
    r"receba notícias|inscreva-se|\(foto:|\(imagem:|reprodução)",
    re.IGNORECASE,
)
_TERMINA_FRASE = re.compile(r"[.!?…:”\"')]\s*$")


def limpar_paragrafos(paragrafos: list[str], titulo: str = "") -> list[str]:
    """
    Remove ruído do texto raspado: rodapé, cookies, convites, legendas de foto,
    o título repetido e manchetes soltas (linhas curtas sem pontuação final,
    que costumam ser chamadas de outras matérias).
    """
    limpos = []
    for p in paragrafos:
        p = p.strip()
        if not p or p == titulo.strip():
            continue
        if _RUIDO.search(p):
            continue
        if len(p) < 140 and not _TERMINA_FRASE.search(p):
            continue
        limpos.append(p)
    return limpos


def dividir_em_trechos(paragrafos: list[str], max_chars: int = 800) -> list[str]:
    trechos, atual = [], ""
    for p in paragrafos:
        if atual and len(atual) + len(p) + 1 > max_chars:
            trechos.append(atual)
            atual = ""
        atual = f"{atual}\n{p}".strip()
    if atual:
        trechos.append(atual)
    return trechos


def limitar_texto(texto: str, max_chars: int) -> tuple[str, bool]:
    """Corta em fronteira de frase para caber na janela de contexto do modelo."""
    if len(texto) <= max_chars:
        return texto, False
    corte = texto[:max_chars]
    ultimo = max(corte.rfind(". "), corte.rfind(".\n"))
    if ultimo > max_chars * 0.5:
        corte = corte[: ultimo + 1]
    return corte, True


_CLASSE = re.compile(r"\b(POSITIVO|NEGATIVO|NEUTRO)\b", re.IGNORECASE)
_PRIMEIRA_FRASE = re.compile(r"(.+?[.!?])(\s|$)", re.DOTALL)


def extrair_resumo_final(operacao: Operacao, texto: str, limite: int = 220) -> str:
    """
    Pequeno resumo exibido junto do resultado: classe final (sentimento) ou a
    primeira frase (demais operações). Determinístico: não gasta outra chamada ao modelo.
    """
    texto = texto.strip()
    if operacao == Operacao.SENTIMENTO:
        m = _CLASSE.search(texto)
        return f"Sentimento: {m.group(1).upper()}" if m else "Sentimento: NÃO CLASSIFICADO"
    m = _PRIMEIRA_FRASE.match(" ".join(texto.split()))
    frase = m.group(1) if m else " ".join(texto.split())
    return frase if len(frase) <= limite else frase[: limite - 1].rstrip() + "…"
