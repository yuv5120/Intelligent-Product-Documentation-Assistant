"""
Configuration management for the RAG system.
Loads settings from environment variables with sensible defaults.
All previously hardcoded magic values are now configurable here.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── LLM Configuration ────────────────────────────────────────────────────
    model_type: Literal["openai", "ollama"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"

    ollama_model: str = "llama2"
    ollama_base_url: str = "http://localhost:11434"

    # LLM Generation Parameters (were previously hardcoded in generator.py)
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=500, ge=50, le=8000)
    conversation_history_turns: int = Field(default=3, ge=1, le=20)

    # ── Vector Database ───────────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"

    # ── Embedding & Reranking Models ──────────────────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ── Retrieval Parameters ──────────────────────────────────────────────────
    chunk_size: int = Field(default=512, ge=100, le=4096)
    chunk_overlap: int = Field(default=50, ge=0, le=200)
    top_k_retrieval: int = Field(default=20, ge=1, le=100)
    top_n_rerank: int = Field(default=5, ge=1, le=20)

    # ── Request Limits ────────────────────────────────────────────────────────
    max_query_length: int = Field(default=2000, ge=10)
    max_file_size_mb: int = Field(default=50, ge=1, le=500)

    # ── Authentication ────────────────────────────────────────────────────────
    # Leave empty to disable auth (useful for local development)
    api_key: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    # Format: "N/period" — e.g. "30/minute", "5/second"
    rate_limit: str = "30/minute"

    # ── Session / Memory ──────────────────────────────────────────────────────
    # Leave empty to use in-memory backend (sessions are lost on restart)
    # Set to a redis URL (e.g. redis://localhost:6379) to enable persistence
    redis_url: str = ""
    session_max_history: int = Field(default=5, ge=1, le=50)

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Observability ─────────────────────────────────────────────────────────
    log_format: Literal["json", "text"] = "json"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
