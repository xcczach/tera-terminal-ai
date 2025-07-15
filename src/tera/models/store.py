"""Store model for application state management."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from .source import Source
from .character import Character
from ..config import DEFAULT_CHARACTER


@dataclass
class Store:
    """Represents the application's persistent state."""
    
    sources: Dict[str, Source] = field(default_factory=dict)
    active_source: Optional[str] = None
    characters: Dict[str, Character] = field(default_factory=dict)
    active_character: str = DEFAULT_CHARACTER
    memory_enabled: bool = False
    
    def __post_init__(self):
        """Ensure default character exists."""
        if DEFAULT_CHARACTER not in self.characters:
            self.characters[DEFAULT_CHARACTER] = Character(DEFAULT_CHARACTER, "")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Store:
        """Create Store instance from dictionary data."""
        # Convert sources
        sources = {}
        for name, source_data in data.get("sources", {}).items():
            sources[name] = Source.from_dict(name, source_data)
        
        # Convert characters
        characters = {}
        for name, setting in data.get("characters", {}).items():
            characters[name] = Character.from_dict(name, setting)
        
        return cls(
            sources=sources,
            active_source=data.get("active"),
            characters=characters,
            active_character=data.get("active_character", DEFAULT_CHARACTER),
            memory_enabled=data.get("memory_enabled", False),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Store instance to dictionary."""
        return {
            "sources": {name: source.to_dict() for name, source in self.sources.items()},
            "active": self.active_source,
            "characters": {name: char.setting for name, char in self.characters.items()},
            "active_character": self.active_character,
            "memory_enabled": self.memory_enabled,
        }
    
    def get_active_source(self) -> Optional[Source]:
        """Get the currently active source."""
        if not self.active_source:
            return None
        return self.sources.get(self.active_source)
    
    def get_active_character(self) -> Character:
        """Get the currently active character."""
        char = self.characters.get(self.active_character)
        if char is None:
            # Fallback to default character
            char = self.characters.get(DEFAULT_CHARACTER)
            if char is None:
                char = Character(DEFAULT_CHARACTER, "")
                self.characters[DEFAULT_CHARACTER] = char
            self.active_character = DEFAULT_CHARACTER
        return char
    
    def add_source(self, source: Source) -> None:
        """Add a new source to the store."""
        self.sources[source.name] = source
    
    def remove_source(self, name: str) -> bool:
        """Remove a source from the store. Returns True if removed."""
        if name not in self.sources:
            return False
        
        del self.sources[name]
        
        # Reset active source if it was the removed one
        if self.active_source == name:
            self.active_source = next(iter(self.sources)) if self.sources else None
        
        return True
    
    def add_character(self, character: Character) -> None:
        """Add a new character to the store."""
        self.characters[character.name] = character
    
    def remove_character(self, name: str) -> bool:
        """Remove a character from the store. Returns True if removed."""
        if name not in self.characters or name == DEFAULT_CHARACTER:
            return False
        
        del self.characters[name]
        
        # Reset active character if it was the removed one
        if self.active_character == name:
            self.active_character = DEFAULT_CHARACTER
        
        return True
