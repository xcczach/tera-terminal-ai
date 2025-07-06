"""角色记忆管理。实现：
1. 将文本及其嵌入保存在本地 JSONL
2. 提供相似度检索接口
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import List, Dict
from datetime import datetime

import numpy as np

# 检查 PyTorch 是否安装
try:
    import torch  # noqa: F401
except ImportError as _e:  # pragma: no cover
    torch = None  # type: ignore

from sentence_transformers import SentenceTransformer

from .storage import DATA_DIR

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

_model_lock = threading.Lock()
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    with _model_lock:
        if _model is None:
            if torch is None:
                raise RuntimeError(
                    "未检测到 PyTorch。请先执行 `pip install torch --index-url https://download.pytorch.org/whl/cpu` "
                    "或安装适用于 GPU 的版本，然后重新运行。"
                )
            _model = SentenceTransformer(MODEL_NAME)
        return _model


# ---------------- 路径工具 ----------------

def _mem_file(character: str) -> Path:
    return DATA_DIR / f"memory_{character}.jsonl"


def _log_file(character: str) -> Path:
    return DATA_DIR / f"chatlog_{character}.jsonl"


# ---------------- 存储与检索 ----------------

def add_memory(character: str, text: str) -> None:
    """将文本写入记忆文件并生成嵌入。"""
    clean = text.strip()
    if not clean or clean.lower() in {"空", "无", "none", "null"}:
        return  # 跳过无意义记忆

    emb = _get_model().encode([clean])[0].tolist()
    record = {"text": clean, "embedding": emb}
    with _mem_file(character).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_memory_records(character: str) -> List[Dict]:
    file = _mem_file(character)
    if not file.exists():
        return []
    records: List[Dict] = []
    with file.open(encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def retrieve_similar(character: str, query: str, top_k: int = 5) -> List[str]:
    """检索相似记忆文本。"""
    records = _load_memory_records(character)
    if not records:
        return []
    model = _get_model()
    q_emb = model.encode([query])[0]
    mem_embs = np.array([r["embedding"] for r in records])
    # 归一化
    mem_norm = mem_embs / np.linalg.norm(mem_embs, axis=1, keepdims=True)
    q_norm = q_emb / np.linalg.norm(q_emb)
    sims = mem_norm @ q_norm
    idx = sims.argsort()[::-1][:top_k]
    return [records[i]["text"] for i in idx]


# ---------------- 聊天日志 ----------------

def append_chat_log(character: str, role: str, content: str) -> None:
    record = {
        "role": role,
        "content": content,
        "ts": datetime.now().isoformat(sep=" ", timespec="seconds"),
    }
    with _log_file(character).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_chat_log(character: str) -> List[Dict[str, str]]:
    file = _log_file(character)
    if not file.exists():
        return []
    logs: List[Dict[str, str]] = []
    with file.open(encoding="utf-8") as f:
        for line in f:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    # 按时间戳排序，若不存在 ts 字段则保持原有顺序
    try:
        logs.sort(key=lambda x: x.get("ts", ""))
    except Exception:
        pass
    return logs


def clear_chat_log(character: str) -> None:
    """清空对应角色的聊天日志文件。"""
    file = _log_file(character)
    if file.exists():
        file.write_text("", encoding="utf-8") 