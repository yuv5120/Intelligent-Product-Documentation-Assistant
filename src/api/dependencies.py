"""
FastAPI dependency injection.

All shared application components are initialised once at startup (via the
FastAPI lifespan context in main.py) and stored on app.state.  These
dependency functions pull them off app.state so that:

  • Every handler receives a fully typed, injected component.
  • Tests can override any dependency with FastAPI's dependency_overrides.
  • There are no module-level mutable singletons.
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, Request

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# ── Component accessors ───────────────────────────────────────────────────────


def get_chroma_client(request: Request):
    """Retrieve the shared ChromaDB client from application state."""
    return request.app.state.chroma_client


def get_retriever(request: Request):
    """Retrieve the shared Retriever from application state."""
    return request.app.state.retriever


def get_generator(request: Request):
    """Retrieve the shared Generator from application state."""
    return request.app.state.generator


def get_memory(request: Request):
    """Retrieve the shared ConversationMemory from application state."""
    return request.app.state.memory


def get_document_parser(request: Request):
    """Retrieve the shared DocumentParser from application state."""
    return request.app.state.document_parser


def get_text_chunker(request: Request):
    """Retrieve the shared TextChunker from application state."""
    return request.app.state.text_chunker


# ── Authentication ────────────────────────────────────────────────────────────


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[str]:
    """
    Validate the X-API-Key request header.

    Auth is disabled when API_KEY is not configured in .env (suitable for
    local development).  When configured, all write endpoints require it.

    Args:
        x_api_key: Value of the X-API-Key header.

    Returns:
        The validated key, or None when auth is disabled.

    Raises:
        HTTPException 401: When a key is configured but the header is missing
            or incorrect.
    """
    configured_key = settings.api_key

    # Auth is opt-in: if no key is configured, skip all checks
    if not configured_key:
        return None

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header. Configure your API key in the client settings.",
        )

    if x_api_key != configured_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    return x_api_key
