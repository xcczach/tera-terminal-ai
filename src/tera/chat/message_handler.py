"""Message handling for chat sessions."""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from rich.console import Console
from rich.markdown import Markdown
from tqdm.auto import tqdm

from ..models import Message, MessageRole, Source, Character
from ..exceptions import APIError


class MessageHandler:
    """Handles message processing and API communication."""
    
    def __init__(self, source: Source, console: Optional[Console] = None):
        """Initialize with source configuration."""
        if OpenAI is None:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        self.source = source
        self.client = OpenAI(api_key=source.api_key, base_url=source.base_url)
        self.console = console or Console()
        self.messages: List[Message] = []
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
    
    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.add_message(Message.system(content))
    
    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message(Message.user(content))
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message(Message.assistant(content))
    
    def setup_character(self, character: Character) -> None:
        """Setup character system message."""
        system_msg = character.get_system_message()
        if system_msg:
            self.add_system_message(system_msg)
    
    def setup_greeting(self) -> None:
        """Setup greeting system message."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        greeting_prompt = (
            f"系统提示：当前日期和时间为 {now_str}，"
            "请首先向用户进行友好的问候，然后等待用户提问。"
        )
        self.add_system_message(greeting_prompt)
    
    def generate_response(self, character_name: str) -> str:
        """Generate and display response from the model."""
        try:
            # Try streaming first
            return self._generate_streaming_response(character_name)
        except Exception:
            # Fallback to non-streaming
            return self._generate_non_streaming_response(character_name)
    
    def _generate_streaming_response(self, character_name: str) -> str:
        """Generate response using streaming API."""
        stream_resp = self.client.chat.completions.create(
            model=self.source.model,
            messages=[msg.to_dict() for msg in self.messages],
            stream=True,
        )
        
        parts: List[str] = []
        for chunk in tqdm(stream_resp, desc=f"{character_name}思考中..."):
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                parts.append(content)
        
        response_text = "".join(parts).strip()
        self._display_response(character_name, response_text)
        return response_text
    
    def _generate_non_streaming_response(self, character_name: str) -> str:
        """Generate response using non-streaming API."""
        try:
            response = self.client.chat.completions.create(
                model=self.source.model,
                messages=[msg.to_dict() for msg in self.messages],
            )
            response_text = response.choices[0].message.content.strip()
            self._display_response(character_name, response_text)
            return response_text
        except Exception as e:
            raise APIError(f"Failed to generate response: {e}") from e
    
    def _display_response(self, character_name: str, response_text: str) -> None:
        """Display the response in the console."""
        self.console.print(f"[bold green]{character_name}>[/bold green]")
        self.console.print(Markdown(response_text))
    
    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """Get messages formatted for API calls."""
        return [msg.to_dict() for msg in self.messages]
    
    def get_messages_for_logging(self) -> List[Dict[str, Any]]:
        """Get messages formatted for logging."""
        return [msg.to_log_dict() for msg in self.messages]
    
    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages.clear()
    
    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.messages)
