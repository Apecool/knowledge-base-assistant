"""
Chat Session Manager — Multi-turn conversation memory.
Manages per-session chat history with context summarization.
"""
import time
from typing import List, Dict, Optional
from collections import defaultdict


class ChatMessage:
    """A single chat message."""
    def __init__(self, role: str, content: str, timestamp: Optional[float] = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }


class ChatSession:
    """A single chat session with message history."""

    def __init__(self, session_id: str, max_history: int = 20):
        self.session_id = session_id
        self.max_history = max_history
        self.messages: List[ChatMessage] = []
        self.created_at = time.time()
        self.updated_at = time.time()

    def add_message(self, role: str, content: str):
        """Add a message and enforce max history limit."""
        self.messages.append(ChatMessage(role, content))
        self.updated_at = time.time()
        # Trim old messages if exceeding limit
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def get_history(self, limit: Optional[int] = None) -> str:
        """
        Format chat history as a text string for LLM context.

        Args:
            limit: Max number of recent messages to include.

        Returns:
            Formatted history string.
        """
        msgs = self.messages
        if limit:
            msgs = msgs[-limit:]

        lines = []
        for msg in msgs:
            prefix = "用户" if msg.role == "user" else "助手"
            lines.append(f"{prefix}: {msg.content}")
        return "\n".join(lines)

    def get_messages_for_llm(self, limit: Optional[int] = None) -> List[dict]:
        """
        Get messages in OpenAI-compatible format.

        Returns:
            List of {"role": ..., "content": ...} dicts.
        """
        msgs = self.messages
        if limit:
            msgs = msgs[-limit:]
        return [{"role": m.role, "content": m.content} for m in msgs]

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [m.to_dict() for m in self.messages],
        }


class ChatSessionManager:
    """
    Manages multiple chat sessions in-memory.
    For production, use Redis/bDatabase backend.
    """

    def __init__(self, max_sessions: int = 100, max_history: int = 20):
        self.max_sessions = max_sessions
        self.max_history = max_history
        self._sessions: Dict[str, ChatSession] = {}

    def get_or_create(self, session_id: str) -> ChatSession:
        """Get existing session or create a new one."""
        if session_id not in self._sessions:
            if len(self._sessions) >= self.max_sessions:
                # Evict oldest session
                oldest = min(self._sessions.values(), key=lambda s: s.updated_at)
                del self._sessions[oldest.session_id]
            self._sessions[session_id] = ChatSession(
                session_id, max_history=self.max_history
            )
        return self._sessions[session_id]

    def add_user_message(self, session_id: str, content: str):
        """Add a user message to a session."""
        session = self.get_or_create(session_id)
        session.add_message("user", content)

    def add_ai_message(self, session_id: str, content: str):
        """Add an AI response to a session."""
        session = self.get_or_create(session_id)
        session.add_message("assistant", content)

    def get_history(self, session_id: str, limit: Optional[int] = None) -> str:
        """Get formatted history for a session."""
        session = self.get_or_create(session_id)
        return session.get_history(limit)

    def delete_session(self, session_id: str):
        """Delete a session."""
        self._sessions.pop(session_id, None)

    def clear_all(self):
        """Clear all sessions."""
        self._sessions.clear()

    def list_sessions(self) -> List[dict]:
        """List all sessions (without full message content for overview)."""
        return [
            {
                "session_id": s.session_id,
                "message_count": len(s.messages),
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in sorted(
                self._sessions.values(), key=lambda x: x.updated_at, reverse=True
            )
        ]


# Singleton instance
session_manager = ChatSessionManager()