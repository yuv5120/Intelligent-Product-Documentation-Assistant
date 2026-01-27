"""
LLM-based answer generator with context assembly.
"""

from typing import List, Dict, Optional
import os

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Generator:
    """
    Generate answers using LLM with retrieved context.
    Supports both OpenAI and local Ollama models.
    """
    
    def __init__(self, model_type: str = None):
        """
        Initialize the generator.
        
        Args:
            model_type: 'openai' or 'ollama' (default from config)
        """
        self.model_type = model_type or settings.model_type
        
        logger.info(f"Initializing generator with model type: {self.model_type}")
        
        if self.model_type == "openai":
            self._init_openai()
        elif self.model_type == "ollama":
            self._init_ollama()
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            
            api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                logger.warning(
                    "No OpenAI API key found. Set OPENAI_API_KEY environment variable."
                )
                self.client = None
            else:
                self.client = OpenAI(api_key=api_key)
                self.model_name = "gpt-3.5-turbo"
                logger.info(f"OpenAI client initialized with model: {self.model_name}")
        
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.client = None
    
    def _init_ollama(self):
        """Initialize Ollama client."""
        try:
            # Ollama uses a simple HTTP API
            import requests
            
            # Test connection
            response = requests.get("http://localhost:11434/api/tags")
            
            if response.status_code == 200:
                self.model_name = "llama2"  # Default model
                logger.info(f"Ollama client initialized with model: {self.model_name}")
            else:
                logger.error("Ollama server not accessible")
                self.client = None
        
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            logger.info("Make sure Ollama is running: ollama serve")
            self.client = None
    
    def generate_answer(
        self,
        query: str,
        context_docs: List[Dict],
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        Generate an answer using LLM with retrieved context.
        
        Args:
            query: User's question
            context_docs: Retrieved documents with text and metadata
            conversation_history: Previous conversation turns
            
        Returns:
            Dictionary with answer and sources
        """
        logger.info(f"Generating answer for query: '{query}'")
        
        # Build context from retrieved documents
        context = self._build_context(context_docs)
        
        # Build prompt
        prompt = self._build_prompt(query, context, conversation_history)
        
        # Generate answer
        if self.model_type == "openai":
            answer = self._generate_openai(prompt, conversation_history)
        elif self.model_type == "ollama":
            answer = self._generate_ollama(prompt)
        else:
            answer = "Error: No LLM configured"
        
        # Format sources
        sources = self._format_sources(context_docs)
        
        logger.info("Answer generated successfully")
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': len(context_docs)
        }
    
    def _build_context(self, context_docs: List[Dict]) -> str:
        """
        Build context string from retrieved documents.
        
        Args:
            context_docs: List of document dictionaries
            
        Returns:
            Formatted context string
        """
        if not context_docs:
            return "No relevant context found."
        
        context_parts = []
        for idx, doc in enumerate(context_docs, 1):
            text = doc['text']
            metadata = doc.get('metadata', {})
            filename = metadata.get('filename', 'Unknown')
            
            context_parts.append(f"[Source {idx}: {filename}]\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Build the prompt for the LLM.
        
        Args:
            query: User's question
            context: Retrieved context
            conversation_history: Previous conversation
            
        Returns:
            Formatted prompt
        """
        system_message = """You are a helpful assistant that answers questions about product documentation.
Use the provided context to answer the user's question accurately.
If the answer is not in the context, say so clearly.
Always cite your sources using [Source N] notation."""
        
        # Add conversation history if available
        history_text = ""
        if conversation_history:
            history_parts = []
            for turn in conversation_history[-3:]:  # Last 3 turns
                history_parts.append(f"User: {turn.get('query', '')}")
                history_parts.append(f"Assistant: {turn.get('answer', '')}")
            history_text = "\n".join(history_parts) + "\n\n"
        
        prompt = f"""{system_message}

{history_text}Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    def _generate_openai(
        self,
        prompt: str,
        conversation_history: List[Dict] = None
    ) -> str:
        """Generate answer using OpenAI."""
        if not self.client:
            return "Error: OpenAI client not initialized. Please set OPENAI_API_KEY."
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            return answer
        
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return f"Error generating answer: {str(e)}"
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate answer using Ollama."""
        try:
            import requests
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                return f"Error: Ollama returned status {response.status_code}"
        
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"Error: {str(e)}. Make sure Ollama is running."
    
    def _format_sources(self, context_docs: List[Dict]) -> List[str]:
        """
        Format source citations.
        
        Args:
            context_docs: Retrieved documents
            
        Returns:
            List of formatted source strings
        """
        sources = []
        for idx, doc in enumerate(context_docs, 1):
            metadata = doc.get('metadata', {})
            filename = metadata.get('filename', 'Unknown')
            chunk_idx = metadata.get('chunk_index', 0)
            
            source = f"[{idx}] {filename} (section {chunk_idx + 1})"
            sources.append(source)
        
        return sources
