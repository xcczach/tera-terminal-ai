"""Repository for store data persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models import Store
from ..config import get_data_dir, SOURCES_FILENAME
from ..exceptions import StorageError


class StoreRepository:
    """Repository for managing store data persistence."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the repository with data directory."""
        self.data_dir = data_dir or get_data_dir()
        self.store_file = self.data_dir / SOURCES_FILENAME
    
    def load(self) -> Store:
        """Load store data from file."""
        if not self.store_file.exists():
            return Store()
        
        try:
            with self.store_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return Store.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise StorageError(f"Failed to load store data: {e}") from e
    
    def save(self, store: Store) -> None:
        """Save store data to file."""
        try:
            # Ensure data directory exists
            self.data_dir.mkdir(exist_ok=True)
            
            with self.store_file.open("w", encoding="utf-8") as f:
                json.dump(store.to_dict(), f, ensure_ascii=False, indent=2)
        except (OSError, ValueError) as e:
            raise StorageError(f"Failed to save store data: {e}") from e
    
    def exists(self) -> bool:
        """Check if store file exists."""
        return self.store_file.exists()
    
    def backup(self, suffix: str = ".backup") -> Path:
        """Create a backup of the store file."""
        if not self.store_file.exists():
            raise StorageError("Store file does not exist, cannot create backup")
        
        backup_path = self.store_file.with_suffix(self.store_file.suffix + suffix)
        try:
            backup_path.write_bytes(self.store_file.read_bytes())
            return backup_path
        except OSError as e:
            raise StorageError(f"Failed to create backup: {e}") from e
