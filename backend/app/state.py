"""
In-memory conversation state management.
Stores conversation history and user data per session.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


class ConversationState:
    """Manages conversation state in memory."""
    
    def __init__(self):
        self.conversations: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Returns:
            Session ID (UUID string)
        """
        session_id = str(uuid.uuid4())
        self.conversations[session_id] = {
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "user_data": {}
        }
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to conversation history.
        
        Args:
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
        """
        if session_id not in self.conversations:
            raise ValueError(f"Session {session_id} not found")
        
        self.conversations[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of messages in format expected by Groq API
        """
        if session_id not in self.conversations:
            return []
        
        # Convert to format expected by Groq API
        messages = []
        for msg in self.conversations[session_id]["messages"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return messages
    
    def update_user_data(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Update user data extracted from conversation.
        
        Args:
            session_id: Session identifier
            data: Dictionary of user data (income, property_price, etc.)
        """
        if session_id not in self.conversations:
            raise ValueError(f"Session {session_id} not found")
        
        self.conversations[session_id]["user_data"].update(data)
    
    def get_user_data(self, session_id: str) -> Dict[str, Any]:
        """
        Get user data for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary of user data
        """
        if session_id not in self.conversations:
            return {}
        
        return self.conversations[session_id]["user_data"]
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self.conversations


# Global state instance
conversation_state = ConversationState()
