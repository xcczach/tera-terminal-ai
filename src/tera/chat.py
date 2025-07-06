"""聊天模式实现。"""
from __future__ import annotations

import sys
from typing import List, Dict, Any

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

    # 加入角色 system message
    _char_name, char_setting = get_active_character()
    messages: List[Dict[str, Any]] = []
    if char_setting:
        messages.append({"role": "system", "content": char_setting})

    click.echo("进入聊天模式，输入 exit / quit 退出。\n")

    while True:
        try:
            user_input = input("你> ").strip()
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
            response = client.chat.completions.create(
                model=src["model"],
                messages=messages,
            )
            reply = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": reply})
            print(f"AI> {reply}\n")
        except Exception as e:  # noqa: BLE001
            click.echo(f"请求出错: {e}") 