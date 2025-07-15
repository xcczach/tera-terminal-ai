"""Service for managing characters."""
from __future__ import annotations

from typing import List, Optional

from ..models import Character, Store
from ..repositories import StoreRepository
from ..exceptions import CharacterNotFoundError
from ..config import DEFAULT_CHARACTER


class CharacterService:
    """Service for managing character configurations."""
    
    def __init__(self, store_repo: Optional[StoreRepository] = None):
        """Initialize the service with a store repository."""
        self.store_repo = store_repo or StoreRepository()
    
    def add_character(self, name: str, setting: str) -> Character:
        """Add a new character and save to store."""
        character = Character(name=name, setting=setting)
        
        store = self.store_repo.load()
        store.add_character(character)
        self.store_repo.save(store)
        
        return character
    
    def get_character(self, name: str) -> Character:
        """Get a character by name."""
        store = self.store_repo.load()
        character = store.characters.get(name)
        if character is None:
            raise CharacterNotFoundError(f"Character '{name}' not found")
        return character
    
    def get_all_characters(self) -> List[Character]:
        """Get all available characters."""
        store = self.store_repo.load()
        return list(store.characters.values())
    
    def get_active_character(self) -> Character:
        """Get the currently active character."""
        store = self.store_repo.load()
        return store.get_active_character()
    
    def set_active_character(self, name: str) -> Character:
        """Set the active character."""
        store = self.store_repo.load()
        if name not in store.characters:
            raise CharacterNotFoundError(f"Character '{name}' not found")
        
        store.active_character = name
        self.store_repo.save(store)
        
        return store.characters[name]
    
    def remove_character(self, name: str) -> bool:
        """Remove a character (cannot remove default character)."""
        if name == DEFAULT_CHARACTER:
            return False
        
        store = self.store_repo.load()
        removed = store.remove_character(name)
        if removed:
            self.store_repo.save(store)
        return removed
    
    def character_exists(self, name: str) -> bool:
        """Check if a character exists."""
        store = self.store_repo.load()
        return name in store.characters
    
    def get_active_character_name(self) -> str:
        """Get the name of the active character."""
        store = self.store_repo.load()
        return store.active_character
    
    def update_character(self, name: str, setting: str) -> Character:
        """Update an existing character's setting."""
        store = self.store_repo.load()
        if name not in store.characters:
            raise CharacterNotFoundError(f"Character '{name}' not found")
        
        character = Character(name=name, setting=setting)
        store.characters[name] = character
        self.store_repo.save(store)
        
        return character
