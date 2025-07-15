"""Service for managing memory functionality."""
from __future__ import annotations

from typing import Optional

from ..repositories import StoreRepository
from ..exceptions import MemoryNotEnabledError


class MemoryService:
    """Service for managing memory functionality."""
    
    def __init__(self, store_repo: Optional[StoreRepository] = None):
        """Initialize the service with a store repository."""
        self.store_repo = store_repo or StoreRepository()
    
    def is_enabled(self) -> bool:
        """Check if memory functionality is enabled."""
        store = self.store_repo.load()
        return store.memory_enabled
    
    def enable(self) -> None:
        """Enable memory functionality."""
        store = self.store_repo.load()
        if not store.memory_enabled:
            store.memory_enabled = True
            self.store_repo.save(store)
    
    def disable(self) -> None:
        """Disable memory functionality."""
        store = self.store_repo.load()
        if store.memory_enabled:
            store.memory_enabled = False
            self.store_repo.save(store)
    
    def toggle(self) -> bool:
        """Toggle memory functionality and return new state."""
        store = self.store_repo.load()
        store.memory_enabled = not store.memory_enabled
        self.store_repo.save(store)
        return store.memory_enabled
    
    def ensure_enabled(self) -> None:
        """Ensure memory is enabled, raise exception if not."""
        if not self.is_enabled():
            raise MemoryNotEnabledError("Memory functionality is not enabled")
