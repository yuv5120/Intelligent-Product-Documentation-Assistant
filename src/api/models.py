"""
Pydantic models for API request/response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for querying the RAG system."""

    query: str = Field(..., description="User's question", min_length=1, max_length=2000)
    session_id: Optional[str] = Field(
        default="default",
        description="Session ID for conversation tracking",
        max_length=128,
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Number of documents to retrieve initially",
        ge=1,
        le=50,
    )
    top_n: Optional[int] = Field(
        default=None,
        description="Number of documents after reranking",
        ge=1,
        le=20,
    )


class Source(BaseModel):
    """Structured source citation."""

    citation: str = Field(..., description="Formatted citation string, e.g. '[1] manual.pdf (section 2)'")
    filename: str = Field(..., description="Source document filename")
    chunk_index: int = Field(..., description="Chunk index within the source document")


class QueryResponse(BaseModel):
    """Response model for query results."""

    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(..., description="Structured source citations")
    context_used: int = Field(..., description="Number of context documents used")
    session_id: str = Field(..., description="Session ID")


class UploadResponse(BaseModel):
    """Response model for document upload."""

    message: str = Field(..., description="Upload status message")
    filename: str = Field(..., description="Uploaded filename")
    chunks_created: int = Field(..., description="Number of chunks created")
    total_documents: int = Field(..., description="Total documents in database")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    model_type: str = Field(..., description="LLM model type")
    total_documents: int = Field(..., description="Total documents in database")
    session_backend: str = Field(..., description="Session storage backend in use")


class ClearResponse(BaseModel):
    """Response model for clearing database."""

    message: str = Field(..., description="Clear operation status")
    documents_removed: int = Field(..., description="Number of documents removed")


class ErrorResponse(BaseModel):
    """Standard error response shape."""

    detail: str = Field(..., description="Human-readable error description")
