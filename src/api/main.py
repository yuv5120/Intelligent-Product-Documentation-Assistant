"""
FastAPI application — Intelligent Product Documentation Assistant.

Key improvements over v1:
  • FastAPI lifespan for proper startup/shutdown resource management
  • Dependency injection via Depends() — no module-level mutable singletons
  • API key authentication (opt-in; disabled when API_KEY is not set)
  • CORS restricted to configured origins
  • Slowapi rate limiting
  • RequestID middleware for end-to-end request tracing
  • Typed error responses — no internal detail leakage
  • Structured source objects in query response
"""

from contextlib import asynccontextmanager
from pathlib import Path
import tempfile
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.api.models import (
    QueryRequest,
    QueryResponse,
    Source,
    UploadResponse,
    HealthResponse,
    ClearResponse,
    ErrorResponse,
)
from src.api.dependencies import (
    get_chroma_client,
    get_retriever,
    get_generator,
    get_memory,
    get_document_parser,
    get_text_chunker,
    verify_api_key,
)
from src.api.middleware import RequestIDMiddleware
from src.api.errors import (
    RAGError,
    DocumentProcessingError,
    rag_exception_handler,
    unhandled_exception_handler,
)
from src.document_processor.parser import DocumentParser
from src.document_processor.chunker import TextChunker
from src.vector_db.chroma_client import ChromaClient
from src.rag.retriever import Retriever
from src.rag.generator import Generator
from src.rag.conversation_memory import create_memory_backend
from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# ── Rate limiter ───────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)


