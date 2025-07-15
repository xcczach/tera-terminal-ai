"""Main chat session management."""
from __future__ import annotations

import sys
import threading
from typing import Optional, List, Tuple

import click
from rich.console import Console

from ..models import Source, Character, Message
from ..services import SourceService, CharacterService, MemoryService
from ..exceptions import NoActiveSourceError, APIError, CodeExecutionError
from .message_handler import MessageHandler
from .code_executor import CodeExecutor, CodeBlock


class ChatSession:
    """Manages a chat session with an LLM."""
    
    def __init__(
        self,
        source_service: Optional[SourceService] = None,
        character_service: Optional[CharacterService] = None,
        memory_service: Optional[MemoryService] = None,
        console: Optional[Console] = None,
    ):
        """Initialize chat session with services."""
        self.source_service = source_service or SourceService()
        self.character_service = character_service or CharacterService()
        self.memory_service = memory_service or MemoryService()
        self.console = console or Console()
        
        self.message_handler: Optional[MessageHandler] = None
        self.code_executor = CodeExecutor()
        self.current_character: Optional[Character] = None
        self.memory_enabled = False
    
    def start(self) -> None:
        """Start the chat session."""
        try:
            self._initialize_session()
            self._run_greeting()
            self._run_chat_loop()
        except NoActiveSourceError:
            click.echo("尚未配置任何源，请先执行 `tera source add`。")
            sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\n退出聊天。")
        except Exception as e:
            click.echo(f"聊天过程中发生错误: {e}")
            sys.exit(1)
    
    def _initialize_session(self) -> None:
        """Initialize the chat session."""
        # Get active source
        source = self.source_service.get_active_source()
        
        # Get active character
        self.current_character = self.character_service.get_active_character()
        
        # Check memory status
        self.memory_enabled = self.memory_service.is_enabled()
        
        # Initialize message handler
        self.message_handler = MessageHandler(source, self.console)
        
        # Setup character
        self.message_handler.setup_character(self.current_character)
        
        # Handle memory initialization if enabled
        if self.memory_enabled:
            self._initialize_memory()
    
    def _initialize_memory(self) -> None:
        """Initialize memory functionality."""
        try:
            # Import memory functions only when needed
            from ..memory import (
                append_chat_log,
                retrieve_similar,
                add_memory,
                read_chat_log,
                clear_chat_log,
            )
            
            self.append_chat_log = append_chat_log
            self.retrieve_similar = retrieve_similar
            self.add_memory = add_memory
            self.read_chat_log = read_chat_log
            self.clear_chat_log = clear_chat_log
            
            # Process previous session memory in background
            self._process_previous_memory()
            
        except ImportError:
            click.echo("记忆功能依赖未安装，请执行: pip install -e .[memory]")
            self.memory_enabled = False
    
    def _process_previous_memory(self) -> None:
        """Process previous session memory in background."""
        try:
            prev_logs = self.read_chat_log(self.current_character.name)
            self.clear_chat_log(self.current_character.name)
            
            if prev_logs:
                threading.Thread(
                    target=self._extract_memory_from_logs,
                    args=(prev_logs,),
                    daemon=True
                ).start()
        except Exception:
            pass  # Silently handle memory processing errors
    
    def _extract_memory_from_logs(self, logs: List[dict]) -> None:
        """Extract memory from previous chat logs."""
        if not logs or not self.message_handler:
            return
        
        # Create conversation text from logs
        convo_text = "\n".join(
            f"[{log.get('ts', '')}] {log['role']}: {log['content']}"
            for log in logs[-100:]  # Last 100 messages
        )
        
        prompt = (
            "你是助手，任务：从用户和助手对话中提炼值得长期记忆的事实或偏好，"
            "每条不超过50字，用中文输出，每行一条。若无可记忆信息，输出空。\n对话:\n" + convo_text
        )
        
        try:
            # Create temporary message handler for memory extraction
            temp_handler = MessageHandler(self.source_service.get_active_source())
            temp_handler.add_system_message(prompt)
            
            response = temp_handler.generate_response("记忆提取")
            
            # Process extracted memories
            lines = response.strip().splitlines()
            for line in lines:
                line = line.strip("- •\t")
                if line:
                    self.add_memory(self.current_character.name, line)
        except Exception:
            pass  # Silently handle memory extraction errors
    
    def _run_greeting(self) -> None:
        """Generate and display greeting message."""
        if not self.message_handler:
            return
        
        self.message_handler.setup_greeting()
        
        try:
            response = self.message_handler.generate_response(self.current_character.name)
            self.message_handler.add_assistant_message(response)
            
            if self.memory_enabled:
                self.append_chat_log(self.current_character.name, "assistant", response)
            
            # Process any code blocks in greeting
            self._process_code_blocks(response)
            
        except APIError as e:
            click.echo(f"生成问候失败: {e}")
    
    def _run_chat_loop(self) -> None:
        """Run the main chat loop."""
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
            
            self._process_user_input(user_input)
    
    def _process_user_input(self, user_input: str) -> None:
        """Process user input and generate response."""
        if not self.message_handler:
            return
        
        # Add user message
        self.message_handler.add_user_message(user_input)
        
        if self.memory_enabled:
            self.append_chat_log(self.current_character.name, "user", user_input)
            
            # Add relevant memories
            self._add_relevant_memories(user_input)
        
        try:
            # Generate response
            response = self.message_handler.generate_response(self.current_character.name)
            self.message_handler.add_assistant_message(response)
            
            if self.memory_enabled:
                self.append_chat_log(self.current_character.name, "assistant", response)
            
            # Process code blocks
            self._process_code_blocks(response)
            
        except APIError as e:
            click.echo(f"请求出错: {e}")
    
    def _add_relevant_memories(self, user_input: str) -> None:
        """Add relevant memories to the conversation."""
        if not self.memory_enabled or not self.message_handler:
            return
        
        try:
            related = self.retrieve_similar(self.current_character.name, user_input, 5)
            if related:
                memory_text = "以下是与你的个人记忆相关的信息，请参考：\n" + "\n".join(f"- {t}" for t in related)
                self.message_handler.add_system_message(memory_text)
        except Exception:
            pass  # Silently handle memory retrieval errors
    
    def _process_code_blocks(self, response_text: str) -> None:
        """Process code blocks in the response."""
        code_blocks = self.code_executor.extract_code_blocks(response_text)
        if not code_blocks:
            return
        
        executed_blocks: List[Tuple[CodeBlock, str]] = []
        
        for block in code_blocks:
            if click.confirm(f"检测到 {block.language} 代码块，是否执行？", default=False):
                try:
                    output = self.code_executor.execute_code_block(block)
                    self.console.print(f"[yellow]执行输出:[/]\n{output}")
                    executed_blocks.append((block, output))
                except CodeExecutionError as e:
                    self.console.print(f"[red]执行失败: {e}[/]")
        
        if executed_blocks:
            self._send_execution_feedback(executed_blocks)
    
    def _send_execution_feedback(self, executed_blocks: List[Tuple[CodeBlock, str]]) -> None:
        """Send code execution feedback to the model."""
        if not self.message_handler:
            return
        
        feedback = self.code_executor.format_execution_feedback(executed_blocks)
        self.message_handler.add_user_message(feedback)
        
        if self.memory_enabled:
            self.append_chat_log(self.current_character.name, "user", feedback)
        
        try:
            response = self.message_handler.generate_response(self.current_character.name)
            self.message_handler.add_assistant_message(response)
            
            if self.memory_enabled:
                self.append_chat_log(self.current_character.name, "assistant", response)
        except APIError as e:
            click.echo(f"处理执行反馈时出错: {e}")
