"""Gateway falso para testes de página (camada de interface)."""
from __future__ import annotations

import pandas as pd

from dengue.adapters.inbound.ui_streamlit.gateways import Gateway


class GatewayFalso(Gateway):
    """Gateway de interface para testes de página; registra chamadas e permite simular erros."""

    def __init__(self, noticias=None, resposta=None, erro_ia: Exception | None = None):
        self.noticias = noticias if noticias is not None else [
            {"id": 1, "titulo": "Joinville zera mortes por dengue", "data_publicacao": "2026-01-09T10:00:00",
             "autor": "Ana", "url": "https://exemplo.com/1", "resumo": "r"}]
        self.resposta, self.erro_ia, self.chamadas = resposta, erro_ia, []
        self.serie = pd.DataFrame({"id": ["a", "b", "c"], "SE": [202601, 202602, 202603], "nivel": [1, 2, 3], "casos": [1, 2, 3]})

    def obter_infodengue(self, se_inicio=None, se_fim=None, niveis=None): return self.serie.copy(), "api"
    def enviar_infodengue(self, novo): self.chamadas.append(("enviar", len(novo))); return {"adicionadas": len(novo), "ignoradas_por_id_repetido": 0, "total": 9}, "api"
    def resetar_uploads(self): self.chamadas.append(("resetar",)); return "api"
    def listar_noticias(self, busca=None): return pd.DataFrame(self.noticias), "api"
    def texto_noticias(self): return "", "api"
    def estado(self): return {"status": "ok", "modelo_ia": {"backend": "fake", "nome": "FakeLLM", "pronto": True, "carregado": True, "detalhe": ""}}

    def processar_noticia(self, noticia_id, operacao, pergunta=None):
        self.chamadas.append(("processar", noticia_id, operacao, pergunta))
        if self.erro_ia:
            raise self.erro_ia
        return self.resposta or {
            "markdown": f"### Joinville zera mortes por dengue\n\n**Operação:** {operacao}\n\n**Resultado:**\n\nTexto da IA.\n\n"
                        f"**Resumo final:** Texto da IA.\n\n_⚠️ Este conteúdo foi gerado por um modelo de IA e pode conter erros._",
            "modelo": "FakeLLM", "tempo_segundos": 0.1}
