"""
Cálculo determinístico dos fatos sobre a série semanal do InfoDengue.

Os números são calculados aqui (pandas), nunca pelo modelo de linguagem: o modelo só redige a resposta a partir
dos fatos. Isso evita erros de aritmética e deixa cada número auditável.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from dengue.core.domain.chat import MUNICIPIO
from dengue.core.domain.erros import ConsultaSemDadosError, ErroDengue


class DadosInfoDengueInvalidosError(ErroDengue):
    codigo, categoria, status_http = "dados_infodengue_invalidos", "dados", 502

    def __init__(self, detalhe: str):
        super().__init__(
            "O InfoDengue devolveu dados em um formato que o aplicativo não reconhece.",
            "Tente novamente mais tarde. Se persistir, o formato da API pode ter mudado.",
            detalhe=detalhe,
        )


@dataclass(frozen=True)
class FatosDengue:
    texto: str            # versão para o modelo de linguagem
    estruturado: dict     # versão JSON-safe, para o painel


def _int(v) -> int:
    return int(round(float(v)))


def fmt(n: int | float) -> str:
    return f"{_int(n):,}".replace(",", ".")


def _data(valor) -> str | None:
    d = pd.to_datetime(valor, errors="coerce")
    return None if pd.isna(d) else d.strftime("%d/%m/%Y")


def _pico(linhas: pd.DataFrame) -> dict:
    r = linhas.loc[linhas["casos"].idxmax()]
    return {"se": _int(r["SE"]), "casos": _int(r["casos"]), "data": _data(r["data_iniSE"]) if "data_iniSE" in linhas else None}


def calcular_fatos(df: pd.DataFrame, ano_atual: int) -> FatosDengue:
    faltando = {"SE", "casos"} - set(df.columns)
    if faltando:
        raise DadosInfoDengueInvalidosError(f"colunas ausentes: {', '.join(sorted(faltando))}")
    d = df.copy()
    d["SE"] = pd.to_numeric(d["SE"], errors="coerce")
    d["casos"] = pd.to_numeric(d["casos"], errors="coerce")
    d = d.dropna(subset=["SE", "casos"]).sort_values("SE").reset_index(drop=True)
    if d.empty:
        raise ConsultaSemDadosError()
    d["ano"], d["semana"] = (d["SE"] // 100).astype(int), (d["SE"] % 100).astype(int)

    por_ano = []
    for ano, g in d.groupby("ano"):
        por_ano.append({
            "ano": int(ano), "total": _int(g["casos"].sum()), "semanas": int(len(g)), "ultima_semana": int(g["semana"].max()),
            "completo": bool(len(g) >= 52 and ano < ano_atual), "pico": _pico(g),
        })
    completos = [a for a in por_ano if a["completo"]]
    mais = max(completos, key=lambda a: a["total"]) if completos else None
    menos = min(completos, key=lambda a: a["total"]) if completos else None

    comparacao = None
    ultimo = por_ano[-1]
    anterior = next((a for a in por_ano if a["ano"] == ultimo["ano"] - 1), None)
    if anterior is not None:
        ate = ultimo["ultima_semana"]
        casos_ant = _int(d[(d["ano"] == anterior["ano"]) & (d["semana"] <= ate)]["casos"].sum())
        dif = ultimo["total"] - casos_ant
        pct = None if casos_ant == 0 else round(100 * dif / casos_ant, 1)
        comparacao = {
            "ano_atual": ultimo["ano"], "ano_anterior": anterior["ano"], "ate_semana": ate, "casos_atual": ultimo["total"],
            "casos_anterior": casos_ant, "variacao_abs": dif, "variacao_pct": pct,
            "direcao": "aumento" if dif > 0 else "queda" if dif < 0 else "estável",
        }

    ult = d.iloc[-1]
    ultima_semana = {"se": _int(ult["SE"]), "casos": _int(ult["casos"]),
                     "nivel": _int(ult["nivel"]) if "nivel" in d and pd.notna(ult.get("nivel")) else None}
    estruturado = {
        "municipio": MUNICIPIO, "periodo": {"ano_inicio": por_ano[0]["ano"], "ano_fim": ultimo["ano"], "ultima_se": ultima_semana["se"]},
        "por_ano": por_ano, "pico_periodo": _pico(d), "ano_mais_casos": mais and {"ano": mais["ano"], "total": mais["total"]},
        "ano_menos_casos": menos and {"ano": menos["ano"], "total": menos["total"]}, "comparacao": comparacao, "ultima_semana": ultima_semana,
    }
    return FatosDengue(_como_texto(estruturado), estruturado)


def _como_texto(e: dict) -> str:
    p = e["periodo"]
    linhas = [
        f"Município: {e['municipio']}. Fonte: InfoDengue (casos notificados por semana epidemiológica; SE = AAAASS).",
        f"Período coberto: {p['ano_inicio']} a {p['ano_fim']} (último dado: SE {p['ultima_se']}). "
        "As últimas semanas podem ser revisadas pelo InfoDengue.",
        "Casos notificados por ano:",
    ]
    for a in e["por_ano"]:
        pico = a["pico"]
        quando = f" em {pico['data']}" if pico.get("data") else ""
        situacao = "ano completo" if a["completo"] else f"ano em andamento, até a SE {a['ultima_semana']}"
        linhas.append(f"- {a['ano']}: {fmt(a['total'])} casos ({situacao}); pico na SE {pico['se']}{quando} com {fmt(pico['casos'])} casos.")
    if e["ano_mais_casos"]:
        linhas.append(f"Ano com mais casos (entre os anos completos): {e['ano_mais_casos']['ano']} ({fmt(e['ano_mais_casos']['total'])} casos).")
        linhas.append(f"Ano com menos casos (entre os anos completos): {e['ano_menos_casos']['ano']} ({fmt(e['ano_menos_casos']['total'])} casos).")
    else:
        linhas.append("Não há ano completo no período consultado, então não é possível apontar o ano com mais ou menos casos.")
    pk = e["pico_periodo"]
    linhas.append(f"Pico de casos no período todo: SE {pk['se']}" + (f" ({pk['data']})" if pk.get("data") else "") + f" com {fmt(pk['casos'])} casos.")
    c = e["comparacao"]
    if c:
        pct = f" ({str(c['variacao_pct']).replace('.', ',')}%)" if c["variacao_pct"] is not None else ""
        linhas.append(
            f"Comparação {c['ano_atual']} x {c['ano_anterior']} nas mesmas semanas (1 a {c['ate_semana']}): {fmt(c['casos_atual'])} x "
            f"{fmt(c['casos_anterior'])} casos; {c['direcao']} de {fmt(abs(c['variacao_abs']))} casos{pct}."
        )
    else:
        linhas.append("Não há dados do ano anterior no período consultado para comparação.")
    return "\n".join(linhas)
