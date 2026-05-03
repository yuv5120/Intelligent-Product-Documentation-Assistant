"""
Retriever with semantic search and cross-encoder reranking.
Reranking model is configurable via settings.rerank_model.
"""

from typing import List, Dict, Tuple

from sentence_transformers import CrossEncoder

from src.vector_db.chroma_client import ChromaClient
from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Retriever:
    """
    Two-stage retrieval:
      1. Dense vector search via ChromaDB (high recall)
      2. Cross-encoder reranking (high precision)
    """

    def __init__(
        self,
        chroma_client: ChromaClient = None,
        rerank_model: str = None,
    ):
        """
        Args:
            chroma_client: Injected ChromaDB client.
            rerank_model: Cross-encoder model name (default: from settings).
        """
        self.chroma_client = chroma_client or ChromaClient()
        model_name = rerank_model or settings.rerank_model

        logger.info("Loading reranking model", extra={"model": model_name})
        self.reranker = CrossEncoder(model_name)
        logger.info("Retriever ready")

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        top_n: int = None,
        include_scores: bool = True,
    ) -> List[Dict]:
        """
        Retrieve and rerank relevant documents.

        Args:
            query: Search query.
            top_k: Initial candidates from vector search (default: settings).
            top_n: Final documents after reranking (default: settings).
            include_scores: Whether to include rerank_score in output.

        Returns:
            List of document dicts: {text, metadata, rerank_score, original_rank}
        """
        if top_k is None:
            top_k = settings.top_k_retrieval
        if top_n is None:
            top_n = settings.top_n_rerank

        logger.info("Retrieving", extra={"query": query[:80], "top_k": top_k, "top_n": top_n})

        # Stage 1: vector search
        search_results = self.chroma_client.search(query, top_k=top_k)
        if not search_results["documents"]:
            logger.warning("No documents found in vector search")
            return []

        # Stage 2: cross-encoder reranking
        pairs = [[query, doc] for doc in search_results["documents"]]
        rerank_scores = self.reranker.predict(pairs)

        combined = [
            {
                "text": doc,
                "metadata": metadata,
                "rerank_score": float(score),
                "original_rank": idx,
            }
            for idx, (doc, metadata, score) in enumerate(
                zip(search_results["documents"], search_results["metadatas"], rerank_scores)
            )
        ]

        combined.sort(key=lambda x: x["rerank_score"], reverse=True)
        top_results = combined[:top_n]

        if not include_scores:
            for r in top_results:
                r.pop("rerank_score", None)
                r.pop("original_rank", None)

        logger.info("Retrieval complete", extra={"returned": len(top_results)})
        return top_results

    def retrieve_with_citations(
        self,
        query: str,
        top_k: int = None,
        top_n: int = None,
    ) -> Tuple[List[Dict], List[str]]:
        """
        Retrieve documents and return formatted citation strings alongside them.

        Returns:
            Tuple of (documents, formatted_citation_strings)
        """
        results = self.retrieve(query, top_k=top_k, top_n=top_n)
        citations = [
            f"[{idx}] {r['metadata'].get('filename', 'Unknown')} (chunk {r['metadata'].get('chunk_index', 0)})"
            for idx, r in enumerate(results, 1)
        ]
        return results, citations
