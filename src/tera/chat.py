"""聊天模式实现。"""
from __future__ import annotations

import sys
from typing import List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown

import click

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    print("未安装 openai，请先执行: pip install openai")
    sys.exit(1)

from .storage import get_active_source, get_active_character, load_store

__all__ = ["chat_mode"]


def chat_mode() -> None:
    """启动交互式聊天。"""
    src = get_active_source()
    if not src:
        click.echo("尚未配置任何源，请先执行 `tera source add`。")
        sys.exit(1)

    client = OpenAI(api_key=src["api_key"], base_url=src["base_url"])
    console = Console()

    # 加入角色 system message
    _char_name, char_setting = get_active_character()
    messages: List[Dict[str, Any]] = []
    if char_setting:
        char_setting = f"你是{_char_name}，聊天过程中要遵循以下设定：\n{char_setting}\n\"系统提示：\"后不是用户输入，你需要遵循系统提示做出响应。"
        messages.append({"role": "system", "content": char_setting})

    # -------- 异步提炼上一轮聊天记忆 -------- #
    import threading

    _mem_enabled = load_store().get("memory_enabled", False)

    if _mem_enabled:
        from .memory import (
            append_chat_log,
            retrieve_similar,
            add_memory,
            read_chat_log,
            clear_chat_log,
        )
    else:
        # 定义空实现以避免导入重量级依赖
        def append_chat_log(*args, **kwargs):
            return None

        def retrieve_similar(*args, **kwargs):
            return []

        def add_memory(*args, **kwargs):
            return None

        def read_chat_log(*args, **kwargs):
            return []

    # 读取上一轮日志并立即清空文件（无论是否启用记忆，以免累积）
    prev_logs = []
    try:
        if _mem_enabled:
            prev_logs = read_chat_log(_char_name)
            clear_chat_log(_char_name)
        else:
            # 仅清空文件
            from pathlib import Path
            from .storage import DATA_DIR

            (_log := (DATA_DIR / f"chatlog_{_char_name}.jsonl")) and _log.write_text("", encoding="utf-8")
    except Exception:
        prev_logs = []

    if _mem_enabled and prev_logs:

        def _extract_last_session_memory() -> None:
            logs = prev_logs
            # 拼接适量文本发送给模型提取关键点，加入时间戳
            convo_text = "\n".join(
                f"[{it.get('ts', '')}] {it['role']}: {it['content']}" for it in logs[-100:]
            )
            prompt = (
                "你是助手，任务：从用户和助手对话中提炼值得长期记忆的事实或偏好，"
                "每条不超过50字，用中文输出，每行一条。若无可记忆信息，输出空。\n对话:\n" + convo_text
            )
            try:
                # 流式优先
                stream_resp = client.chat.completions.create(
                    model=src["model"],
                    messages=[{"role": "system", "content": prompt}],
                    stream=True,
                )
                parts: list[str] = []
                for chunk in stream_resp:
                    delta = chunk.choices[0].delta
                    content_part = getattr(delta, "content", None)
                    if content_part:
                        parts.append(content_part)
                full = "".join(parts)
            except Exception:
                try:
                    resp = client.chat.completions.create(
                        model=src["model"],
                        messages=[{"role": "system", "content": prompt}],
                    )
                    full = resp.choices[0].message.content
                except Exception as e:  # noqa: BLE001
                    click.echo(f"提取记忆失败: {e}")
                    return

            lines = full.strip().splitlines()
            for ln in lines:
                ln = ln.strip("- \u2022\t")
                if ln:
                    add_memory(_char_name, ln)

    if _mem_enabled and prev_logs:
        threading.Thread(target=_extract_last_session_memory, daemon=True).start()

    # -------- 自动问候逻辑 -------- #
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    greet_prompt = (
        f"系统提示：当前日期和时间为 {now_str}，请首先向用户进行友好的问候，然后等待用户提问。"
    )
    messages.append({"role": "system", "content": greet_prompt})

    # 调用模型生成问候
    try:
        stream_resp = client.chat.completions.create(
            model=src["model"],
            messages=messages,
            stream=True,
        )
        reply_parts: list[str] = []
        for chunk in stream_resp:
            delta = chunk.choices[0].delta
            content_part = getattr(delta, "content", None)
            if content_part:
                reply_parts.append(content_part)
        reply = "".join(reply_parts).strip()
        console.print(f"[bold green]{_char_name}>[/bold green]")
        console.print(Markdown(reply))
    except Exception:
        try:
            response = client.chat.completions.create(
                model=src["model"],
                messages=messages,
            )
            reply = response.choices[0].message.content.strip()
            console.print(f"[bold green]{_char_name}>[/bold green]")
            console.print(Markdown(reply))
        except Exception as e:
            click.echo(f"生成问候失败: {e}")
            reply = ""

    if reply:
        messages.append({"role": "assistant", "content": reply})
        if _mem_enabled:
            append_chat_log(_char_name, "assistant", reply)

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("\n退出聊天。")
            break

        if user_input.lower() in {"exit", "quit"}:
            click.echo("退出聊天。")
            break
        if not user_input:
            continue

        # 先记录用户输入
        messages.append({"role": "user", "content": user_input})
        if _mem_enabled:
            append_chat_log(_char_name, "user", user_input)

        if _mem_enabled:
            related = retrieve_similar(_char_name, user_input, 5)
            if related:
                mem_text = "以下是与你的个人记忆相关的信息，请参考：\n" + "\n".join(f"- {t}" for t in related)
                messages.append({"role": "system", "content": mem_text})

        try:
            # 首先尝试流式模式
            stream_resp = client.chat.completions.create(
                model=src["model"],
                messages=messages,
                stream=True,
            )

            reply_parts: list[str] = []
            for chunk in stream_resp:
                delta = chunk.choices[0].delta
                content_part = getattr(delta, "content", None)
                if content_part:
                    reply_parts.append(content_part)
            reply = "".join(reply_parts).strip()
            console.print(f"[bold green]{_char_name}>[/bold green]")
            console.print(Markdown(reply))
        except Exception:
            # 若流式失败，退回非流式
            try:
                response = client.chat.completions.create(
                    model=src["model"],
                    messages=messages,
                )
                reply = response.choices[0].message.content.strip()
                console.print(f"[bold green]{_char_name}>[/bold green]")
                console.print(Markdown(reply))
            except Exception as e2:  # noqa: BLE001
                click.echo(f"请求出错: {e2}")
                continue

        # 将回复加入上下文，便于后续对话
        messages.append({"role": "assistant", "content": reply})
        if _mem_enabled:
            append_chat_log(_char_name, "assistant", reply)
 