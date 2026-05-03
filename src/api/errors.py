"""
Typed error hierarchy and safe HTTP error responses.

Prevents leaking internal implementation details (stack traces, file paths,
DB errors) into API responses — a critical security requirement.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ── Domain Exceptions ─────────────────────────────────────────────────────────


class RAGError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.detail = detail  # Internal detail — never sent to client


class DocumentProcessingError(RAGError):
    """Raised when a document cannot be parsed or chunked."""
    pass


class LLMGenerationError(RAGError):
    """Raised when the LLM fails to produce a response."""
    pass


class DatabaseError(RAGError):
    """Raised on vector database failures."""
    pass


class SessionNotFoundError(RAGError):
    """Raised when a session ID does not exist."""
    pass


# ── Safe HTTP Error Mapping ───────────────────────────────────────────────────

# Maps exception types → (HTTP status code, safe user-facing message)
_ERROR_MAP: dict[type[RAGError], tuple[int, str]] = {
    DocumentProcessingError: (422, "Failed to process the uploaded document. Please ensure it is a valid, non-empty file."),
    LLMGenerationError: (503, "The language model is temporarily unavailable. Please try again shortly."),
    DatabaseError: (503, "The vector database is temporarily unavailable."),
    SessionNotFoundError: (404, "Session not found."),
}


def rag_error_to_http(exc: RAGError) -> HTTPException:
    """
    Convert a domain exception to a safe HTTPException.

    The internal `detail` is logged server-side but never exposed to the client.
    """
    status_code, safe_message = _ERROR_MAP.get(
        type(exc), (500, "An internal error occurred.")
    )
    # Log the full internal detail for debugging
    logger.error(
        "RAGError converted to HTTP response",
        extra={
            "error_type": type(exc).__name__,
            "public_message": safe_message,
            "internal_detail": exc.detail or str(exc),
        },
    )
    return HTTPException(status_code=status_code, detail=safe_message)


# ── Global Exception Handlers ─────────────────────────────────────────────────


async def rag_exception_handler(request: Request, exc: RAGError) -> JSONResponse:
    """FastAPI exception handler for all RAGError subclasses."""
    http_exc = rag_error_to_http(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unexpected exceptions.
    Returns a generic 500 without any internal details.
    """
    logger.exception(
        "Unhandled exception",
        extra={"path": request.url.path, "method": request.method},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )
