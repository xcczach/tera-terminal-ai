"""Character model for role-playing configurations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from ..config import MAX_CHARACTER_PREVIEW_LENGTH


@dataclass
class Character:
    """Represents a character/role configuration."""
    
    name: str
    setting: str
    
    @classmethod
    def from_dict(cls, name: str, setting: str) -> Character:
        """Create a Character instance from name and setting."""
        return cls(name=name, setting=setting)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert Character instance to dictionary."""
        return {"name": self.name, "setting": self.setting}
    
    def get_system_message(self) -> str:
        """Generate system message for this character."""
        if not self.setting:
            return ""
        
        return (
            f"你是{self.name}，聊天过程中要遵循以下设定：\n{self.setting}\n"
            "\"系统提示：\"后不是用户输入，你需要遵循系统提示做出响应。"
        )
    
    def get_preview(self) -> str:
        """Get a short preview of the character setting."""
        if not self.setting:
            return "空设定"
        
        if len(self.setting) <= MAX_CHARACTER_PREVIEW_LENGTH:
            return self.setting
        
        return self.setting[:MAX_CHARACTER_PREVIEW_LENGTH] + "…"
    
    def __str__(self) -> str:
        """String representation of the character."""
        return f"{self.name} -> {self.get_preview()}"
