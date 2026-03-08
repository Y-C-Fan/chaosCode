"""
MCP 协议模块

[Anthropic MCP 规范参考: https://spec.modelcontextprotocol.io]
[MS-Agent 参考: MCP 客户端实现]

MCP (Model Context Protocol) 是 Anthropic 开源的一个协议，
用于在 AI 应用和外部工具/资源之间建立标准化通信。

## 核心概念

- **Tools**: 可调用的工具函数
- **Resources**: 可访问的数据资源
- **Prompts**: 预定义的提示模板

## 使用示例

```python
from chaos_code.mcp import MCPClient, StdioTransport

# 创建客户端
transport = StdioTransport("python", ["-m", "my_mcp_server"])
client = MCPClient(transport)

# 连接并获取工具
await client.connect()
tools = await client.list_tools()

# 调用工具
result = await client.call_tool("my_tool", {"arg": "value"})

# 断开连接
await client.disconnect()
```

## 配置文件示例

在项目根目录创建 `mcp.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-token"
      }
    }
  }
}
```

然后设置环境变量:
```
CHAOS_CODE_MCP_CONFIG_PATH=mcp.json
```
"""

from chaos_code.mcp.protocol import (
    ContentType,
    EmbeddedResource,
    ImageContent,
    InitializeParams,
    InitializeResult,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    ListResourcesResult,
    ListToolsResult,
    MCPCapabilities,
    MCPClientInfo,
    MCPContent,
    MCPErrorCode,
    MCPImplementation,
    MCPServerInfo,
    MCPTool,
    Resource,
    ResourceContents,
    ResourceLink,
    ResourceTemplate,
    TextContent,
    ToolCallParams,
    ToolInputSchema,
    ToolResult,
)
from chaos_code.mcp.client import (
    HTTPTransport,
    MCPClient,
    MCPError,
    MCPManager,
    MCPServerConfig,
    StdioTransport,
    Transport,
)
from chaos_code.mcp.adapter import (
    MCPToolAdapter,
    create_mcp_tools,
    load_mcp_tools_from_config,
)

__all__ = [
    # 协议类型
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "ContentType",
    "TextContent",
    "ImageContent",
    "ResourceLink",
    "EmbeddedResource",
    "MCPContent",
    # MCP 类型
    "MCPImplementation",
    "MCPClientInfo",
    "MCPCapabilities",
    "MCPServerInfo",
    "InitializeParams",
    "InitializeResult",
    "MCPTool",
    "ToolInputSchema",
    "ToolCallParams",
    "ToolResult",
    "ListToolsResult",
    "Resource",
    "ResourceTemplate",
    "ResourceContents",
    "ListResourcesResult",
    "MCPErrorCode",
    # 传输层
    "Transport",
    "StdioTransport",
    "HTTPTransport",
    # 客户端
    "MCPClient",
    "MCPError",
    "MCPServerConfig",
    "MCPManager",
    # 适配器
    "MCPToolAdapter",
    "create_mcp_tools",
    "load_mcp_tools_from_config",
]
