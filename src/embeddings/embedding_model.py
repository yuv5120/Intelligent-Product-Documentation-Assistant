"""
Embedding model for generating vector representations of text.
Uses sentence-transformers for local, free embedding generation.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingModel:
    """
    Wrapper for sentence-transformers embedding model.
    Provides efficient batch embedding generation.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model
                       (default from config)
        """
        self.model_name = model_name or settings.embedding_model
        
        logger.info(f"Loading embedding model: {self.model_name}")
        
        try:
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            logger.info(
                f"Embedding model loaded successfully. "
                f"Dimension: {self.embedding_dim}"
            )
        
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text.
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Embedding vector(s) as list(s) of floats
        """
        try:
            # Handle single string
            if isinstance(text, str):
                embedding = self.model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            
            # Handle list of strings (batch)
            elif isinstance(text, list):
                embeddings = self.model.encode(
                    text,
                    convert_to_numpy=True,
                    show_progress_bar=len(text) > 10  # Show progress for large batches
                )
                return embeddings.tolist()
            
            else:
                raise ValueError(f"Unsupported input type: {type(text)}")
        
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts with progress tracking.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            
            return embeddings.tolist()
        
        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dim