# ── Application lifespan ───────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialise shared components once at startup and store them on app.state.
    Dependency functions in dependencies.py read from app.state, enabling
    clean injection and full test-override capability.
    """
    logger.info("Starting up — initialising components")

    app.state.chroma_client = ChromaClient()
    app.state.retriever = Retriever(chroma_client=app.state.chroma_client)
    app.state.generator = Generator()
    app.state.memory = create_memory_backend()
    app.state.document_parser = DocumentParser()
    app.state.text_chunker = TextChunker()

    logger.info(
        "Application ready",
        extra={
            "model_type": settings.model_type,
            "session_backend": app.state.memory.backend_name,
            "documents": app.state.chroma_client.get_count(),
        },
    )

    yield

    logger.info("Shutting down")


# ── App instance ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Intelligent Product Documentation Assistant",
    description=(
        "RAG system for answering questions about product documentation. "
        "Upload documents, then ask questions — answers come with source citations."
    ),
    version="2.0.0",
    lifespan=lifespan,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorised"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)

# Rate limiter state + exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Domain exception handler must be registered BEFORE the generic Exception handler.
# FastAPI resolves handlers by checking isinstance() in registration order —
# if Exception is first, it will catch RAGError subclasses before RAGError does.
app.add_exception_handler(RAGError, rag_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Request ID tracing middleware (innermost — runs first on request)
app.add_middleware(RequestIDMiddleware)

# CORS — restricted to configured origins, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ── Endpoints ──────────────────────────────────────────────────────────────────


@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    """API root — redirect hint."""
    return {
        "message": "Intelligent Product Documentation Assistant API v2",
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Service health check",
)
async def health_check(
    chroma_client=Depends(get_chroma_client),
    memory=Depends(get_memory),
):
    """Return service status, document count, and active configuration."""
    try:
        total_docs = chroma_client.get_count()
        return HealthResponse(
            status="healthy",
            model_type=settings.model_type,
            total_documents=total_docs,
            session_backend=memory.backend_name,
        )
    except Exception as exc:
        logger.error("Health check failed", extra={"error": str(exc)})
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.post(
    "/upload",
    response_model=UploadResponse,
    tags=["Documents"],
    summary="Upload and index a document",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(settings.rate_limit)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    chroma_client=Depends(get_chroma_client),
    document_parser=Depends(get_document_parser),
    text_chunker=Depends(get_text_chunker),
):
    """
    Upload a document (PDF, HTML, Markdown, DOCX, TXT) and index it for RAG.
    Requires X-API-Key header when API_KEY is configured.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "Upload request received",
        extra={"doc_filename": file.filename, "request_id": request_id},
    )

    # Validate format
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in document_parser.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported format: {file_ext!r}. "
                f"Accepted: {', '.join(sorted(document_parser.SUPPORTED_FORMATS))}"
            ),
        )

    # Validate file size
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_file_size_mb} MB limit.",
        )
    await file.seek(0)

    # Write to temp file, parse, chunk, index
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        try:
            parsed_doc = document_parser.parse(tmp_path)
        except Exception as exc:
            raise DocumentProcessingError(
                "Document parsing failed",
                detail=str(exc),
            )

        chunks = text_chunker.chunk_text(parsed_doc["text"], metadata=parsed_doc["metadata"])
        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="No text content could be extracted from the document.",
            )

        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        chroma_client.add_documents(texts=texts, metadatas=metadatas)

        total_docs = chroma_client.get_count()
        logger.info(
            "Document indexed",
            extra={
                "doc_filename": file.filename,
                "chunks": len(chunks),
                "total_docs": total_docs,
                "request_id": request_id,
            },
        )

        return UploadResponse(
            message="Document uploaded and indexed successfully.",
            filename=file.filename,
            chunks_created=len(chunks),
            total_documents=total_docs,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.post(
    "/query",
    response_model=QueryResponse,
    tags=["Query"],
    summary="Ask a question about your documentation",
    dependencies=[Depends(verify_api_key)],
)
@limiter.limit(settings.rate_limit)
async def query_documents(
    request: Request,
    body: QueryRequest,
    retriever=Depends(get_retriever),
    generator=Depends(get_generator),
    memory=Depends(get_memory),
    chroma_client=Depends(get_chroma_client),
):
    """
    Query the RAG pipeline.  Returns an answer with structured source citations.
    Maintains conversational context per session_id.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "Query received",
        extra={
            "session_id": body.session_id,
            "query_length": len(body.query),
            "request_id": request_id,
        },
    )

    if chroma_client.get_count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents are indexed yet. Please upload documents first.",
        )

    retrieved_docs = retriever.retrieve(
        query=body.query,
        top_k=body.top_k,
        top_n=body.top_n,
    )

    if not retrieved_docs:
        return QueryResponse(
            answer="I couldn't find any relevant information to answer your question.",
            sources=[],
            context_used=0,
            session_id=body.session_id,
        )

    history = memory.get_history(body.session_id)
    result = generator.generate_answer(
        query=body.query,
        context_docs=retrieved_docs,
        conversation_history=history,
    )

    # Persist turn
    memory.add_turn(
        session_id=body.session_id,
        query=body.query,
        answer=result["answer"],
        sources=result["sources"],
    )

    # Map raw dicts → Source Pydantic objects
    sources = [Source(**s) for s in result["sources"]]

    logger.info(
        "Query complete",
        extra={
            "session_id": body.session_id,
            "sources_used": len(sources),
            "request_id": request_id,
        },
    )

    return QueryResponse(
        answer=result["answer"],
        sources=sources,
        context_used=result["context_used"],
        session_id=body.session_id,
    )


@app.delete(
    "/clear",
    response_model=ClearResponse,
    tags=["Documents"],
    summary="Delete all indexed documents",
    dependencies=[Depends(verify_api_key)],
)
async def clear_database(
    chroma_client=Depends(get_chroma_client),
    memory=Depends(get_memory),
):
    """
    Permanently delete all indexed documents and clear all sessions.
    Requires X-API-Key header when API_KEY is configured.
    """
    logger.warning("Clear database requested")
    docs_before = chroma_client.get_count()

    for session_id in memory.get_active_sessions():
        memory.clear_session(session_id)

    chroma_client.clear_collection()

    logger.info("Database cleared", extra={"documents_removed": docs_before})
    return ClearResponse(
        message="Database cleared successfully.",
        documents_removed=docs_before,
    )


@app.get("/sessions", tags=["Conversation"], summary="List active sessions")
async def list_sessions(memory=Depends(get_memory)):
    """Return all active session IDs and their count."""
    sessions = memory.get_active_sessions()
    return {"active_sessions": sessions, "total_sessions": len(sessions)}


@app.delete(
    "/sessions/{session_id}",
    tags=["Conversation"],
    summary="Clear a specific session",
    dependencies=[Depends(verify_api_key)],
)
async def clear_session(session_id: str, memory=Depends(get_memory)):
    """Clear conversation history for the given session_id."""
    memory.clear_session(session_id)
    logger.info("Session cleared", extra={"session_id": session_id})
    return {"message": f"Session '{session_id}' cleared."}


# ── Dev entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
