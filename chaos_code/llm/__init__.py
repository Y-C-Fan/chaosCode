"""
LLM 集成模块

[MS-Agent 参考: 多 LLM 后端抽象]
"""

from chaos_code.llm.base import LLM, LLMResponse
from chaos_code.llm.message import Message, ToolCall, ToolResult
from chaos_code.llm.providers import create_llm

__all__ = [
    "LLM",
    "LLMResponse",
    "Message",
    "ToolCall",
    "ToolResult",
    "create_llm",
]
