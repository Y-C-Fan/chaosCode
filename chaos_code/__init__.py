"""
ChaosCode - AI 编程助手 CLI 工具

借鉴 OpenCode、Gemini CLI、MS-Agent 精华设计
"""

__version__ = "0.1.0"
__author__ = "ChaosCode Team"

from chaos_code.agent import Agent, CodingAgent, PlannerAgent
from chaos_code.llm import LLM, Message, create_llm
from chaos_code.tools import ToolBase, ToolRegistry, default_tools

__all__ = [
    "__version__",
    "__author__",
    # Agent [OpenCode 参考]
    "Agent",
    "CodingAgent",
    "PlannerAgent",
    # LLM [MS-Agent 参考]
    "LLM",
    "Message",
    "create_llm",
    # Tools [OpenCode 参考]
    "ToolBase",
    "ToolRegistry",
    "default_tools",
]
