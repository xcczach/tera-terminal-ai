"""Code execution functionality for chat."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from typing import List, Tuple

from ..config import SUPPORTED_LANGUAGES
from ..exceptions import CodeExecutionError


class CodeBlock:
    """Represents a code block found in text."""
    
    def __init__(self, language: str, code: str):
        self.language = language
        self.code = code
        self.output: str = ""
    
    def __str__(self) -> str:
        return f"```{self.language}\n{self.code}\n```"


class CodeExecutor:
    """Handles code execution from chat messages."""
    
    CODE_BLOCK_PATTERN = re.compile(r"```(\w*)\n([\s\S]*?)```", re.MULTILINE)
    
    def extract_code_blocks(self, text: str) -> List[CodeBlock]:
        """Extract code blocks from text."""
        blocks = []
        for lang_hint, code in self.CODE_BLOCK_PATTERN.findall(text):
            language = self._detect_language(lang_hint, code)
            if language in SUPPORTED_LANGUAGES:
                blocks.append(CodeBlock(language, code))
        return blocks
    
    def _detect_language(self, lang_hint: str, code: str) -> str:
        """Detect the programming language of a code block."""
        hint = lang_hint.lower()
        
        # Explicit language hints
        if hint in {"python", "py"}:
            return "python"
        if hint in {"bash", "sh", "shell"}:
            return "shell"
        
        # Heuristic detection
        if code.lstrip().startswith("import ") or "def " in code:
            return "python"
        
        return "shell"
    
    def execute_code_block(self, block: CodeBlock) -> str:
        """Execute a single code block and return output."""
        try:
            if block.language == "python":
                return self._execute_python(block.code)
            elif block.language in {"bash", "sh", "shell"}:
                return self._execute_shell(block.code)
            else:
                raise CodeExecutionError(f"Unsupported language: {block.language}")
        except Exception as e:
            raise CodeExecutionError(f"Failed to execute {block.language} code: {e}") from e
    
    def _execute_python(self, code: str) -> str:
        """Execute Python code and return output."""
        # Ensure UTF-8 encoding declaration
        if not code.lstrip().startswith("#"):
            code = "# -*- coding: utf-8 -*-\n" + code
        
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py", encoding="utf-8") as fp:
            fp.write(code)
            tmp_path = fp.name
        
        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                shell=False,
                timeout=30  # 30 second timeout
            )
            return self._format_output(result)
        finally:
            # Clean up temporary file
            try:
                import os
                os.unlink(tmp_path)
            except OSError:
                pass
    
    def _execute_shell(self, code: str) -> str:
        """Execute shell code and return output."""
        result = subprocess.run(
            code,
            capture_output=True,
            text=True,
            shell=True,
            timeout=30  # 30 second timeout
        )
        return self._format_output(result)
    
    def _format_output(self, result: subprocess.CompletedProcess) -> str:
        """Format subprocess output."""
        output_parts = []
        
        if result.stdout:
            output_parts.append(result.stdout.strip())
        
        if result.stderr:
            output_parts.append(f"STDERR:\n{result.stderr.strip()}")
        
        if not output_parts:
            return "(无输出)"
        
        return "\n".join(output_parts)
    
    def format_execution_feedback(self, executed_blocks: List[Tuple[CodeBlock, str]]) -> str:
        """Format execution results for feedback to the model."""
        if not executed_blocks:
            return ""
        
        parts = ["(以下是我在本地执行你上一条消息中所有代码块后的输出)"]
        
        for block, output in executed_blocks:
            parts.append(
                f"```{block.language}\n{block.code}\n```\n"
                f"执行结果:\n```text\n{output}\n```"
            )
        
        return "\n\n".join(parts)
