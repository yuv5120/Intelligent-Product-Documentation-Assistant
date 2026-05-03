"""
Shared pytest fixtures for the test suite.

All heavy dependencies (ChromaDB, embedding models, LLM) are mocked so tests
run fast without requiring GPU, API keys, or an internet connection.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def _make_mock_memory(backend_name: str = "in-memory") -> MagicMock:
    m = MagicMock()
    m.backend_name = backend_name
    m.get_active_sessions.return_value = []
    m.get_history.return_value = []
    m.get_session_count.return_value = 0
    return m


def _make_mock_chroma(doc_count: int = 0) -> MagicMock:
    m = MagicMock()
    m.get_count.return_value = doc_count
    return m


def _make_mock_retriever() -> MagicMock:
    m = MagicMock()
    m.retrieve.return_value = [
        {
            "text": "The warranty is 2 years.",
            "metadata": {"filename": "manual.pdf", "chunk_index": 0},
            "rerank_score": 0.95,
        }
    ]
    return m


def _make_mock_generator() -> MagicMock:
    m = MagicMock()
    m.generate_answer.return_value = {
        "answer": "The warranty period is 2 years.",
        "sources": [
            {"citation": "[1] manual.pdf (section 1)", "filename": "manual.pdf", "chunk_index": 0}
        ],
        "context_used": 1,
    }
    return m


@pytest.fixture()
def api_client():
    """
    Isolated TestClient with all heavy deps mocked.
    Auth is DISABLED (API_KEY not set).
    """
    with (
        patch("src.api.main.ChromaClient") as mock_chroma_cls,
        patch("src.api.main.Retriever") as mock_retriever_cls,
        patch("src.api.main.Generator") as mock_gen_cls,
        patch("src.api.main.create_memory_backend") as mock_mem_factory,
        patch("src.api.main.DocumentParser") as mock_parser_cls,
        patch("src.api.main.TextChunker") as mock_chunker_cls,
    ):
        mock_chroma = _make_mock_chroma(doc_count=5)
        mock_chroma_cls.return_value = mock_chroma

        mock_retriever = _make_mock_retriever()
        mock_retriever_cls.return_value = mock_retriever

        mock_generator = _make_mock_generator()
        mock_gen_cls.return_value = mock_generator

        mock_memory = _make_mock_memory()
        mock_mem_factory.return_value = mock_memory

        mock_parser_cls.return_value = MagicMock()
        mock_chunker_cls.return_value = MagicMock()

        from src.api.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, {
                "chroma": mock_chroma,
                "retriever": mock_retriever,
                "generator": mock_generator,
                "memory": mock_memory,
            }


@pytest.fixture()
def api_client_empty_db():
    """TestClient with empty database (0 documents)."""
    with (
        patch("src.api.main.ChromaClient") as mock_chroma_cls,
        patch("src.api.main.Retriever"),
        patch("src.api.main.Generator"),
        patch("src.api.main.create_memory_backend") as mock_mem_factory,
        patch("src.api.main.DocumentParser"),
        patch("src.api.main.TextChunker"),
    ):
        mock_chroma = _make_mock_chroma(doc_count=0)
        mock_chroma_cls.return_value = mock_chroma
        mock_mem_factory.return_value = _make_mock_memory()

        from src.api.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            yield client


@pytest.fixture()
def api_client_with_auth(monkeypatch):
    """TestClient with API_KEY='test-secret' configured."""
    monkeypatch.setenv("API_KEY", "test-secret")

    with (
        patch("src.api.main.ChromaClient") as mock_chroma_cls,
        patch("src.api.main.Retriever"),
        patch("src.api.main.Generator"),
        patch("src.api.main.create_memory_backend") as mock_mem_factory,
        patch("src.api.main.DocumentParser"),
        patch("src.api.main.TextChunker"),
    ):
        mock_chroma = _make_mock_chroma(doc_count=3)
        mock_chroma_cls.return_value = mock_chroma
        mock_mem_factory.return_value = _make_mock_memory()

        # Re-import settings so the monkeypatched env var takes effect
        import importlib
        import src.config as config_mod
        importlib.reload(config_mod)

        from src.api.main import app

        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
