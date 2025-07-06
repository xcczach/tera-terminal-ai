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

from .storage import get_active_source, get_active_character

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
            console.print("[bold green]AI>[/bold green]")
            console.print(Markdown(reply))
        except Exception as e:
            click.echo(f"生成问候失败: {e}")
            reply = ""

    if reply:
        messages.append({"role": "assistant", "content": reply})

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

        messages.append({"role": "user", "content": user_input})

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
            console.print("[bold green]AI>[/bold green]")
            console.print(Markdown(reply))
        except Exception:
            # 若流式失败，退回非流式
            try:
                response = client.chat.completions.create(
                    model=src["model"],
                    messages=messages,
                )
                reply = response.choices[0].message.content.strip()
                console.print("[bold green]AI>[/bold green]")
                console.print(Markdown(reply))
            except Exception as e2:  # noqa: BLE001
                click.echo(f"请求出错: {e2}")
                continue

        # 将回复加入上下文，便于后续对话
        messages.append({"role": "assistant", "content": reply})
 