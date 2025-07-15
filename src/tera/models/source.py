"""Source model for LLM API configuration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from ..config import DEFAULT_BASE_URL, DEFAULT_MODEL


@dataclass
class Source:
    """Represents an LLM API source configuration."""
    
    name: str
    base_url: str
    api_key: str
    model: str
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> Source:
        """Create a Source instance from dictionary data."""
        return cls(
            name=name,
            base_url=data.get("base_url", DEFAULT_BASE_URL),
            api_key=data["api_key"],
            model=data.get("model", DEFAULT_MODEL),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Source instance to dictionary."""
        return {
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model": self.model,
        }
    
    def __str__(self) -> str:
        """String representation of the source."""
        return f"{self.name} -> {self.model} ({self.base_url})"
