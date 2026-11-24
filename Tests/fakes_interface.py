"""Gateway falso para testes de página (camada de interface)."""
from __future__ import annotations

import pandas as pd

from dengue.adapters.inbound.ui_streamlit.gateways import Gateway


class GatewayFalso(Gateway):
    """Gateway de interface para testes de página; registra chamadas e permite simular erros."""

    def __init__(self, noticias=None, resposta=None, erro_ia: Exception | None = None, erro_chat: Exception | None = None,
                 erro_historico: Exception | None = None, sentimentos=None):
        self.noticias = noticias if noticias is not None else [
            {"id": 1, "titulo": "Joinville zera mortes por dengue", "data_publicacao": "2026-01-09T10:00:00",
             "autor": "Ana", "url": "https://exemplo.com/1", "resumo": "r"}]
        self.resposta, self.erro_ia, self.chamadas = resposta, erro_ia, []
        self.erro_chat, self.erro_historico = erro_chat, erro_historico
        self.sents = sentimentos if sentimentos is not None else pd.DataFrame()
        self.historico, self.fatos = historico_exemplo()
        self.resposta_chat = lambda sessao, pergunta: {
            "sessao_id": sessao or "sessao12345678", "pergunta": pergunta, "tipo": "resposta",
            "resposta": "O pico foi na SE 202614 com 120 casos.", "modelo": "FakeLLM", "tempo_segundos": 0.2,
            "plano": {"intencao": "pico", "ano_inicio": 2026, "ano_fim": 2026, "origem": "ia"},
            "requisicao": {"url": "https://info.dengue.mat.br/api/alertcity?x", "geocode": 4209102, "doenca": "dengue", "ano_inicio": 2026, "ano_fim": 2026},
            "fatos": "Município: Joinville/SC.", "avisos": [], "aviso_padrao": "⚠️ Este conteúdo foi gerado por um modelo de IA e pode conter erros.",
            "etapas": [{"nome": "planejamento", "tempo_segundos": 0.1, "tokens_gerados": 20}, {"nome": "resposta", "tempo_segundos": 0.1, "tokens_gerados": 30}]}
        self.serie = pd.DataFrame({"id": ["a", "b", "c"], "SE": [202601, 202602, 202603], "nivel": [1, 2, 3], "casos": [1, 2, 3]})

    def obter_infodengue(self, se_inicio=None, se_fim=None, niveis=None): return self.serie.copy(), "api"
    def enviar_infodengue(self, novo): self.chamadas.append(("enviar", len(novo))); return {"adicionadas": len(novo), "ignoradas_por_id_repetido": 0, "total": 9}, "api"
    def resetar_uploads(self): self.chamadas.append(("resetar",)); return "api"
    def listar_noticias(self, busca=None): return pd.DataFrame(self.noticias), "api"
    def texto_noticias(self): return "", "api"
    def historico_infodengue(self, ano_inicio=None, ano_fim=None):
        self.chamadas.append(("historico", ano_inicio, ano_fim))
        if self.erro_historico:
            raise self.erro_historico
        return {"serie": self.historico, "fatos": self.fatos, "requisicao": {"url": "http://infodengue/x"}, "canal": "api"}
    def sentimentos(self): return self.sents.copy()
    def perguntar(self, sessao_id, pergunta):
        self.chamadas.append(("perguntar", sessao_id, pergunta))
        if self.erro_chat:
            raise self.erro_chat
        return self.resposta_chat(sessao_id, pergunta)
    def encerrar_conversa(self, sessao_id): self.chamadas.append(("encerrar", sessao_id))
    def estado(self): return {"status": "ok", "modelo_ia": {"backend": "fake", "nome": "FakeLLM", "pronto": True, "carregado": True, "detalhe": ""}}

    def processar_noticia(self, noticia_id, operacao, pergunta=None):
        self.chamadas.append(("processar", noticia_id, operacao, pergunta))
        if self.erro_ia:
            raise self.erro_ia
        return self.resposta or {
            "markdown": f"### Joinville zera mortes por dengue\n\n**Operação:** {operacao}\n\n**Resultado:**\n\nTexto da IA.\n\n"
                        f"**Resumo final:** Texto da IA.\n\n_⚠️ Este conteúdo foi gerado por um modelo de IA e pode conter erros._",
            "modelo": "FakeLLM", "tempo_segundos": 0.1}


def historico_exemplo():
    """Série de 3 anos (2024–2026, o último incompleto) e os fatos correspondentes, calculados pelo próprio núcleo."""
    from dengue.core.services.fatos_dengue import calcular_fatos

    linhas = []
    for ano, semanas in ((2024, 52), (2025, 52), (2026, 40)):
        for w in range(1, semanas + 1):
            linhas.append({"SE": ano * 100 + w, "data_iniSE": f"{ano}-{min(w, 52):02d}-01" if False else pd.Timestamp(f"{ano}-01-01") + pd.Timedelta(weeks=w - 1),
                           "casos": (w * 3 + ano % 10) % 90, "nivel": 1 + w % 4})
    df = pd.DataFrame(linhas)
    serie = df.assign(ano=df["SE"] // 100, semana=df["SE"] % 100)
    return serie, calcular_fatos(df, 2026).estruturado
