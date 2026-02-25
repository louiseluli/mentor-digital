"""
session_manager.py — Gerenciamento de sessões via Redis (Micro-Batch 2.3)

Substitui o dict in-memory de 2.2. Cada sessão expira em DEFAULT_TTL segundos.
Injetável: aceita redis.Redis no construtor — facilita testes com fakeredis.
"""

import json
import redis

from src.models import ConversationContext
from src.engine.fsm import QuestioningFSM

KEY_PREFIX = "mentor:session:"
DEFAULT_TTL = 3600  # 1 hora

ANALYSIS_KEY_PREFIX = "mentor:analysis:"
ANALYSIS_TTL = 604800  # 7 dias


class SessionManager:
    """Gerencia sessões de conversa no Redis."""

    def __init__(self, redis_client: redis.Redis, ttl: int = DEFAULT_TTL):
        self._r = redis_client
        self._ttl = ttl

    @classmethod
    def from_url(cls, url: str, ttl: int = DEFAULT_TTL) -> "SessionManager":
        """Cria SessionManager a partir de uma URL Redis."""
        client = redis.from_url(url)
        return cls(client, ttl)

    # ── Operações públicas ────────────────────────────────────────────────────

    def get_or_create(self, user_id: str, platform: str = "telegram") -> QuestioningFSM:
        """Restaura sessão existente ou cria nova FSM."""
        raw = self._r.get(f"{KEY_PREFIX}{user_id}")
        if not raw:
            ctx = ConversationContext(user_id=user_id, platform=platform)
            return QuestioningFSM(ctx)

        session = json.loads(raw)
        ctx = ConversationContext.from_json(session["context"])
        fsm = QuestioningFSM(ctx)
        fsm.state = session["state"]
        return fsm

    def save(self, user_id: str, fsm: QuestioningFSM) -> None:
        """Persiste estado e contexto no Redis com TTL."""
        data = json.dumps({
            "context": fsm.context.to_json(),
            "state": fsm.state,
        })
        self._r.set(f"{KEY_PREFIX}{user_id}", data, ex=self._ttl)

    def delete(self, user_id: str) -> None:
        """Remove sessão (chamado em /start e após estado end)."""
        self._r.delete(f"{KEY_PREFIX}{user_id}")

    def exists(self, user_id: str) -> bool:
        """Verifica se existe sessão ativa para o usuário."""
        return bool(self._r.exists(f"{KEY_PREFIX}{user_id}"))

    # ── Análise por content_id ────────────────────────────────────────────────

    def save_analysis(self, content_id: str, data: dict) -> None:
        """Persiste resultados de análise indexados por content_id (TTL 7 dias).

        Chave separada da sessão do usuário — permite acesso pela plataforma web
        sem expor dados do usuário. O content_id UUID atua como token de acesso.
        """
        self._r.set(
            f"{ANALYSIS_KEY_PREFIX}{content_id}",
            json.dumps(data),
            ex=ANALYSIS_TTL,
        )

    @property
    def redis(self):
        """Expõe o cliente Redis para uso por módulos externos (ex: analytics)."""
        return self._r

    def get_analysis(self, content_id: str) -> dict | None:
        """Recupera resultados de análise por content_id.

        Returns:
            Dict com resultados de análise, ou None se não encontrado / expirado.
        """
        raw = self._r.get(f"{ANALYSIS_KEY_PREFIX}{content_id}")
        if raw is None:
            return None
        return json.loads(raw)
