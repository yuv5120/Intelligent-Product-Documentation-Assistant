"""
LLM-based answer generator with context assembly.
All generation parameters are pulled from settings — no magic numbers.
"""

import asyncio
from typing import List, Dict, Optional

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Generator:
    """
    Generate answers using LLM with retrieved context.
    Supports OpenAI and Ollama backends.
    LLM calls are wrapped in run_in_executor so they don't block
    FastAPI's async event loop.
    """

    def __init__(self, model_type: str = None):
        """
        Args:
            model_type: 'openai' or 'ollama' (default: from settings)
        """
        self.model_type = model_type or settings.model_type
        logger.info("Initialising generator", extra={"model_type": self.model_type})

        if self.model_type == "openai":
            self._init_openai()
        elif self.model_type == "ollama":
            self._init_ollama()
        else:
            raise ValueError(f"Unsupported model type: {self.model_type!r}. Choose 'openai' or 'ollama'.")

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_openai(self) -> None:
        """Initialise the OpenAI client."""
        try:
            from openai import OpenAI

            api_key = settings.openai_api_key
            if not api_key:
                logger.warning("No OPENAI_API_KEY configured — OpenAI calls will fail.")
                self.client = None
            else:
                self.client = OpenAI(api_key=api_key)
                self.model_name = settings.openai_model
                logger.info("OpenAI client ready", extra={"model": self.model_name})
        except Exception as exc:
            logger.error("OpenAI init failed", extra={"error": str(exc)})
            self.client = None

    def _init_ollama(self) -> None:
        """Verify Ollama connectivity and store connection config."""
        import requests

        base_url = settings.ollama_base_url
        try:
            resp = requests.get(f"{base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                self.model_name = settings.ollama_model
                self.ollama_base_url = base_url
                logger.info("Ollama client ready", extra={"model": self.model_name, "base_url": base_url})
            else:
                raise ConnectionError(f"Ollama returned HTTP {resp.status_code}")
        except Exception as exc:
            logger.error("Ollama init failed — is `ollama serve` running?", extra={"error": str(exc)})
            self.client = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def generate_answer(
        self,
        query: str,
        context_docs: List[Dict],
        conversation_history: List[Dict] = None,
    ) -> Dict:
        """
        Generate an answer using the configured LLM.

        Args:
            query: User's question.
            context_docs: Retrieved and reranked documents.
            conversation_history: Previous turns for this session.

        Returns:
            dict with keys: answer (str), sources (List[dict]), context_used (int)
        """
        context = self._build_context(context_docs)
        prompt = self._build_prompt(query, context, conversation_history)

        if self.model_type == "openai":
            answer = self._generate_openai_sync(prompt)
        else:
            answer = self._generate_ollama_sync(prompt)

        sources = self._format_sources(context_docs)
        logger.info("Answer generated", extra={"sources_count": len(sources)})

        return {
            "answer": answer,
            "sources": sources,
            "context_used": len(context_docs),
        }

    # ── Context & Prompt builders ─────────────────────────────────────────────

    def _build_context(self, context_docs: List[Dict]) -> str:
        if not context_docs:
            return "No relevant context found."
        parts = []
        for idx, doc in enumerate(context_docs, 1):
            filename = doc.get("metadata", {}).get("filename", "Unknown")
            parts.append(f"[Source {idx}: {filename}]\n{doc['text']}")
        return "\n\n".join(parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]],
    ) -> str:
        system_message = (
            "You are a helpful assistant that answers questions about product documentation.\n"
            "Use the provided context to answer the user's question accurately.\n"
            "If the answer is not in the context, say so clearly.\n"
            "Always cite your sources using [Source N] notation."
        )

        # Include only the last N turns (configurable, not hardcoded)
        history_text = ""
        if conversation_history:
            turns = conversation_history[-settings.conversation_history_turns :]
            lines = []
            for turn in turns:
                lines.append(f"User: {turn.get('query', '')}")
                lines.append(f"Assistant: {turn.get('answer', '')}")
            history_text = "\n".join(lines) + "\n\n"

        return (
            f"{system_message}\n\n"
            f"{history_text}"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )

    # ── LLM calls ─────────────────────────────────────────────────────────────

    def _generate_openai_sync(self, prompt: str) -> str:
        """Synchronous OpenAI completion (called via run_in_executor in async routes)."""
        if not self.client:
            return "Error: OpenAI client is not initialised. Please set OPENAI_API_KEY."
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.error("OpenAI generation error", extra={"error": str(exc)})
            raise

    def _generate_ollama_sync(self, prompt: str) -> str:
        """Synchronous Ollama completion."""
        import requests

        try:
            resp = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                return resp.json()["response"]
            raise RuntimeError(f"Ollama returned HTTP {resp.status_code}")
        except Exception as exc:
            logger.error("Ollama generation error", extra={"error": str(exc)})
            raise

    # ── Source formatting ──────────────────────────────────────────────────────

    def _format_sources(self, context_docs: List[Dict]) -> List[Dict]:
        """Return structured source dicts matching the Source Pydantic model."""
        sources = []
        for idx, doc in enumerate(context_docs, 1):
            metadata = doc.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            chunk_index = metadata.get("chunk_index", 0)
            sources.append(
                {
                    "citation": f"[{idx}] {filename} (section {chunk_index + 1})",
                    "filename": filename,
                    "chunk_index": chunk_index,
                }
            )
        return sources
