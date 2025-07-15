"""Legacy chat mode implementation.

This module is deprecated. Use ChatSession from .chat package instead.
"""
from __future__ import annotations

import warnings

from .chat import ChatSession

__all__ = ["chat_mode"]


def chat_mode() -> None:
    """启动交互式聊天。

    Deprecated: Use ChatSession instead.
    """
    warnings.warn(
        "chat_mode is deprecated. Use ChatSession instead.",
        DeprecationWarning,
        stacklevel=2
    )
    chat_session = ChatSession()
    chat_session.start()
 