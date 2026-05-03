"""
API endpoint tests — updated for DI-based architecture.
Uses mocked dependencies from conftest.py fixtures.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


class TestRootAndHealth:
    def test_root_returns_message(self, api_client):
        client, _ = api_client
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_returns_required_fields(self, api_client):
        client, _ = api_client
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "model_type" in data
        assert "total_documents" in data
        assert "session_backend" in data  # new field in v2

    def test_health_reports_document_count(self, api_client):
        client, mocks = api_client
        mocks["chroma"].get_count.return_value = 42
        response = client.get("/health")
        assert response.json()["total_documents"] == 42


class TestQueryEndpoint:
    def test_query_returns_answer_with_sources(self, api_client):
        client, mocks = api_client
        mocks["chroma"].get_count.return_value = 5
        # Ensure generator returns proper typed data (not MagicMock defaults)
        mocks["generator"].generate_answer.return_value = {
            "answer": "The warranty period is 2 years.",
            "sources": [
                {"citation": "[1] manual.pdf (section 1)", "filename": "manual.pdf", "chunk_index": 0}
            ],
            "context_used": 1,
        }

        response = client.post(
            "/query",
            json={"query": "What is the warranty?", "session_id": "s1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert data["session_id"] == "s1"
        assert "context_used" in data

    def test_query_sources_are_structured(self, api_client):
        """Sources must be structured objects with citation/filename/chunk_index."""
        client, mocks = api_client
        mocks["chroma"].get_count.return_value = 1
        mocks["generator"].generate_answer.return_value = {
            "answer": "Test answer.",
            "sources": [
                {"citation": "[1] doc.pdf (section 1)", "filename": "doc.pdf", "chunk_index": 0}
            ],
            "context_used": 1,
        }

        response = client.post("/query", json={"query": "test query"})
        assert response.status_code == 200
        sources = response.json()["sources"]
        assert len(sources) > 0
        assert "citation" in sources[0]
        assert "filename" in sources[0]
        assert "chunk_index" in sources[0]

    def test_query_empty_db_returns_400(self, api_client_empty_db):
        response = api_client_empty_db.post(
            "/query", json={"query": "What is the warranty?"}
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_query_too_long_returns_422(self, api_client):
        client, _ = api_client
        response = client.post("/query", json={"query": "x" * 3000})
        assert response.status_code == 422

    def test_query_empty_string_returns_422(self, api_client):
        client, _ = api_client
        response = client.post("/query", json={"query": ""})
        assert response.status_code == 422

    def test_query_missing_body_returns_422(self, api_client):
        client, _ = api_client
        response = client.post("/query", json={})
        assert response.status_code == 422

    def test_query_no_results_returns_graceful_message(self, api_client):
        client, mocks = api_client
        mocks["chroma"].get_count.return_value = 5
        mocks["retriever"].retrieve.return_value = []

        response = client.post("/query", json={"query": "something obscure"})
        assert response.status_code == 200
        assert "couldn't find" in response.json()["answer"].lower()


class TestUploadEndpoint:
    def _make_parser_chunker(self):
        """Helper: create mock parser + chunker with correct attributes."""
        mock_parser = MagicMock()
        mock_parser.SUPPORTED_FORMATS = {".txt", ".md", ".pdf", ".html", ".htm", ".docx", ".markdown"}
        mock_parser.parse.return_value = {
            "text": "Test document content.",
            "metadata": {"filename": "test.txt"},
        }

        mock_chunker = MagicMock()
        mock_chunker.chunk_text.return_value = [
            {"text": "Test document content.", "metadata": {"filename": "test.txt", "chunk_index": 0}}
        ]
        return mock_parser, mock_chunker

    def test_unsupported_format_returns_400(self, api_client):
        client, _ = api_client
        response = client.post(
            "/upload",
            files={"file": ("test.exe", b"binary", "application/octet-stream")},
        )
        # The parser's SUPPORTED_FORMATS check happens based on file extension
        # .exe is not in any supported list → should be 400
        assert response.status_code == 400

    def test_upload_txt_file_succeeds(self, api_client):
        client, mocks = api_client
        from src.api.main import app

        # Set mock parser/chunker directly on app.state (how DI reads them)
        mock_parser = MagicMock()
        mock_parser.SUPPORTED_FORMATS = {".txt", ".md", ".pdf", ".html", ".htm", ".docx", ".markdown"}
        mock_parser.parse.return_value = {
            "text": "Test document content.",
            "metadata": {"filename": "readme.txt"},
        }
        mock_chunker = MagicMock()
        mock_chunker.chunk_text.return_value = [
            {"text": "Test document content.", "metadata": {"filename": "readme.txt", "chunk_index": 0}}
        ]
        mocks["chroma"].get_count.return_value = 1

        app.state.document_parser = mock_parser
        app.state.text_chunker = mock_chunker

        response = client.post(
            "/upload",
            files={"file": ("readme.txt", b"Hello world content.", "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "readme.txt"
        assert data["chunks_created"] > 0


class TestSessionEndpoints:
    def test_list_sessions_returns_expected_shape(self, api_client):
        client, _ = api_client
        response = client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "active_sessions" in data
        assert "total_sessions" in data

    def test_clear_session_returns_confirmation(self, api_client):
        client, _ = api_client
        response = client.delete("/sessions/test-session-123")
        assert response.status_code == 200
        assert "message" in response.json()


class TestClearEndpoint:
    def test_clear_returns_documents_removed(self, api_client):
        client, mocks = api_client
        mocks["chroma"].get_count.return_value = 10
        mocks["memory"].get_active_sessions.return_value = ["s1", "s2"]

        response = client.delete("/clear")
        assert response.status_code == 200
        data = response.json()
        assert "documents_removed" in data
        assert "message" in data


class TestMiddleware:
    def test_request_id_header_in_response(self, api_client):
        """Every response must include X-Request-ID."""
        client, _ = api_client
        response = client.get("/health")
        assert "x-request-id" in response.headers

    def test_custom_request_id_echoed_back(self, api_client):
        """If client sends X-Request-ID, it must be echoed in response."""
        client, _ = api_client
        custom_id = "my-trace-id-12345"
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.headers.get("x-request-id") == custom_id


if __name__ == "__main__":
    import pytest as pt
    pt.main([__file__, "-v"])
