"""
MCP 工具适配器

将 MCP 工具适配为 ChaosCode 工具系统
"""

from typing import Any, Dict, Optional

from chaos_code.mcp.client import MCPManager
from chaos_code.mcp.protocol import MCPTool, TextContent, ImageContent
from chaos_code.tools.base import ToolBase, ToolContext, ToolResult


class MCPToolAdapter(ToolBase):
    """
    MCP 工具适配器

    将 MCP 工具包装为 ChaosCode 的 ToolBase，使其可以在 Agent 中使用
    """

    def __init__(
        self,
        full_name: str,
        mcp_tool: MCPTool,
        manager: MCPManager,
    ):
        """
        初始化适配器

        Args:
            full_name: 完整工具名（服务器.工具名）
            mcp_tool: MCP 工具定义
            manager: MCP 管理器实例
        """
        self.full_name = full_name
        self.mcp_tool = mcp_tool
        self.manager = manager

        # 设置工具属性
        self.name = full_name
        self.description = mcp_tool.description
        self.parameters_schema = mcp_tool.inputSchema.model_dump()

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """
        执行工具调用

        Args:
            params: 工具参数
            context: 执行上下文

        Returns:
            ToolResult: 执行结果
        """
        try:
            # 调用 MCP 工具
            mcp_result = await self.manager.call_tool(self.full_name, params)

            # 处理结果内容
            output_parts = []
            for content in mcp_result.content:
                if isinstance(content, TextContent):
                    output_parts.append(content.text)
                elif isinstance(content, ImageContent):
                    output_parts.append(f"[图片: {content.mimeType}, {len(content.data)} 字节]")
                else:
                    output_parts.append(str(content))

            output = "\n".join(output_parts)

            return ToolResult(
                success=not mcp_result.isError,
                output=output,
                error=None if not mcp_result.isError else output,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"MCP 工具调用失败: {e}",
            )

    def get_description(self, params: Dict[str, Any]) -> str:
        """获取工具调用描述"""
        return f"调用 MCP 工具: {self.full_name}"


def create_mcp_tools(manager: MCPManager) -> Dict[str, ToolBase]:
    """
    从 MCP 管理器创建工具实例

    Args:
        manager: MCP 管理器

    Returns:
        Dict[str, ToolBase]: 工具名到工具实例的映射
    """
    tools = {}
    for full_name, mcp_tool in manager.tools.items():
        tools[full_name] = MCPToolAdapter(full_name, mcp_tool, manager)
    return tools


async def load_mcp_tools_from_config(
    configs: list,
) -> Dict[str, ToolBase]:
    """
    从配置加载 MCP 工具

    Args:
        configs: MCP 服务器配置列表

    Returns:
        Dict[str, ToolBase]: 加载的工具
    """
    from chaos_code.mcp.client import MCPServerConfig

    manager = MCPManager()

    for config_dict in configs:
        config = MCPServerConfig(**config_dict)
        try:
            await manager.connect_server(config)
        except Exception as e:
            # 记录错误但继续加载其他服务器
            print(f"警告: 连接 MCP 服务器 {config.name} 失败: {e}")

    return create_mcp_tools(manager)
