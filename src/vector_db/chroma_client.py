"""
ChromaDB client for vector storage and similarity search.
Document IDs use UUID4 to prevent collisions on concurrent uploads.
"""

import uuid
from typing import List, Dict, Optional

import chromadb

from src.config import settings
from src.embeddings.embedding_model import EmbeddingModel
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ChromaClient:
    """
    Wrapper for ChromaDB vector database operations.
    Handles document indexing and similarity search.
    """

    def __init__(
        self,
        collection_name: str = "product_docs",
        persist_directory: str = None,
    ):
        """
        Args:
            collection_name: ChromaDB collection name.
            persist_directory: Persistence directory (default: from settings).
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_dir

        logger.info("Initialising ChromaDB", extra={"path": self.persist_directory})

        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.embedding_model = EmbeddingModel()

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "ChromaDB ready",
            extra={
                "collection": self.collection_name,
                "document_count": self.collection.count(),
            },
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict] = None,
        ids: List[str] = None,
    ) -> None:
        """
        Index documents into the vector database.

        Args:
            texts: Text chunks to embed and store.
            metadatas: Metadata dict per chunk.
            ids: Optional explicit IDs. When omitted, UUID4 values are
                 generated — this is the safe default and avoids collisions
                 that sequential counter IDs produce after deletions.
        """
        if not texts:
            logger.warning("add_documents called with empty text list")
            return

        # Always use UUID4 unless the caller provides explicit IDs
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]

        logger.info("Generating embeddings", extra={"count": len(texts)})
        embeddings = self.embedding_model.embed_batch(texts)

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info(
            "Documents indexed",
            extra={"added": len(texts), "total": self.collection.count()},
        )

    # ── Read ──────────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Dict = None,
    ) -> Dict:
        """
        Semantic similarity search.

        Args:
            query: Free-text query.
            top_k: Number of results (default: from settings).
            filter_metadata: Optional ChromaDB where-filter.

        Returns:
            dict with keys: documents, metadatas, distances, ids
        """
        if top_k is None:
            top_k = settings.top_k_retrieval

        logger.info("Vector search", extra={"query": query[:80], "top_k": top_k})

        query_embedding = self.embedding_model.embed_text(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
        )

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else [],
        }

    def get_count(self) -> int:
        """Return the total number of indexed chunks."""
        return self.collection.count()

    # ── Delete ────────────────────────────────────────────────────────────────

    def clear_collection(self) -> None:
        """Delete all documents and recreate the collection."""
        logger.warning("Clearing collection", extra={"collection": self.collection_name})
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Collection cleared")

    def delete_by_metadata(self, metadata_filter: Dict) -> None:
        """
        Delete documents matching a metadata filter.

        Args:
            metadata_filter: ChromaDB where-filter dict.
        """
        logger.info("Deleting by metadata", extra={"filter": metadata_filter})
        results = self.collection.get(where=metadata_filter)
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info("Documents deleted", extra={"count": len(results["ids"])})
        else:
            logger.info("No documents matched deletion filter")
