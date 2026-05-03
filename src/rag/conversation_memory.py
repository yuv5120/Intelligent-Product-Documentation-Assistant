"""
Conversation memory with pluggable storage backends.

Backends:
  InMemoryBackend  — default, zero dependencies, sessions lost on restart.
  RedisBackend     — persistent across restarts; requires REDIS_URL in .env.

The factory function `create_memory_backend()` selects the backend
automatically based on whether REDIS_URL is configured.
"""

import json
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# ── Abstract interface ────────────────────────────────────────────────────────


class MemoryBackend(ABC):
    """Abstract base for conversation history storage."""

    @abstractmethod
    def add_turn(
        self,
        session_id: str,
        query: str,
        answer: str,
        sources: List[dict],
    ) -> None: ...

    @abstractmethod
    def get_history(self, session_id: str) -> List[Dict]: ...

    @abstractmethod
    def clear_session(self, session_id: str) -> None: ...

    @abstractmethod
    def get_active_sessions(self) -> List[str]: ...

    @abstractmethod
    def get_session_count(self) -> int: ...

    @property
    @abstractmethod
    def backend_name(self) -> str: ...


# ── In-Memory backend (default) ───────────────────────────────────────────────


class InMemoryBackend(MemoryBackend):
    """
    In-process dictionary-based session storage.
    Fast and zero-dependency, but sessions are lost when the process restarts.
    """

    def __init__(self, max_history: int = None):
        self._max_history = max_history or settings.session_max_history
        self._sessions: Dict[str, List[Dict]] = defaultdict(list)
        logger.info(
            "InMemoryBackend initialised",
            extra={"max_history": self._max_history},
        )

    def add_turn(
        self,
        session_id: str,
        query: str,
        answer: str,
        sources: List[dict],
    ) -> None:
        turn = {"query": query, "answer": answer, "sources": sources}
        self._sessions[session_id].append(turn)
        # Trim to window
        if len(self._sessions[session_id]) > self._max_history:
            self._sessions[session_id] = self._sessions[session_id][-self._max_history :]

    def get_history(self, session_id: str) -> List[Dict]:
        return list(self._sessions.get(session_id, []))

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def get_active_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    def get_session_count(self) -> int:
        return len(self._sessions)

    @property
    def backend_name(self) -> str:
        return "in-memory"


# ── Redis backend (optional) ──────────────────────────────────────────────────


class RedisBackend(MemoryBackend):
    """
    Redis-backed session storage.
    Sessions survive process restarts and work across multiple instances.
    Requires redis[hiredis] to be installed and REDIS_URL to be set.
    """

    _KEY_PREFIX = "rag:session:"
    _SESSIONS_SET = "rag:sessions"
    _TTL_SECONDS = 86_400  # 24 hours

    def __init__(self, redis_url: str, max_history: int = None):
        import redis as redis_lib

        self._max_history = max_history or settings.session_max_history
        self._redis = redis_lib.Redis.from_url(redis_url, decode_responses=True)
        # Connectivity check
        self._redis.ping()
        logger.info("RedisBackend initialised", extra={"redis_url": redis_url})

    def _session_key(self, session_id: str) -> str:
        return f"{self._KEY_PREFIX}{session_id}"

    def add_turn(
        self,
        session_id: str,
        query: str,
        answer: str,
        sources: List[dict],
    ) -> None:
        key = self._session_key(session_id)
        turn = json.dumps({"query": query, "answer": answer, "sources": sources})
        pipe = self._redis.pipeline()
        pipe.rpush(key, turn)
        pipe.ltrim(key, -self._max_history, -1)
        pipe.expire(key, self._TTL_SECONDS)
        pipe.sadd(self._SESSIONS_SET, session_id)
        pipe.execute()

    def get_history(self, session_id: str) -> List[Dict]:
        raw = self._redis.lrange(self._session_key(session_id), 0, -1)
        return [json.loads(item) for item in raw]

    def clear_session(self, session_id: str) -> None:
        self._redis.delete(self._session_key(session_id))
        self._redis.srem(self._SESSIONS_SET, session_id)

    def get_active_sessions(self) -> List[str]:
        return list(self._redis.smembers(self._SESSIONS_SET))

    def get_session_count(self) -> int:
        return self._redis.scard(self._SESSIONS_SET)

    @property
    def backend_name(self) -> str:
        return "redis"


# ── Public facade ─────────────────────────────────────────────────────────────


class ConversationMemory:
    """
    Public interface for conversation history.
    Delegates to whichever MemoryBackend was selected at startup.
    """

    def __init__(self, backend: MemoryBackend):
        self._backend = backend

    # Delegate every public method to the backend
    def add_turn(self, session_id: str, query: str, answer: str, sources: List[dict]) -> None:
        self._backend.add_turn(session_id, query, answer, sources)

    def get_history(self, session_id: str) -> List[Dict]:
        return self._backend.get_history(session_id)

    def clear_session(self, session_id: str) -> None:
        self._backend.clear_session(session_id)

    def get_active_sessions(self) -> List[str]:
        return self._backend.get_active_sessions()

    def get_session_count(self) -> int:
        return self._backend.get_session_count()

    @property
    def backend_name(self) -> str:
        return self._backend.backend_name


# ── Factory ───────────────────────────────────────────────────────────────────


def create_memory_backend() -> ConversationMemory:
    """
    Instantiate the appropriate ConversationMemory based on configuration.

    - REDIS_URL set  → RedisBackend (persistent, multi-instance safe)
    - REDIS_URL empty → InMemoryBackend (default, zero dependencies)
    """
    if settings.redis_url:
        try:
            backend = RedisBackend(
                redis_url=settings.redis_url,
                max_history=settings.session_max_history,
            )
            logger.info("Using Redis session backend")
            return ConversationMemory(backend)
        except Exception as exc:
            logger.warning(
                "Redis connection failed; falling back to in-memory sessions",
                extra={"error": str(exc)},
            )

    backend = InMemoryBackend(max_history=settings.session_max_history)
    logger.info("Using in-memory session backend")
    return ConversationMemory(backend)
