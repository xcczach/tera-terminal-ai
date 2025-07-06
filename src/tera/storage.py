"""数据存取模块。

负责 sources.json 的读写及目录初始化。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR",
    "SOURCES_FILE",
    "load_store",
    "save_store",
    "get_active_source",
]

# data 目录位于项目根目录（即 src 之上）
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
SOURCES_FILE: Path = DATA_DIR / "sources.json"


def _default_store() -> Dict[str, Any]:
    """返回默认空存储结构。"""
    return {"sources": {}, "active": None}


def load_store() -> Dict[str, Any]:
    """载入本地 store 数据。若文件不存在则返回默认结构。"""
    if not SOURCES_FILE.exists():
        return _default_store()
    try:
        with SOURCES_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # 若文件损坏，回到初始状态
        return _default_store()


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