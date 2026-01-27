"""
Pydantic models for API request/response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for querying the RAG system."""
    
    query: str = Field(..., description="User's question", min_length=1)
    session_id: Optional[str] = Field(
        default="default",
        description="Session ID for conversation tracking"
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Number of documents to retrieve initially",
        ge=1,
        le=50
    )
    top_n: Optional[int] = Field(
        default=None,
        description="Number of documents after reranking",
        ge=1,
        le=20
    )


class Source(BaseModel):
    """Source citation model."""
    
    citation: str = Field(..., description="Formatted citation")
    filename: str = Field(..., description="Source filename")
    chunk_index: int = Field(..., description="Chunk index in document")


class QueryResponse(BaseModel):
    """Response model for query results."""
    
    answer: str = Field(..., description="Generated answer")
    sources: List[str] = Field(..., description="Source citations")
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


class ClearResponse(BaseModel):
    """Response model for clearing database."""
    
    message: str = Field(..., description="Clear operation status")
    documents_removed: int = Field(..., description="Number of documents removed")
