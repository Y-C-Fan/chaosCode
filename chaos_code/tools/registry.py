"""
工具注册表

[OpenCode 参考: 工具管理和查找]
"""

from typing import Dict, List, Optional

from chaos_code.llm.base import ToolSchema
from chaos_code.tools.base import ToolBase


class ToolRegistry:
    """
    工具注册表 [OpenCode 参考]

    管理所有可用工具的注册、查找和 Schema 生成

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register(BashTool())
        >>> tool = registry.get("bash")
        >>> schemas = registry.get_schemas()
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
        """
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            bool: 是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[ToolBase]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            ToolBase | None: 工具实例，不存在则返回 None
        """
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def get_schemas(self) -> List[ToolSchema]:
        """
        获取所有工具的 Schema [OpenCode 参考]

        用于传递给 LLM 的 tools 参数
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def get_all(self) -> Dict[str, ToolBase]:
        """获取所有工具"""
        return self._tools.copy()

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __repr__(self) -> str:
        tools = ", ".join(self._tools.keys())
        return f"<ToolRegistry tools=[{tools}]>"
