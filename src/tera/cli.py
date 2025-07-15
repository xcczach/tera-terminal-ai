"""命令行入口模块。"""
from __future__ import annotations

import sys

import click

from .services import SourceService, CharacterService, MemoryService
from .chat import ChatSession
from .exceptions import (
    SourceNotFoundError,
    NoActiveSourceError,
    CharacterNotFoundError,
    StorageError,
)

__all__ = ["main"]


@click.group(invoke_without_command=True)
@click.pass_context
def tera_cli(ctx: click.Context) -> None:  # noqa: D401
    """Tera Terminal AI 命令行工具。直接执行 `tera` 进入聊天模式。"""
    if ctx.invoked_subcommand is None:
        chat_session = ChatSession()
        chat_session.start()


# ========== help 命令 ==========


@tera_cli.command("help", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
def _help(ctx: click.Context) -> None:
    """显示帮助信息，与 --help 等价。"""
    if ctx.args:
        # 若指定子命令，显示子命令帮助
        cmd_name = ctx.args[0]
        cmd = tera_cli.get_command(ctx, cmd_name)
        if cmd is None:
            click.echo(f"未知命令: {cmd_name}")
            ctx.exit(1)
        click.echo(cmd.get_help(ctx))
    else:
        click.echo(tera_cli.get_help(ctx))


# ===== 子命令: source =====

@tera_cli.group()
def source() -> None:  # noqa: D401
    """管理 LLM API 源。"""


@source.command("add")
def source_add() -> None:
    """添加新的 API 源。"""
    name = click.prompt("请输入源名称")
    base_url = click.prompt("请输入 API base_url", default="https://api.openai.com/v1")
    api_key = click.prompt("请输入 API Key")
    model = click.prompt("请输入模型名", default="gpt-3.5-turbo")

    try:
        source_service = SourceService()
        source = source_service.add_source(name, base_url, api_key, model)
        click.echo(f"已添加源 {name}")
        click.echo(f"API Key: {api_key}")

        # 若未设置当前源，或用户确认切换，则切换
        if not source_service.get_active_source_name() or click.confirm(f"是否立即切换到源 {name}?", default=True):
            source_service.set_active_source(name)
            click.echo(f"已切换到源 {name}")
    except StorageError as e:
        click.echo(f"保存源配置失败: {e}")
        sys.exit(1)


@source.command("use")
@click.argument("name")
def source_use(name: str) -> None:
    """切换当前源。"""
    try:
        source_service = SourceService()
        source_service.set_active_source(name)
        click.echo(f"已切换到源 {name}")
    except SourceNotFoundError:
        click.echo(f"源 {name} 不存在。")
        sys.exit(1)
    except StorageError as e:
        click.echo(f"切换源失败: {e}")
        sys.exit(1)


@source.command("show")
def source_show() -> None:
    """显示所有源及当前使用的源。"""
    try:
        source_service = SourceService()
        sources = source_service.get_all_sources()

        if not sources:
            click.echo("暂无任何源，请先添加。")
            return

        active_name = source_service.get_active_source_name()
        click.echo("可用源列表：")
        for source in sources:
            marker = "*" if source.name == active_name else " "
            click.echo(f"{marker} {source}")
        if active_name:
            click.echo(f"\n当前源: {active_name}")
    except StorageError as e:
        click.echo(f"读取源配置失败: {e}")
        sys.exit(1)


@source.command("delete")
@click.argument("name")
def source_delete(name: str) -> None:
    """删除指定源。"""
    try:
        source_service = SourceService()

        if not source_service.source_exists(name):
            click.echo(f"源 {name} 不存在。")
            return

        if not click.confirm(f"确认删除源 {name} 吗？", default=False):
            click.echo("已取消删除。")
            return

        source_service.remove_source(name)
        click.echo(f"已删除源 {name}")
    except StorageError as e:
        click.echo(f"删除源失败: {e}")
        sys.exit(1)


# ===== 入口 =====

def main() -> None:
    """CLI 入口。使得 `python -m tera` 或 `tera_cli.py` 可运行。"""
    tera_cli()


############################################
# character 子命令组
############################################


@tera_cli.group()
def character() -> None:  # noqa: D401
    """管理角色设定。"""


@character.command("add")
def character_add() -> None:
    """添加新角色。"""
    name = click.prompt("请输入角色名称")
    setting = click.prompt("请输入角色设定(可留空)", default="")

    try:
        character_service = CharacterService()

        if character_service.character_exists(name):
            click.echo("角色已存在，覆盖旧设定。")

        character = character_service.add_character(name, setting)
        click.echo(f"已添加角色 {name}")

        # 询问是否切换到该角色
        if click.confirm(f"是否立即切换到角色 {name}?", default=True):
            character_service.set_active_character(name)
            click.echo(f"已切换到角色 {name}")
    except StorageError as e:
        click.echo(f"保存角色失败: {e}")
        sys.exit(1)


@character.command("use")
@click.argument("name")
def character_use(name: str) -> None:
    """切换当前角色。"""
    try:
        character_service = CharacterService()
        character_service.set_active_character(name)
        click.echo(f"已切换到角色 {name}")
    except CharacterNotFoundError:
        click.echo(f"角色 {name} 不存在。")
        sys.exit(1)
    except StorageError as e:
        click.echo(f"切换角色失败: {e}")
        sys.exit(1)


@character.command("show")
@click.argument("name", required=False)
def character_show(name: str | None = None) -> None:
    """显示角色列表或指定角色设定。"""
    try:
        character_service = CharacterService()

        if name:
            try:
                character = character_service.get_character(name)
                click.echo(f"角色 {name} 的完整设定:\n{character.setting}")
            except CharacterNotFoundError:
                click.echo(f"角色 {name} 不存在。")
                sys.exit(1)
            return

        characters = character_service.get_all_characters()
        if not characters:
            click.echo("暂无角色，请先添加。")
            return

        active_name = character_service.get_active_character_name()
        click.echo("可用角色列表：")
        for character in characters:
            marker = "*" if character.name == active_name else " "
            click.echo(f"{marker} {character}")
        if active_name:
            click.echo(f"\n当前角色: {active_name}")
    except StorageError as e:
        click.echo(f"读取角色配置失败: {e}")
        sys.exit(1)


@character.command("delete")
@click.argument("name")
def character_delete(name: str) -> None:
    """删除指定角色。"""
    try:
        character_service = CharacterService()

        if not character_service.character_exists(name):
            click.echo(f"角色 {name} 不存在。")
            return

        if not click.confirm(f"确认删除角色 {name} 吗？", default=False):
            click.echo("已取消删除。")
            return

        if character_service.remove_character(name):
            click.echo(f"已删除角色 {name}")
        else:
            click.echo("无法删除默认角色。")
    except StorageError as e:
        click.echo(f"删除角色失败: {e}")
        sys.exit(1)


############################################
# memory 开关
############################################


@tera_cli.group()
def memory() -> None:
    """记忆功能开关。"""


@memory.command("on")
def memory_on() -> None:
    try:
        memory_service = MemoryService()
        if memory_service.is_enabled():
            click.echo("记忆功能已启用。")
            return
        memory_service.enable()
        click.echo("已启用记忆功能。首次使用将自动下载嵌入模型并可能较慢。")
    except StorageError as e:
        click.echo(f"启用记忆功能失败: {e}")
        sys.exit(1)


@memory.command("off")
def memory_off() -> None:
    try:
        memory_service = MemoryService()
        if not memory_service.is_enabled():
            click.echo("记忆功能本已关闭。")
            return
        memory_service.disable()
        click.echo("已关闭记忆功能。后续聊天将不再记录与检索记忆。")
    except StorageError as e:
        click.echo(f"关闭记忆功能失败: {e}")
        sys.exit(1)


@memory.command("show")
def memory_show() -> None:
    try:
        memory_service = MemoryService()
        enabled = memory_service.is_enabled()
        status = "启用" if enabled else "关闭"
        click.echo(f"记忆功能当前状态：{status}")
    except StorageError as e:
        click.echo(f"读取记忆功能状态失败: {e}")
        sys.exit(1)