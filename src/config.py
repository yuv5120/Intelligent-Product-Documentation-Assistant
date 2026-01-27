"""
Configuration management for the RAG system.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    model_type: Literal["openai", "ollama"] = "openai"
    openai_api_key: str = ""
    
    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_db"
    
    # Embedding Model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Retrieval Configuration
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 20
    top_n_rerank: int = 5
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
