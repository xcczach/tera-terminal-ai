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
except ImportError:  # pragma: no cover
    torch = None  # type: ignore

# 检查 faiss
try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover
    faiss = None  # type: ignore

from sentence_transformers import SentenceTransformer

from .storage import DATA_DIR

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

_model_lock = threading.Lock()
_model: SentenceTransformer | None = None

MAX_MEMORY_ITEMS = 500  # 超过此数量触发压缩
SUMMARY_BATCH = 100     # 取最早的多少条进行汇总


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

def _index_file(character: str) -> Path:
    return DATA_DIR / f"memory_{character}.index"


def _meta_file(character: str) -> Path:
    return DATA_DIR / f"memory_{character}_meta.jsonl"


def _log_file(character: str) -> Path:
    return DATA_DIR / f"chatlog_{character}.jsonl"


# ---------------- Index Helpers ----------------

def _get_index(character: str, dim: int):
    path = _index_file(character)
    if path.exists():
        return faiss.read_index(str(path))
    index = faiss.IndexFlatIP(dim)
    return index


def _save_index(character: str, index):
    faiss.write_index(index, str(_index_file(character)))


def _append_meta(character: str, text: str):
    with _meta_file(character).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")


def _load_meta(character: str):
    file = _meta_file(character)
    if not file.exists():
        return []
    meta = []
    with file.open(encoding="utf-8") as f:
        for line in f:
            try:
                meta.append(json.loads(line)["text"])
            except Exception:
                meta.append("")
    return meta


# ---------------- 存储与检索 ----------------

def add_memory(character: str, text: str) -> None:
    """新增记忆并写入 Faiss 索引 + meta。"""
    if faiss is None:
        raise RuntimeError("未安装 faiss，无法使用记忆索引功能。请 pip install faiss-cpu")

    clean = text.strip()
    if not clean or clean.lower() in {"空", "无", "none", "null"}:
        return

    emb = _get_model().encode([clean])[0]
    dim = emb.shape[0]
    # 归一化
    emb = emb / np.linalg.norm(emb)
    emb = emb.astype("float32").reshape(1, -1)

    index = _get_index(character, dim)
    index.add(emb)
    _save_index(character, index)
    _append_meta(character, clean)

    # 触发压缩检查
    _maybe_compact_memory(character)


def retrieve_similar(character: str, query: str, top_k: int = 5) -> List[str]:
    """使用 Faiss 检索相似记忆文本。"""
    if faiss is None:
        return []

    meta = _load_meta(character)
    if not meta:
        return []

    model = _get_model()
    q_emb = model.encode([query])[0]
    q_emb = q_emb / np.linalg.norm(q_emb)
    q_emb = q_emb.astype("float32").reshape(1, -1)

    index_path = _index_file(character)
    if not index_path.exists():
        return []
    index = faiss.read_index(str(index_path))
    D, I = index.search(q_emb, min(top_k, index.ntotal))
    result = []
    for idx in I[0]:
        if idx < len(meta):
            result.append(meta[idx])
    return result


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


def _maybe_compact_memory(character: str) -> None:
    """若记忆条数超过阈值，则让大模型总结 oldest SUMMARY_BATCH 条。"""
    meta = _load_meta(character)
    if len(meta) <= MAX_MEMORY_ITEMS:
        return

    batch = meta[:SUMMARY_BATCH]
    if not batch:
        return

    # 构造提示
    prompt = (
        "你是助手，请将以下多条用户相关记忆信息进行归纳压缩，"\
        "保留关键信息，输出不超过20条，每条不超过50字，中文，每行一条。\n\n" +
        "\n".join(f"- {t}" for t in batch)
    )

    # 动态导入 openai，避免未安装时报错
    try:
        from openai import OpenAI
        from .storage import load_store

        src = load_store()["sources"].get(load_store().get("active"))
        if not src:
            return
        client = OpenAI(api_key=src["api_key"], base_url=src["base_url"])

        try:
            resp = client.chat.completions.create(
                model=src["model"],
                messages=[{"role": "system", "content": prompt}],
            )
            summary_lines = [ln.strip("- \t") for ln in resp.choices[0].message.content.splitlines() if ln.strip()]
        except Exception:
            return

    except Exception:
        return

    if not summary_lines:
        return

    # 1. 重建索引：移除 batch 部分
    index_path = _index_file(character)
    if not index_path.exists():
        return

    index = faiss.read_index(str(index_path))
    dim = index.d
    total = index.ntotal
    vecs = np.zeros((total, dim), dtype="float32")
    for i in range(total):
        vecs[i] = index.reconstruct(i)

    # 保留后面部分
    remain_vecs = vecs[SUMMARY_BATCH:]
    remain_meta = meta[SUMMARY_BATCH:]

    # 创建新索引并添加剩余向量
    new_index = faiss.IndexFlatIP(dim)
    if remain_vecs.size:
        new_index.add(remain_vecs)

    # 2. 将总结结果作为新记忆加入
    for s in summary_lines:
        s_clean = s.strip()
        if not s_clean:
            continue
        emb = _get_model().encode([s_clean])[0]
        emb = emb / np.linalg.norm(emb)
        new_index.add(emb.astype("float32").reshape(1, -1))
        remain_meta.append(s_clean)

    # 保存新索引与 meta
    _save_index(character, new_index)
    _meta_file(character).write_text("\n".join(json.dumps({"text": t}, ensure_ascii=False) for t in remain_meta), encoding="utf-8") 