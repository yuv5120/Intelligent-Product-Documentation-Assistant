"""
ChromaDB client for vector storage and similarity search.
"""

from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

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
        persist_directory: str = None
    ):
        """
        Initialize ChromaDB client.
        
        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist the database
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        
        logger.info(f"Initializing ChromaDB at: {self.persist_directory}")
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )
        
        # Initialize embedding model
        self.embedding_model = EmbeddingModel()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        logger.info(
            f"ChromaDB initialized. Collection: {self.collection_name}, "
            f"Documents: {self.collection.count()}"
        )
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict] = None,
        ids: List[str] = None
    ) -> None:
        """
        Add documents to the vector database.
        
        Args:
            texts: List of text chunks to add
            metadatas: List of metadata dictionaries for each chunk
            ids: Optional list of IDs (auto-generated if not provided)
        """
        if not texts:
            logger.warning("No texts provided to add_documents")
            return
        
        # Generate IDs if not provided
        if ids is None:
            start_id = self.collection.count()
            ids = [f"doc_{start_id + i}" for i in range(len(texts))]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} documents")
        embeddings = self.embedding_model.embed_batch(texts)
        
        # Add to collection
        logger.info(f"Adding {len(texts)} documents to ChromaDB")
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(
            f"Successfully added {len(texts)} documents. "
            f"Total documents: {self.collection.count()}"
        )
    
    def search(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Dict = None
    ) -> Dict:
        """
        Search for similar documents using semantic search.
        
        Args:
            query: Search query text
            top_k: Number of results to return (default from config)
            filter_metadata: Optional metadata filter
            
        Returns:
            Dictionary with documents, metadatas, and distances
        """
        if top_k is None:
            top_k = settings.top_k_retrieval
        
        logger.info(f"Searching for: '{query}' (top_k={top_k})")
        
        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )
        
        # Format results
        formatted_results = {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }
        
        logger.info(f"Found {len(formatted_results['documents'])} results")
        
        return formatted_results
    
    def clear_collection(self) -> None:
        """Delete all documents from the collection."""
        logger.warning(f"Clearing collection: {self.collection_name}")
        
        # Delete the collection
        self.client.delete_collection(name=self.collection_name)
        
        # Recreate empty collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info("Collection cleared successfully")
    
    def get_count(self) -> int:
        """
        Get the number of documents in the collection.
        
        Returns:
            Document count
        """
        return self.collection.count()
    
    def delete_by_metadata(self, metadata_filter: Dict) -> None:
        """
        Delete documents matching metadata filter.
        
        Args:
            metadata_filter: Metadata filter to match documents
        """
        logger.info(f"Deleting documents with filter: {metadata_filter}")
        
        # This is a limitation of ChromaDB - we need to query first, then delete
        results = self.collection.get(where=metadata_filter)
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
            logger.info(f"Deleted {len(results['ids'])} documents")
        else:
            logger.info("No documents matched the filter")
