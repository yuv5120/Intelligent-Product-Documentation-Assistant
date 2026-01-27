"""
API endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_type" in data
    assert "total_documents" in data


def test_upload_document():
    """Test document upload."""
    sample_file = Path("sample_docs/faq.md")
    
    if not sample_file.exists():
        pytest.skip("Sample file not found")
    
    with open(sample_file, "rb") as f:
        response = client.post(
            "/upload",
            files={"file": ("faq.md", f, "text/markdown")}
        )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["filename"] == "faq.md"
    assert data["chunks_created"] > 0
    assert data["total_documents"] > 0


def test_query_without_documents():
    """Test querying when no documents are indexed."""
    # Clear database first
    client.delete("/clear")
    
    response = client.post(
        "/query",
        json={"query": "What is the warranty?"}
    )
    
    # Should return error since no documents
    assert response.status_code == 400


def test_query_with_documents():
    """Test querying after uploading documents."""
    # Upload a document first
    sample_file = Path("sample_docs/faq.md")
    
    if not sample_file.exists():
        pytest.skip("Sample file not found")
    
    with open(sample_file, "rb") as f:
        client.post(
            "/upload",
            files={"file": ("faq.md", f, "text/markdown")}
        )
    
    # Now query
    response = client.post(
        "/query",
        json={
            "query": "What is the return policy?",
            "session_id": "test_session"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "context_used" in data
    assert data["session_id"] == "test_session"


def test_clear_database():
    """Test clearing the database."""
    response = client.delete("/clear")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "documents_removed" in data


def test_list_sessions():
    """Test listing active sessions."""
    response = client.get("/sessions")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "active_sessions" in data
    assert "total_sessions" in data


def test_clear_session():
    """Test clearing a specific session."""
    session_id = "test_session_to_clear"
    
    response = client.delete(f"/sessions/{session_id}")
    
    assert response.status_code == 200
    assert "message" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
