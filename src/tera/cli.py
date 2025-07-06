"""命令行入口模块。"""
from __future__ import annotations

import sys
from typing import Any, Dict

import click

from .storage import load_store, save_store, get_active_source
from .chat import chat_mode

__all__ = ["main"]


@click.group(invoke_without_command=True)
@click.pass_context
def tera_cli(ctx: click.Context) -> None:  # noqa: D401
    """Tera Terminal AI 命令行工具。直接执行 `tera` 进入聊天模式。"""
    if ctx.invoked_subcommand is None:
        chat_mode()


# ===== 子命令: source =====

@tera_cli.group()
def source() -> None:  # noqa: D401
    """管理 LLM API 源。"""


@source.command("add")
def source_add() -> None:
    """添加新的 API 源。"""
    name = click.prompt("请输入源名称")
    base_url = click.prompt("请输入 API base_url", default="https://api.openai.com/v1")
    api_key = click.prompt("请输入 API Key", hide_input=True)
    model = click.prompt("请输入模型名", default="gpt-3.5-turbo")

    store = load_store()
    store["sources"][name] = {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    }
    # 如未设置当前源，则自动设为刚添加的源
    if not store.get("active"):
        store["active"] = name
    save_store(store)
    click.echo(f"已添加源 {name}")


@source.command("use")
@click.argument("name")
def source_use(name: str) -> None:
    """切换当前源。"""
    store = load_store()
    if name not in store["sources"]:
        click.echo(f"源 {name} 不存在。")
        sys.exit(1)
    store["active"] = name
    save_store(store)
    click.echo(f"已切换到源 {name}")


@source.command("show")
def source_show() -> None:
    """显示所有源及当前使用的源。"""
    store = load_store()
    if not store["sources"]:
        click.echo("暂无任何源，请先添加。")
        return

    active = store.get("active")
    click.echo("可用源列表：")
    for name, cfg in store["sources"].items():
        marker = "*" if name == active else " "
        click.echo(f"{marker} {name} -> {cfg['model']} ({cfg['base_url']})")
    if active:
        click.echo(f"\n当前源: {active}")


@source.command("delete")
@click.argument("name")
def source_delete(name: str) -> None:
    """删除指定源。"""
    store = load_store()
    if name not in store["sources"]:
        click.echo(f"源 {name} 不存在。")
        return

    if not click.confirm(f"确认删除源 {name} 吗？", default=False):
        click.echo("已取消删除。")
        return

    del store["sources"][name]
    # 如果删除的是当前源，则重置当前源
    if store.get("active") == name:
        store["active"] = next(iter(store["sources"])) if store["sources"] else None
    save_store(store)
    click.echo(f"已删除源 {name}")


# ===== 入口 =====

def main() -> None:
    """CLI 入口。使得 `python -m tera` 或 `tera_cli.py` 可运行。"""
    tera_cli() 