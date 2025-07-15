"""Message model for chat conversations."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any
from datetime import datetime


class MessageRole(Enum):
    """Enumeration of message roles in a conversation."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Represents a single message in a conversation."""
    
    role: MessageRole
    content: str
    timestamp: datetime | None = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @classmethod
    def system(cls, content: str) -> Message:
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)
    
    @classmethod
    def user(cls, content: str) -> Message:
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content)
    
    @classmethod
    def assistant(cls, content: str) -> Message:
        """Create an assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format for API calls."""
        return {
            "role": self.role.value,
            "content": self.content,
        }
    
    def to_log_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format for logging."""
        return {
            "role": self.role.value,
            "content": self.content,
            "ts": self.timestamp.isoformat() if self.timestamp else None,
        }
    
    @classmethod
    def from_log_dict(cls, data: Dict[str, Any]) -> Message:
        """Create message from log dictionary."""
        timestamp = None
        if data.get("ts"):
            try:
                timestamp = datetime.fromisoformat(data["ts"])
            except ValueError:
                pass
        
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=timestamp,
        )
