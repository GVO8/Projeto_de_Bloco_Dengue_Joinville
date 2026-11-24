"""Memória conversacional em RAM (por sessão). Perde-se ao reiniciar a API — por design, sem dados pessoais em disco."""

from __future__ import annotations

import threading
from collections import OrderedDict

from dengue.core.domain.chat import Turno
from dengue.core.ports.repositorios import RepositorioConversas


class ConversasEmMemoria(RepositorioConversas):
    def __init__(self, max_sessoes: int = 200, max_turnos: int = 20):
        self._max_sessoes, self._max_turnos = max_sessoes, max_turnos
        self._dados: OrderedDict[str, list[Turno]] = OrderedDict()
        self._lock = threading.Lock()

    def obter(self, sessao_id: str) -> list[Turno]:
        with self._lock:
            return list(self._dados.get(sessao_id, []))

    def existe(self, sessao_id: str) -> bool:
        with self._lock:
            return sessao_id in self._dados

    def adicionar(self, sessao_id: str, turno: Turno) -> None:
        with self._lock:
            turnos = self._dados.setdefault(sessao_id, [])
            turnos.append(turno)
            del turnos[: -self._max_turnos]                # mantém só os mais recentes
            self._dados.move_to_end(sessao_id)
            while len(self._dados) > self._max_sessoes:    # descarta a sessão menos recente
                self._dados.popitem(last=False)

    def limpar(self, sessao_id: str) -> None:
        with self._lock:
            self._dados.pop(sessao_id, None)
