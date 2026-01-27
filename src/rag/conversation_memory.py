"""
Conversation memory for maintaining context across multiple turns.
"""

from typing import List, Dict, Optional
from collections import defaultdict

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConversationMemory:
    """
    Manage conversation history for contextual follow-up questions.
    """
    
    def __init__(self, max_history: int = 5):
        """
        Initialize conversation memory.
        
        Args:
            max_history: Maximum number of turns to remember per session
        """
        self.max_history = max_history
        self.sessions: Dict[str, List[Dict]] = defaultdict(list)
        
        logger.info(f"ConversationMemory initialized (max_history={max_history})")
    
    def add_turn(
        self,
        session_id: str,
        query: str,
        answer: str,
        sources: List[str] = None
    ) -> None:
        """
        Add a conversation turn to the session history.
        
        Args:
            session_id: Unique session identifier
            query: User's query
            answer: Assistant's answer
            sources: Source citations
        """
        turn = {
            'query': query,
            'answer': answer,
            'sources': sources or []
        }
        
        self.sessions[session_id].append(turn)
        
        # Trim history if it exceeds max_history
        if len(self.sessions[session_id]) > self.max_history:
            self.sessions[session_id] = self.sessions[session_id][-self.max_history:]
        
        logger.info(
            f"Added turn to session {session_id}. "
            f"Total turns: {len(self.sessions[session_id])}"
        )
    
    def get_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation turns
        """
        return self.sessions.get(session_id, [])
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs.
        
        Returns:
            List of session IDs
        """
        return list(self.sessions.keys())
    
    def get_session_count(self) -> int:
        """
        Get number of active sessions.
        
        Returns:
            Session count
        """
        return len(self.sessions)
