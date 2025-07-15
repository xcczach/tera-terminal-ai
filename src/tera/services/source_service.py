"""Service for managing LLM sources."""
from __future__ import annotations

from typing import List, Optional

from ..models import Source, Store
from ..repositories import StoreRepository
from ..exceptions import SourceNotFoundError, NoActiveSourceError


class SourceService:
    """Service for managing LLM API sources."""
    
    def __init__(self, store_repo: Optional[StoreRepository] = None):
        """Initialize the service with a store repository."""
        self.store_repo = store_repo or StoreRepository()
    
    def add_source(self, name: str, base_url: str, api_key: str, model: str) -> Source:
        """Add a new source and save to store."""
        source = Source(name=name, base_url=base_url, api_key=api_key, model=model)
        
        store = self.store_repo.load()
        store.add_source(source)
        self.store_repo.save(store)
        
        return source
    
    def get_source(self, name: str) -> Source:
        """Get a source by name."""
        store = self.store_repo.load()
        source = store.sources.get(name)
        if source is None:
            raise SourceNotFoundError(f"Source '{name}' not found")
        return source
    
    def get_all_sources(self) -> List[Source]:
        """Get all available sources."""
        store = self.store_repo.load()
        return list(store.sources.values())
    
    def get_active_source(self) -> Source:
        """Get the currently active source."""
        store = self.store_repo.load()
        source = store.get_active_source()
        if source is None:
            raise NoActiveSourceError("No active source configured")
        return source
    
    def set_active_source(self, name: str) -> Source:
        """Set the active source."""
        store = self.store_repo.load()
        if name not in store.sources:
            raise SourceNotFoundError(f"Source '{name}' not found")
        
        store.active_source = name
        self.store_repo.save(store)
        
        return store.sources[name]
    
    def remove_source(self, name: str) -> bool:
        """Remove a source."""
        store = self.store_repo.load()
        removed = store.remove_source(name)
        if removed:
            self.store_repo.save(store)
        return removed
    
    def source_exists(self, name: str) -> bool:
        """Check if a source exists."""
        store = self.store_repo.load()
        return name in store.sources
    
    def get_active_source_name(self) -> Optional[str]:
        """Get the name of the active source."""
        store = self.store_repo.load()
        return store.active_source
    
    def has_sources(self) -> bool:
        """Check if any sources are configured."""
        store = self.store_repo.load()
        return len(store.sources) > 0
