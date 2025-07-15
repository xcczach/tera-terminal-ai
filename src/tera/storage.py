"""Legacy storage module for backward compatibility.

This module is deprecated. Use the new repository and service layers instead.
"""
from __future__ import annotations

import warnings
from typing import Any, Dict, Tuple

from .repositories import StoreRepository
from .models import Store

# Backward compatibility
from .config import get_project_root, get_data_dir

PROJECT_ROOT = get_project_root()
DATA_DIR = get_data_dir()
SOURCES_FILE = DATA_DIR / "sources.json"

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "SOURCES_FILE",
    "load_store",
    "save_store",
    "get_active_source",
    "get_active_character",
]

def _default_store() -> Dict[str, Any]:
    """返回默认空存储结构，包括角色。

    Deprecated: Use Store model instead.
    """
    warnings.warn(
        "_default_store is deprecated. Use Store model instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return {
        "sources": {},
        "active": None,  # 当前源
        "characters": {"default": ""},  # 角色名 -> prompt
        "active_character": "default",  # 当前角色
        "memory_enabled": False,  # 是否启用记忆
    }


def load_store() -> Dict[str, Any]:
    """载入本地 store 数据。若文件不存在则返回默认结构。

    Deprecated: Use StoreRepository instead.
    """
    warnings.warn(
        "load_store is deprecated. Use StoreRepository instead.",
        DeprecationWarning,
        stacklevel=2
    )
    repo = StoreRepository()
    store = repo.load()
    return store.to_dict()


def save_store(data: Dict[str, Any]) -> None:
    """保存 store 数据到本地 json 文件。

    Deprecated: Use StoreRepository instead.
    """
    warnings.warn(
        "save_store is deprecated. Use StoreRepository instead.",
        DeprecationWarning,
        stacklevel=2
    )
    repo = StoreRepository()
    store = Store.from_dict(data)
    repo.save(store)


def get_active_source() -> Dict[str, Any] | None:
    """获取当前激活的源配置。

    Deprecated: Use SourceService instead.
    """
    warnings.warn(
        "get_active_source is deprecated. Use SourceService instead.",
        DeprecationWarning,
        stacklevel=2
    )
    repo = StoreRepository()
    store = repo.load()
    source = store.get_active_source()
    return source.to_dict() if source else None


def get_active_character() -> Tuple[str, str]:
    """返回 (角色名, 角色设定)。若未设置则返回 ("default", "")。

    Deprecated: Use CharacterService instead.
    """
    warnings.warn(
        "get_active_character is deprecated. Use CharacterService instead.",
        DeprecationWarning,
        stacklevel=2
    )
    repo = StoreRepository()
    store = repo.load()
    character = store.get_active_character()
    return character.name, character.setting