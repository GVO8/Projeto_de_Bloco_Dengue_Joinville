"""
Porta de saída da interface: tudo que as páginas precisam do "sistema".

- ApiGateway: fala com a API FastAPI por HTTP.
- LocalGateway: usa os casos de uso diretamente (sem API).
- GatewayComAlternativa: tenta a API e, se ela estiver fora do ar, usa o local. Só o processamento
  por IA exige a API (o modelo não é carregado dentro do processo da interface).
Cada método devolve (dados, canal) em que canal é 'api' ou 'local'.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd
import requests

from dengue.container import Container
from dengue.core.domain.erros import ApiIndisponivelError, ErroRemoto


class Gateway(ABC):
    @abstractmethod
    def obter_infodengue(self, se_inicio=None, se_fim=None, niveis=None) -> tuple[pd.DataFrame, str]: ...
    @abstractmethod
    def enviar_infodengue(self, novo: pd.DataFrame) -> tuple[dict, str]: ...
    @abstractmethod
    def resetar_uploads(self) -> str: ...
    @abstractmethod
    def listar_noticias(self, busca: str | None = None) -> tuple[pd.DataFrame, str]: ...
    @abstractmethod
    def texto_noticias(self) -> tuple[str, str]: ...
    @abstractmethod
    def processar_noticia(self, noticia_id: int, operacao: str, pergunta: str | None = None) -> dict: ...
    @abstractmethod
    def estado(self) -> dict: ...


class ApiGateway(Gateway):
    def __init__(self, url: str, http=requests, timeout_s: float = 5, timeout_ia_s: float = 900):
        self._url, self._http, self._timeout, self._timeout_ia = url.rstrip("/"), http, timeout_s, timeout_ia_s

    def _chamar(self, metodo: str, caminho: str, *, timeout: float | None = None, **kw) -> dict | None:
        try:
            r = self._http.request(metodo, f"{self._url}{caminho}", timeout=timeout or self._timeout, **kw)
        except (requests.ConnectionError, requests.Timeout) as exc:
            if isinstance(exc, requests.Timeout) and timeout == self._timeout_ia:
                raise ErroRemoto({"codigo": "tempo_esgotado", "categoria": "ia",
                                  "mensagem": "A IA demorou mais do que o esperado e o aplicativo parou de esperar.",
                                  "sugestao": "Tente uma operação mais curta ou aumente o tempo de espera (DENGUE_LLM_TIMEOUT_S)."}, 504) from exc
            raise ApiIndisponivelError(self._url) from exc
        if r.status_code >= 400:
            try:
                payload = r.json()
            except ValueError:
                payload = {"mensagem": f"A API respondeu com erro {r.status_code}.", "sugestao": "Tente novamente."}
            raise ErroRemoto(payload, r.status_code)
        return None if r.status_code == 204 else r.json()

    def obter_infodengue(self, se_inicio=None, se_fim=None, niveis=None):
        d = self._chamar("GET", "/infodengue", params={"se_inicio": se_inicio, "se_fim": se_fim, "nivel": niveis})
        return pd.DataFrame(d["dados"]), "api"

    def enviar_infodengue(self, novo):
        registros = novo.astype(object).where(pd.notna(novo), None).to_dict(orient="records")
        return self._chamar("POST", "/infodengue", json=registros, timeout=self._timeout * 3), "api"

    def resetar_uploads(self):
        self._chamar("DELETE", "/infodengue/uploads")
        return "api"

    def listar_noticias(self, busca=None):
        d = self._chamar("GET", "/noticias", params={"busca": busca, "limit": 200})
        return pd.DataFrame(d["noticias"]), "api"

    def texto_noticias(self):
        return self._chamar("GET", "/noticias/texto")["texto"], "api"

    def processar_noticia(self, noticia_id, operacao, pergunta=None):
        return self._chamar("POST", f"/noticias/{noticia_id}/processar", timeout=self._timeout_ia,
                            json={"operacao": operacao, "pergunta": pergunta})

    def estado(self):
        return self._chamar("GET", "/health")


class LocalGateway(Gateway):
    def __init__(self, container: Container):
        self._c = container

    def obter_infodengue(self, se_inicio=None, se_fim=None, niveis=None):
        df, _ = self._c.serie.obter(se_inicio, se_fim, niveis)
        return df, "local"

    def enviar_infodengue(self, novo):
        return self._c.serie.adicionar(novo), "local"

    def resetar_uploads(self):
        self._c.serie.resetar()
        return "local"

    def listar_noticias(self, busca=None):
        return pd.DataFrame([n.__dict__ for n in self._c.noticias.listar(busca)]), "local"

    def texto_noticias(self):
        return self._c.noticias.texto_para_nuvem(), "local"

    def processar_noticia(self, noticia_id, operacao, pergunta=None):
        raise ApiIndisponivelError(self._c.config.api_url)

    def estado(self):
        raise ApiIndisponivelError(self._c.config.api_url)


class GatewayComAlternativa(Gateway):
    def __init__(self, api: Gateway, local: Gateway):
        self._api, self._local = api, local

    def _tentar(self, nome: str, *args, **kw):
        try:
            return getattr(self._api, nome)(*args, **kw)
        except ApiIndisponivelError:
            return getattr(self._local, nome)(*args, **kw)

    def obter_infodengue(self, *a, **k): return self._tentar("obter_infodengue", *a, **k)
    def enviar_infodengue(self, *a, **k): return self._tentar("enviar_infodengue", *a, **k)
    def resetar_uploads(self): return self._tentar("resetar_uploads")
    def listar_noticias(self, *a, **k): return self._tentar("listar_noticias", *a, **k)
    def texto_noticias(self): return self._tentar("texto_noticias")
    def processar_noticia(self, *a, **k): return self._api.processar_noticia(*a, **k)  # só via API
    def estado(self): return self._api.estado()
