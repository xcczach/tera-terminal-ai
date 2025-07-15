"""Custom exceptions for Tera Terminal AI."""
from __future__ import annotations


class TeraError(Exception):
    """Base exception for all Tera Terminal AI errors."""
    pass


class SourceError(TeraError):
    """Errors related to LLM source management."""
    pass


class SourceNotFoundError(SourceError):
    """Raised when a requested source is not found."""
    pass


class NoActiveSourceError(SourceError):
    """Raised when no active source is configured."""
    pass


class CharacterError(TeraError):
    """Errors related to character management."""
    pass


class CharacterNotFoundError(CharacterError):
    """Raised when a requested character is not found."""
    pass


class MemoryError(TeraError):
    """Errors related to memory functionality."""
    pass


class MemoryNotEnabledError(MemoryError):
    """Raised when memory functionality is not enabled."""
    pass


class CodeExecutionError(TeraError):
    """Errors related to code execution."""
    pass


class StorageError(TeraError):
    """Errors related to data storage and retrieval."""
    pass


class APIError(TeraError):
    """Errors related to LLM API calls."""
    pass
