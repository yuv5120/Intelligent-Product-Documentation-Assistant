"""
Integration tests for the RAG pipeline.
"""

import pytest
from pathlib import Path

from src.document_processor.parser import DocumentParser
from src.document_processor.chunker import TextChunker
from src.vector_db.chroma_client import ChromaClient
from src.rag.retriever import Retriever
from src.rag.generator import Generator
from src.rag.conversation_memory import ConversationMemory


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    This is a test document about our product.
    The product has many features including Wi-Fi connectivity.
    The warranty lasts for 2 years from the date of purchase.
    To reset the device, go to Settings and select Factory Reset.
    """


@pytest.fixture
def chroma_client():
    """Create a test ChromaDB client."""
    client = ChromaClient(collection_name="test_collection")
    yield client
    # Cleanup
    client.clear_collection()


def test_document_parser():
    """Test document parsing."""
    parser = DocumentParser()
    
    # Test with sample markdown file
    sample_file = Path("sample_docs/faq.md")
    
    if sample_file.exists():
        result = parser.parse(str(sample_file))
        
        assert 'text' in result
        assert 'metadata' in result
        assert len(result['text']) > 0
        assert result['metadata']['filename'] == 'faq.md'


def test_text_chunker(sample_text):
    """Test text chunking."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    
    chunks = chunker.chunk_text(sample_text, metadata={'source': 'test'})
    
    assert len(chunks) > 0
    assert all('text' in chunk for chunk in chunks)
    assert all('metadata' in chunk for chunk in chunks)
    assert all(chunk['metadata']['source'] == 'test' for chunk in chunks)


def test_vector_database(chroma_client, sample_text):
    """Test vector database operations."""
    chunker = TextChunker()
    chunks = chunker.chunk_text(sample_text)
    
    # Add documents
    texts = [chunk['text'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    
    initial_count = chroma_client.get_count()
    chroma_client.add_documents(texts=texts, metadatas=metadatas)
    
    assert chroma_client.get_count() > initial_count
    
    # Search
    results = chroma_client.search("warranty", top_k=3)
    
    assert len(results['documents']) > 0
    assert 'warranty' in results['documents'][0].lower()


def test_retriever(chroma_client, sample_text):
    """Test retrieval with reranking."""
    # Setup
    chunker = TextChunker()
    chunks = chunker.chunk_text(sample_text)
    texts = [chunk['text'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    chroma_client.add_documents(texts=texts, metadatas=metadatas)
    
    # Test retrieval
    retriever = Retriever(chroma_client=chroma_client)
    results = retriever.retrieve("How long is the warranty?", top_k=5, top_n=2)
    
    assert len(results) > 0
    assert 'text' in results[0]
    assert 'metadata' in results[0]
    assert 'rerank_score' in results[0]


def test_conversation_memory():
    """Test conversation memory."""
    memory = ConversationMemory(max_history=3)
    
    session_id = "test_session"
    
    # Add turns
    memory.add_turn(session_id, "Question 1", "Answer 1", ["Source 1"])
    memory.add_turn(session_id, "Question 2", "Answer 2", ["Source 2"])
    
    history = memory.get_history(session_id)
    
    assert len(history) == 2
    assert history[0]['query'] == "Question 1"
    assert history[1]['answer'] == "Answer 2"
    
    # Test max history
    memory.add_turn(session_id, "Question 3", "Answer 3", ["Source 3"])
    memory.add_turn(session_id, "Question 4", "Answer 4", ["Source 4"])
    
    history = memory.get_history(session_id)
    assert len(history) == 3  # Should only keep last 3
    
    # Clear session
    memory.clear_session(session_id)
    assert len(memory.get_history(session_id)) == 0


def test_end_to_end_rag(chroma_client):
    """Test complete RAG pipeline."""
    # Parse sample document
    parser = DocumentParser()
    sample_file = Path("sample_docs/faq.md")
    
    if not sample_file.exists():
        pytest.skip("Sample file not found")
    
    parsed = parser.parse(str(sample_file))
    
    # Chunk
    chunker = TextChunker()
    chunks = chunker.chunk_text(parsed['text'], metadata=parsed['metadata'])
    
    # Index
    texts = [chunk['text'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    chroma_client.add_documents(texts=texts, metadatas=metadatas)
    
    # Retrieve
    retriever = Retriever(chroma_client=chroma_client)
    results = retriever.retrieve("What is the return policy?", top_n=3)
    
    assert len(results) > 0
    
    # Check that relevant content was retrieved
    combined_text = " ".join([r['text'] for r in results])
    assert 'return' in combined_text.lower() or 'refund' in combined_text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
