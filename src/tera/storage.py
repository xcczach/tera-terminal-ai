"""数据存取模块。

负责 sources.json 的读写及目录初始化。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
import sys

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "SOURCES_FILE",
    "load_store",
    "save_store",
    "get_active_source",
    "get_active_character",
]

def _get_project_root() -> Path:
    """返回运行时的项目根目录。

    - PyInstaller 单文件模式下，`sys.executable` 指向可执行文件路径；
      我们以其所在目录为根。
    - 源码运行时，仍使用包文件的上级目录。
    """
    if getattr(sys, "frozen", False):  # PyInstaller 环境
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


# data 目录位于项目根目录
PROJECT_ROOT: Path = _get_project_root()
DATA_DIR: Path = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
SOURCES_FILE: Path = DATA_DIR / "sources.json"


def _default_store() -> Dict[str, Any]:
    """返回默认空存储结构，包括角色。"""
    return {
        "sources": {},
        "active": None,  # 当前源
        "characters": {"default": ""},  # 角色名 -> prompt
        "active_character": "default",  # 当前角色
        "memory_enabled": False,  # 是否启用记忆
    }


def load_store() -> Dict[str, Any]:
    """载入本地 store 数据。若文件不存在则返回默认结构。"""
    if not SOURCES_FILE.exists():
        return _default_store()
    try:
        with SOURCES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        # 若文件损坏，回到初始状态
        return _default_store()

    # 确保新字段存在（向后兼容旧文件）
    changed = False
    default = _default_store()
    for key, value in default.items():
        if key not in data:
            data[key] = value
            changed = True
    if changed:
        save_store(data)
    return data


def save_store(data: Dict[str, Any]) -> None:
    """保存 store 数据到本地 json 文件。"""
    with SOURCES_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_active_source() -> Dict[str, Any] | None:
    """获取当前激活的源配置。"""
    store = load_store()
    active_name: str | None = store.get("active")
    if not active_name:
        return None
    return store["sources"].get(active_name)


def get_active_character() -> tuple[str, str]:
    """返回 (角色名, 角色设定)。若未设置则返回 ("default", "")."""
    store = load_store()
    name: str = store.get("active_character", "default")
    setting = store["characters"].get(name, "")
    return name, setting 