"""
Caso de uso: conversar em linguagem natural com os dados do InfoDengue (memória conversacional).

Fluxo: guarda de escopo → plano (IA, com alternativa por regras) → requisição ao InfoDengue → fatos calculados em código
→ resposta redigida pela IA só a partir dos fatos → turno guardado na memória da sessão.
"""

from __future__ import annotations

import re
import time
import uuid
from datetime import date

from dengue.core import prompts_chat
from dengue.core.domain.chat import (
    ANO_MINIMO_VALIDO, MAX_PERGUNTA, EtapaMedida, PlanoConsulta, RespostaChat, Turno,
)
from dengue.core.domain.erros import ConsultaSemDadosError, EntradaInvalidaError, PerguntaInvalidaError
from dengue.core.domain.escopo import MotivoRecusa, avaliar_escopo, mensagem_recusa, normalizar
from dengue.core.domain.planejamento import (
    anos_explicitos, extrair_json, interpretar_plano_do_modelo, periodo_valido, planejar_por_regras,
)
from dengue.core.ports.modelo_linguagem import ModeloLinguagem
from dengue.core.ports.repositorios import ConsultaInfoDengue, RepositorioConversas
from dengue.core.services.fatos_dengue import calcular_fatos

_RE_SESSAO = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
MAX_TOKENS_PLANO, MAX_TOKENS_RESPOSTA = 120, 250


class ConversarComDados:
    def __init__(self, modelo: ModeloLinguagem, consulta: ConsultaInfoDengue, conversas: RepositorioConversas,
                 ano_atual=lambda: date.today().year, turnos_no_contexto: int = 3, relogio=time.perf_counter):
        self._modelo, self._consulta, self._conversas = modelo, consulta, conversas
        self._ano_atual, self._n_ctx, self._relogio = ano_atual, turnos_no_contexto, relogio

    # ------------------------------------------------------------------
    def executar(self, sessao_id: str | None, pergunta: str) -> RespostaChat:
        inicio = self._relogio()
        pergunta = self._validar_pergunta(pergunta)
        sessao_id = self._validar_sessao(sessao_id)
        ano_atual = self._ano_atual()
        turnos = self._conversas.obter(sessao_id)

        motivo = avaliar_escopo(pergunta, tem_historico=bool(turnos))
        if motivo:
            return self._recusar(sessao_id, pergunta, motivo, inicio)

        historico = self._historico_texto(turnos)
        avisos: list[str] = []
        etapas: list[EtapaMedida] = []

        plano, sinais = self._planejar(pergunta, historico, ano_atual, avisos, etapas)
        if sinais and sinais["cidade"] == "outra":
            return self._recusar(sessao_id, pergunta, MotivoRecusa.OUTRA_CIDADE, inicio, etapas=etapas)
        if sinais and not sinais["assunto_valido"] and not re.search(r"\b(dengue|casos?)\b", normalizar(pergunta)):
            return self._recusar(sessao_id, pergunta, MotivoRecusa.OUTRO_ASSUNTO, inicio, etapas=etapas)
        if not periodo_valido(plano, ano_atual):
            if anos_explicitos(pergunta):
                return self._recusar(sessao_id, pergunta, MotivoRecusa.PERIODO_SEM_DADOS, inicio, etapas=etapas,
                                     detalhe=f"Tenho dados de {ANO_MINIMO_VALIDO} a {ano_atual}.")
            plano = planejar_por_regras(pergunta, ano_atual)
            avisos.append("O período sugerido pela IA era inválido; usei o período deduzido pelas regras.")

        t = self._relogio()
        df, requisicao = self._consulta.consultar(plano.ano_inicio, plano.ano_fim)
        etapas.append(EtapaMedida("consulta_infodengue", round(self._relogio() - t, 2)))
        if df.empty:
            raise ConsultaSemDadosError(plano.ano_inicio, plano.ano_fim)
        fatos = calcular_fatos(df, ano_atual)

        prompt = prompts_chat.montar("respondedor", historico=historico, fatos=fatos.texto, pergunta=pergunta)
        resposta = self._gerar(prompt, MAX_TOKENS_RESPOSTA, "resposta", etapas)
        self._conversas.adicionar(sessao_id, Turno(pergunta, resposta, "resposta", plano.ano_inicio, plano.ano_fim))
        return RespostaChat(
            sessao_id=sessao_id, pergunta=pergunta, tipo="resposta", resposta=resposta, modelo=self._modelo.nome,
            tempo_segundos=round(self._relogio() - inicio, 2), plano=plano, requisicao=requisicao, fatos=fatos.texto,
            etapas=tuple(etapas), avisos=tuple(avisos),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _validar_pergunta(pergunta: str) -> str:
        pergunta = (pergunta or "").strip()
        if not pergunta:
            raise PerguntaInvalidaError("A pergunta está vazia.")
        if len(pergunta) > MAX_PERGUNTA:
            raise PerguntaInvalidaError(f"A pergunta tem {len(pergunta)} caracteres; o máximo é {MAX_PERGUNTA}.")
        return pergunta

    @staticmethod
    def _validar_sessao(sessao_id: str | None) -> str:
        if sessao_id is None:
            return uuid.uuid4().hex
        if not _RE_SESSAO.match(sessao_id):
            raise EntradaInvalidaError("O identificador da conversa é inválido.",
                                       "Use de 8 a 64 caracteres (letras, números, '-' ou '_') ou deixe em branco para iniciar uma nova conversa.")
        return sessao_id

    def _historico_texto(self, turnos: list[Turno]) -> str:
        uteis = [t for t in turnos if t.tipo == "resposta"][-self._n_ctx:]
        if not uteis:
            return "(início da conversa)"
        return "\n".join(f"Usuário: {t.pergunta}\nAssistente: {t.resposta[:300]}" for t in uteis)

    def _gerar(self, prompt: str, max_tokens: int, nome: str, etapas: list[EtapaMedida], formato_json: bool = False) -> str:
        t = self._relogio()
        texto = self._modelo.gerar(prompt, max_tokens=max_tokens, formato_json=formato_json).strip()
        m = self._modelo.ultimas_metricas() or {}
        etapas.append(EtapaMedida(nome, round(self._relogio() - t, 2), m.get("tokens_gerados")))
        return texto

    def _planejar(self, pergunta, historico, ano_atual, avisos, etapas) -> tuple[PlanoConsulta, dict | None]:
        prompt = prompts_chat.montar("planejador", ano_atual=ano_atual, ano_anterior=ano_atual - 1,
                                     historico=historico, pergunta=pergunta)
        saida = self._gerar(prompt, MAX_TOKENS_PLANO, "planejamento", etapas, formato_json=True)
        interpretado = interpretar_plano_do_modelo(extrair_json(saida), pergunta, ano_atual)
        if interpretado is None:
            avisos.append("A IA não devolveu um plano de consulta válido; a pergunta foi interpretada por regras.")
            return planejar_por_regras(pergunta, ano_atual), None
        sinais, plano = interpretado
        return plano, sinais

    def _recusar(self, sessao_id, pergunta, motivo, inicio, etapas=(), detalhe="") -> RespostaChat:
        texto = mensagem_recusa(motivo, detalhe)
        self._conversas.adicionar(sessao_id, Turno(pergunta, texto, "recusa"))
        return RespostaChat(sessao_id=sessao_id, pergunta=pergunta, tipo="recusa", resposta=texto, modelo=self._modelo.nome,
                            tempo_segundos=round(self._relogio() - inicio, 2), etapas=tuple(etapas))
