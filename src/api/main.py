"""
FastAPI application for the RAG system.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tempfile
import shutil

from src.api.models import (
    QueryRequest,
    QueryResponse,
    UploadResponse,
    HealthResponse,
    ClearResponse
)
from src.document_processor.parser import DocumentParser
from src.document_processor.chunker import TextChunker
from src.vector_db.chroma_client import ChromaClient
from src.rag.retriever import Retriever
from src.rag.generator import Generator
from src.rag.conversation_memory import ConversationMemory
from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent Product Documentation Assistant",
    description="RAG system for answering questions about product documentation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
chroma_client = ChromaClient()
retriever = Retriever(chroma_client=chroma_client)
generator = Generator()
conversation_memory = ConversationMemory()
document_parser = DocumentParser()
text_chunker = TextChunker()

logger.info("FastAPI application initialized")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Intelligent Product Documentation Assistant API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns service status and statistics.
    """
    try:
        total_docs = chroma_client.get_count()
        
        return HealthResponse(
            status="healthy",
            model_type=settings.model_type,
            total_documents=total_docs
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index a document.
    Supports PDF, HTML, Markdown, DOCX, and TXT formats.
    """
    try:
        logger.info(f"Received upload request: {file.filename}")
        
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in document_parser.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. "
                       f"Supported: {', '.join(document_parser.SUPPORTED_FORMATS)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # Parse document
            parsed_doc = document_parser.parse(tmp_path)
            
            # Chunk text
            chunks = text_chunker.chunk_text(
                parsed_doc['text'],
                metadata=parsed_doc['metadata']
            )
            
            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail="No text content extracted from document"
                )
            
            # Add to vector database
            texts = [chunk['text'] for chunk in chunks]
            metadatas = [chunk['metadata'] for chunk in chunks]
            
            chroma_client.add_documents(texts=texts, metadatas=metadatas)
            
            total_docs = chroma_client.get_count()
            
            logger.info(
                f"Successfully indexed {file.filename}: "
                f"{len(chunks)} chunks, {total_docs} total documents"
            )
            
            return UploadResponse(
                message="Document uploaded and indexed successfully",
                filename=file.filename,
                chunks_created=len(chunks),
                total_documents=total_docs
            )
        
        finally:
            # Clean up temporary file
            Path(tmp_path).unlink(missing_ok=True)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_documents(request: QueryRequest):
    """
    Query the RAG system with a question.
    Returns an answer with source citations.
    """
    try:
        logger.info(f"Query request: '{request.query}' (session: {request.session_id})")
        
        # Check if database has documents
        if chroma_client.get_count() == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents in database. Please upload documents first."
            )
        
        # Retrieve relevant documents
        retrieved_docs = retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            top_n=request.top_n
        )
        
        if not retrieved_docs:
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question.",
                sources=[],
                context_used=0,
                session_id=request.session_id
            )
        
        # Get conversation history
        history = conversation_memory.get_history(request.session_id)
        
        # Generate answer
        result = generator.generate_answer(
            query=request.query,
            context_docs=retrieved_docs,
            conversation_history=history
        )
        
        # Save to conversation memory
        conversation_memory.add_turn(
            session_id=request.session_id,
            query=request.query,
            answer=result['answer'],
            sources=result['sources']
        )
        
        logger.info(f"Query completed: {len(result['sources'])} sources used")
        
        return QueryResponse(
            answer=result['answer'],
            sources=result['sources'],
            context_used=result['context_used'],
            session_id=request.session_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear", response_model=ClearResponse, tags=["Documents"])
async def clear_database():
    """
    Clear all documents from the vector database.
    Use with caution!
    """
    try:
        logger.warning("Clear database request received")
        
        docs_before = chroma_client.get_count()
        chroma_client.clear_collection()
        
        # Also clear conversation memory
        for session_id in conversation_memory.get_active_sessions():
            conversation_memory.clear_session(session_id)
        
        logger.info(f"Database cleared: {docs_before} documents removed")
        
        return ClearResponse(
            message="Database cleared successfully",
            documents_removed=docs_before
        )
    
    except Exception as e:
        logger.error(f"Clear database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", tags=["Conversation"])
async def list_sessions():
    """List active conversation sessions."""
    try:
        sessions = conversation_memory.get_active_sessions()
        return {
            "active_sessions": sessions,
            "total_sessions": len(sessions)
        }
    
    except Exception as e:
        logger.error(f"List sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}", tags=["Conversation"])
async def clear_session(session_id: str):
    """Clear conversation history for a specific session."""
    try:
        conversation_memory.clear_session(session_id)
        return {"message": f"Session {session_id} cleared"}
    
    except Exception as e:
        logger.error(f"Clear session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
