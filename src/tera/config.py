"""Configuration constants and settings for Tera Terminal AI."""
from __future__ import annotations

from pathlib import Path
import sys

# Default values
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_CHARACTER = "default"

# Memory settings
MEMORY_MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
MAX_MEMORY_ITEMS = 500
SUMMARY_BATCH = 100

# Code execution settings
SUPPORTED_LANGUAGES = {"python", "py", "bash", "sh", "shell"}

# File patterns
SOURCES_FILENAME = "sources.json"
MEMORY_INDEX_PATTERN = "memory_{character}.index"
MEMORY_META_PATTERN = "memory_{character}.meta"
CHAT_LOG_PATTERN = "chatlog_{character}.jsonl"

# UI settings
MAX_CHARACTER_PREVIEW_LENGTH = 30

def get_project_root() -> Path:
    """返回运行时的项目根目录。
    
    - PyInstaller 单文件模式下，`sys.executable` 指向可执行文件路径；
      我们以其所在目录为根。
    - 源码运行时，仍使用包文件的上级目录。
    """
    if getattr(sys, "frozen", False):  # PyInstaller 环境
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent

def get_data_dir() -> Path:
    """获取数据目录路径。"""
    data_dir = get_project_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir
