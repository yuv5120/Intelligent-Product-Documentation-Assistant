"""
Authentication middleware tests.

Verifies that:
  - Auth is skipped when API_KEY is not configured (dev-friendly default)
  - Protected endpoints return 401 when key is missing
  - Protected endpoints return 401 for wrong key
  - Protected endpoints succeed with correct key
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


def _make_memory():
    m = MagicMock()
    m.backend_name = "in-memory"
    m.get_active_sessions.return_value = []
    m.get_history.return_value = []
    return m


def _make_chroma(count: int = 5):
    m = MagicMock()
    m.get_count.return_value = count
    return m


class TestAuthDisabled:
    """When API_KEY is not set, all endpoints should be accessible without a key."""

    def test_health_no_key_required(self, api_client):
        client, _ = api_client
        response = client.get("/health")
        assert response.status_code == 200

    def test_sessions_no_key_required(self, api_client):
        client, _ = api_client
        response = client.get("/sessions")
        assert response.status_code == 200

    def test_clear_no_key_required(self, api_client):
        client, mocks = api_client
        mocks["memory"].get_active_sessions.return_value = []
        response = client.delete("/clear")
        assert response.status_code == 200

    def test_query_no_key_required(self, api_client):
        """Query should succeed with no X-API-Key when auth is disabled."""
        client, mocks = api_client
        mocks["chroma"].get_count.return_value = 1
        mocks["generator"].generate_answer.return_value = {
            "answer": "Test answer.",
            "sources": [],
            "context_used": 1,
        }
        response = client.post("/query", json={"query": "What is the warranty?"})
        # 200 OK (auth disabled) OR 400 (no docs — still not 401)
        assert response.status_code != 401


class TestAuthEnabled:
    """When API_KEY is set, write endpoints must require it."""

    def _make_auth_client(self):
        """Create a TestClient with auth enabled via dependency override."""
        from fastapi.testclient import TestClient
        from src.api.main import app
        from src.api.dependencies import verify_api_key
        from fastapi import HTTPException

        # Override verify_api_key to enforce a test key
        async def strict_verify(x_api_key: str = None):
            if x_api_key != "test-secret":
                raise HTTPException(status_code=401, detail="Invalid API key.")
            return x_api_key

        app.dependency_overrides[verify_api_key] = strict_verify
        return app, strict_verify

    def test_missing_key_returns_401(self, api_client):
        from src.api.dependencies import verify_api_key
        from fastapi import HTTPException, Header
        from typing import Optional
        from src.api.main import app

        async def strict_verify(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
            if x_api_key != "test-secret":
                raise HTTPException(status_code=401, detail="Invalid API key.")
            return x_api_key

        app.dependency_overrides[verify_api_key] = strict_verify
        client, _ = api_client
        try:
            response = client.post("/query", json={"query": "test"})
            assert response.status_code == 401
            assert "detail" in response.json()
        finally:
            app.dependency_overrides.pop(verify_api_key, None)

    def test_wrong_key_returns_401(self, api_client):
        from src.api.dependencies import verify_api_key
        from fastapi import HTTPException, Header
        from typing import Optional
        from src.api.main import app

        async def strict_verify(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
            if x_api_key != "test-secret":
                raise HTTPException(status_code=401, detail="Invalid API key.")
            return x_api_key

        app.dependency_overrides[verify_api_key] = strict_verify
        client, _ = api_client
        try:
            response = client.post(
                "/query",
                json={"query": "test"},
                headers={"X-API-Key": "wrong-key"},
            )
            assert response.status_code == 401
        finally:
            app.dependency_overrides.pop(verify_api_key, None)

    def test_correct_key_succeeds(self, api_client):
        """Correct key → auth passes; backend may return 200 or 400 (no docs) but not 401."""
        from src.api.dependencies import verify_api_key
        from fastapi import HTTPException, Header
        from typing import Optional
        from src.api.main import app

        async def strict_verify(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
            if x_api_key != "test-secret":
                raise HTTPException(status_code=401, detail="Invalid API key.")
            return x_api_key

        app.dependency_overrides[verify_api_key] = strict_verify
        client, mocks = api_client
        mocks["chroma"].get_count.return_value = 1
        mocks["generator"].generate_answer.return_value = {
            "answer": "Answer.",
            "sources": [],
            "context_used": 1,
        }
        try:
            response = client.post(
                "/query",
                json={"query": "test question"},
                headers={"X-API-Key": "test-secret"},
            )
            assert response.status_code != 401, f"Got 401 with correct key: {response.json()}"
        finally:
            app.dependency_overrides.pop(verify_api_key, None)

    def test_health_never_requires_key(self, api_client):
        """Health check must always be publicly accessible."""
        client, _ = api_client
        response = client.get("/health")
        assert response.status_code == 200

    def test_sessions_list_never_requires_key(self, api_client):
        """GET /sessions is read-only — no auth required."""
        client, _ = api_client
        response = client.get("/sessions")
        assert response.status_code == 200
