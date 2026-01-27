"""
Retriever with semantic search and reranking.
"""

from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder

from src.vector_db.chroma_client import ChromaClient
from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Retriever:
    """
    Semantic retrieval with cross-encoder reranking for improved accuracy.
    """
    
    def __init__(
        self,
        chroma_client: ChromaClient = None,
        rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        """
        Initialize the retriever.
        
        Args:
            chroma_client: ChromaDB client instance
            rerank_model: Cross-encoder model for reranking
        """
        self.chroma_client = chroma_client or ChromaClient()
        
        logger.info(f"Loading reranking model: {rerank_model}")
        self.reranker = CrossEncoder(rerank_model)
        
        logger.info("Retriever initialized successfully")
    
    def retrieve(
        self,
        query: str,
        top_k: int = None,
        top_n: int = None,
        include_scores: bool = True
    ) -> List[Dict]:
        """
        Retrieve relevant documents with reranking.
        
        Args:
            query: Search query
            top_k: Number of initial candidates (default from config)
            top_n: Number of final results after reranking (default from config)
            include_scores: Whether to include relevance scores
            
        Returns:
            List of document dictionaries with text, metadata, and scores
        """
        if top_k is None:
            top_k = settings.top_k_retrieval
        if top_n is None:
            top_n = settings.top_n_rerank
        
        logger.info(f"Retrieving documents for query: '{query}'")
        
        # Step 1: Initial vector search
        search_results = self.chroma_client.search(query, top_k=top_k)
        
        if not search_results['documents']:
            logger.warning("No documents found in vector search")
            return []
        
        # Step 2: Rerank using cross-encoder
        logger.info(f"Reranking {len(search_results['documents'])} candidates")
        
        # Prepare query-document pairs for reranking
        pairs = [[query, doc] for doc in search_results['documents']]
        
        # Get reranking scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Combine results with scores
        combined = []
        for idx, (doc, metadata, score) in enumerate(zip(
            search_results['documents'],
            search_results['metadatas'],
            rerank_scores
        )):
            combined.append({
                'text': doc,
                'metadata': metadata,
                'rerank_score': float(score),
                'original_rank': idx
            })
        
        # Sort by rerank score (descending)
        combined.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        # Take top N
        top_results = combined[:top_n]
        
        logger.info(f"Retrieved {len(top_results)} documents after reranking")
        
        # Format results
        if not include_scores:
            for result in top_results:
                result.pop('rerank_score', None)
                result.pop('original_rank', None)
        
        return top_results
    
    def retrieve_with_citations(
        self,
        query: str,
        top_k: int = None,
        top_n: int = None
    ) -> Tuple[List[Dict], List[str]]:
        """
        Retrieve documents and format citations.
        
        Args:
            query: Search query
            top_k: Number of initial candidates
            top_n: Number of final results
            
        Returns:
            Tuple of (documents, formatted_citations)
        """
        results = self.retrieve(query, top_k=top_k, top_n=top_n)
        
        citations = []
        for idx, result in enumerate(results, 1):
            metadata = result['metadata']
            filename = metadata.get('filename', 'Unknown')
            chunk_idx = metadata.get('chunk_index', 0)
            
            citation = f"[{idx}] {filename} (chunk {chunk_idx})"
            citations.append(citation)
        
        return results, citations
