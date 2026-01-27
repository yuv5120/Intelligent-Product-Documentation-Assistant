"""
Text chunking with semantic awareness for better retrieval.
"""

from typing import List, Dict
import re

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TextChunker:
    """
    Chunk text into smaller segments with overlap for better retrieval.
    Uses sentence-aware chunking to preserve semantic meaning.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Maximum characters per chunk (default from config)
            chunk_overlap: Overlap between chunks in characters (default from config)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        logger.info(
            f"TextChunker initialized: chunk_size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}"
        )
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, any] = None
    ) -> List[Dict[str, any]]:
        """
        Split text into chunks with metadata preservation.
        
        Args:
            text: Text to chunk
            metadata: Document metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        # Split into sentences first
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_text = chunk_text[-self.chunk_overlap:] if len(chunk_text) > self.chunk_overlap else chunk_text
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text)
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Create chunk objects with metadata
        chunk_objects = []
        for idx, chunk_text in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_index'] = idx
            chunk_metadata['total_chunks'] = len(chunks)
            
            chunk_objects.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })
        
        logger.info(f"Created {len(chunk_objects)} chunks from text")
        
        return chunk_objects
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting on common punctuation
        # This regex splits on . ! ? followed by whitespace
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
