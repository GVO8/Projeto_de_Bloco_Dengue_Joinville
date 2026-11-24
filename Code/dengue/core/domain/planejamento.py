"""Planejamento determinístico da consulta e leitura tolerante do plano gerado pelo modelo."""

from __future__ import annotations

import json
import re

from dengue.core.domain.chat import ANO_MINIMO_VALIDO, JANELA_HISTORICA_ANOS, PlanoConsulta
from dengue.core.domain.escopo import normalizar

_RE_ANO = re.compile(r"\b(20\d{2})\b")
_RE_ANO_PASSADO = re.compile(r"\b(ano passado|ano anterior|ultimo ano)\b")
_RE_ANO_RETRASADO = re.compile(r"\bano retrasado\b")
_RE_ESTE_ANO = re.compile(r"\b(este ano|neste ano|esse ano|nesse ano|ano atual|ano corrente)\b")
_RE_RANKING = re.compile(r"(qual (foi )?o ano|em que ano|ano com (mais|menos)|ano (mais|menos)|anos? (de|com) (maior|menor)|historic)")
_RE_COMPARACAO = re.compile(r"(em relacao|compar|versus|\bvs\b|subiram|diminuiram|aumentaram|cairam|cresceram|reduziram|aumento|queda|subiu|caiu|diminuiu|aumentou)")
_RE_MENOS = re.compile(r"\b(menos|menor|minimo)\b")
_RE_PICO = re.compile(r"\b(pico|maior numero|semana com mais|recorde)\b")

INTENCOES = ("pico", "ano_mais_casos", "ano_menos_casos", "comparar_anos", "total", "outra")


def anos_explicitos(pergunta: str) -> list[int]:
    return sorted({int(a) for a in _RE_ANO.findall(pergunta)})


def planejar_por_regras(pergunta: str, ano_atual: int) -> PlanoConsulta:
    """Plano determinístico (usado como alternativa e para conferir o plano do modelo)."""
    t = normalizar(pergunta)
    anos = set(anos_explicitos(t))
    if _RE_ANO_PASSADO.search(t):
        anos.add(ano_atual - 1)
    if _RE_ANO_RETRASADO.search(t):
        anos.add(ano_atual - 2)
    if _RE_ESTE_ANO.search(t):
        anos.add(ano_atual)

    if _RE_RANKING.search(t):
        intencao = "ano_menos_casos" if _RE_MENOS.search(t) else "ano_mais_casos"
        inicio, fim = ano_atual - JANELA_HISTORICA_ANOS + 1, ano_atual
        if anos:
            inicio = min(inicio, min(anos))
    elif _RE_COMPARACAO.search(t):
        intencao = "comparar_anos"
        base = anos or {ano_atual}
        inicio, fim = min(min(base), ano_atual - 1), max(base)
        if len(anos) < 2:
            fim = max(fim, ano_atual)
    else:
        intencao = "pico" if _RE_PICO.search(t) else "total"
        if anos:
            inicio, fim = min(anos), max(anos)
        else:
            inicio, fim = ano_atual - 1, ano_atual
    return PlanoConsulta(intencao, int(inicio), int(fim), "regras")


def extrair_json(texto: str) -> dict | None:
    """Lê um objeto JSON da saída do modelo, tolerando cercas de código e texto ao redor."""
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?|```$", "", texto, flags=re.MULTILINE).strip()
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio < 0 or fim <= inicio:
        return None
    try:
        dado = json.loads(texto[inicio : fim + 1])
    except json.JSONDecodeError:
        return None
    return dado if isinstance(dado, dict) else None


def _como_ano(valor) -> int | None:
    if isinstance(valor, bool):
        return None
    try:
        return int(valor) if valor is not None else None
    except (TypeError, ValueError):
        return None


def interpretar_plano_do_modelo(dado: dict | None, pergunta: str, ano_atual: int) -> tuple[dict, PlanoConsulta] | None:
    """
    Valida o JSON do modelo e o reconcilia com as regras: anos escritos na pergunta sempre entram na consulta.
    Retorna (sinais, plano) ou None se o JSON não servir (então o chamador usa as regras).
    """
    if not dado or "assunto_valido" not in dado:
        return None
    regras = planejar_por_regras(pergunta, ano_atual)
    inicio, fim = _como_ano(dado.get("ano_inicio")), _como_ano(dado.get("ano_fim"))
    intencao = dado.get("intencao") if dado.get("intencao") in INTENCOES else regras.intencao
    if inicio is None and fim is None:
        inicio, fim = regras.ano_inicio, regras.ano_fim
    inicio, fim = (inicio if inicio is not None else fim), (fim if fim is not None else inicio)
    if inicio > fim:
        inicio, fim = fim, inicio
    explicitos = anos_explicitos(pergunta)
    if explicitos:
        inicio, fim = min(inicio, min(explicitos)), max(fim, max(explicitos))
    if intencao in ("ano_mais_casos", "ano_menos_casos"):
        inicio = min(inicio, ano_atual - JANELA_HISTORICA_ANOS + 1)
    sinais = {"assunto_valido": bool(dado.get("assunto_valido")), "cidade": str(dado.get("cidade", "nao_citada")).lower()}
    return sinais, PlanoConsulta(str(intencao), inicio, fim, "ia")


def periodo_valido(plano: PlanoConsulta, ano_atual: int) -> bool:
    return ANO_MINIMO_VALIDO <= plano.ano_inicio <= plano.ano_fim <= ano_atual
