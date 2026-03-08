"""
工具系统

[OpenCode 参考: 工具定义和实现]
[Gemini CLI 参考: 确认机制]
"""

from chaos_code.tools.base import ToolBase, ToolContext, ToolResult
from chaos_code.tools.registry import ToolRegistry
from chaos_code.tools.bash import BashTool
from chaos_code.tools.file_read import ReadTool
from chaos_code.tools.file_write import WriteTool
from chaos_code.tools.file_edit import EditTool
from chaos_code.tools.glob import GlobTool
from chaos_code.tools.grep import GrepTool

__all__ = [
    "ToolBase",
    "ToolContext",
    "ToolResult",
    "ToolRegistry",
    # 核心工具 [OpenCode 参考]
    "BashTool",
    "ReadTool",
    "WriteTool",
    "EditTool",
    "GlobTool",
    "GrepTool",
    "default_tools",
]


def default_tools() -> ToolRegistry:
    """
    创建默认工具注册表 [OpenCode 参考]

    包含所有核心工具：bash, read, write, edit, glob, grep
    """
    registry = ToolRegistry()
    registry.register(BashTool())
    registry.register(ReadTool())
    registry.register(WriteTool())
    registry.register(EditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
    return registry
