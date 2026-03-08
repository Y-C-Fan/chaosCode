"""
MCP 模块测试

[Anthropic MCP 规范参考]
"""

import pytest

from chaos_code.mcp import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    MCPClient,
    MCPError,
    MCPServerConfig,
    MCPTool,
    StdioTransport,
    ToolInputSchema,
    ToolResult,
    TextContent,
    MCPManager,
    MCPToolAdapter,
)


class TestProtocol:
    """测试 MCP 协议类型"""

    def test_jsonrpc_request(self):
        """测试 JSON-RPC 请求"""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            id=1,
            method="initialize",
            params={"protocolVersion": "2024-11-05"},
        )

        assert request.jsonrpc == "2.0"
        assert request.id == 1
        assert request.method == "initialize"
        assert request.params["protocolVersion"] == "2024-11-05"

    def test_jsonrpc_response(self):
        """测试 JSON-RPC 响应"""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            id=1,
            result={"status": "ok"},
        )

        assert response.jsonrpc == "2.0"
        assert response.id == 1
        assert response.result["status"] == "ok"
        assert response.error is None

    def test_jsonrpc_error_response(self):
        """测试 JSON-RPC 错误响应"""
        response = JSONRPCResponse(
            jsonrpc="2.0",
            id=1,
            error=JSONRPCError(
                code=-32600,
                message="Invalid Request",
            ),
        )

        assert response.error is not None
        assert response.error.code == -32600
        assert response.error.message == "Invalid Request"

    def test_mcp_tool(self):
        """测试 MCP 工具定义"""
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            inputSchema=ToolInputSchema(
                type="object",
                properties={
                    "query": {
                        "type": "string",
                        "description": "查询字符串",
                    }
                },
                required=["query"],
            ),
        )

        assert tool.name == "test_tool"
        assert tool.description == "测试工具"
        assert "query" in tool.inputSchema.properties

    def test_tool_result(self):
        """测试工具执行结果"""
        result = ToolResult(
            content=[
                TextContent(text="执行成功"),
            ],
            isError=False,
        )

        assert not result.isError
        assert len(result.content) == 1
        assert result.content[0].text == "执行成功"


class TestTransport:
    """测试传输层"""

    def test_stdio_transport_creation(self):
        """测试 stdio 传输层创建"""
        transport = StdioTransport(
            command="python",
            args=["-m", "test_server"],
            env={"TEST": "1"},
            cwd="/tmp",
        )

        assert transport.command == "python"
        assert transport.args == ["-m", "test_server"]
        assert transport.env["TEST"] == "1"
        assert transport.cwd == "/tmp"

    def test_stdio_transport_from_config(self):
        """测试从配置创建传输层"""
        config = MCPServerConfig(
            name="test",
            command="node",
            args=["server.js"],
            env={"NODE_ENV": "development"},
        )

        transport = config.create_transport()

        assert transport.command == "node"
        assert transport.args == ["server.js"]


class TestMCPManager:
    """测试 MCP 管理器"""

    def test_manager_creation(self):
        """测试管理器创建"""
        manager = MCPManager()

        assert len(manager.clients) == 0
        assert len(manager.tools) == 0

    def test_manager_tool_schemas(self):
        """测试获取工具 Schema"""
        manager = MCPManager()

        # 手动添加一个工具
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
        )
        manager._tools["server.test_tool"] = tool
        manager._tool_to_server["server.test_tool"] = "server"

        schemas = manager.get_tool_schemas()

        assert len(schemas) == 1
        assert schemas[0]["name"] == "server.test_tool"


class TestMCPToolAdapter:
    """测试 MCP 工具适配器"""

    def test_adapter_creation(self):
        """测试适配器创建"""
        tool = MCPTool(
            name="echo",
            description="回显工具",
            inputSchema=ToolInputSchema(
                type="object",
                properties={"message": {"type": "string"}},
            ),
        )

        manager = MCPManager()
        adapter = MCPToolAdapter("test.echo", tool, manager)

        assert adapter.name == "test.echo"
        assert adapter.description == "回显工具"
        assert "message" in adapter.parameters_schema["properties"]


class TestMCPError:
    """测试 MCP 错误"""

    def test_error_creation(self):
        """测试错误创建"""
        error = MCPError(
            code=-32601,
            message="Method not found",
            data={"method": "unknown"},
        )

        assert error.code == -32601
        assert error.message == "Method not found"
        assert error.data["method"] == "unknown"

    def test_error_message(self):
        """测试错误消息"""
        error = MCPError(code=-32000, message="Server error")

        assert "[-32000]" in str(error)
        assert "Server error" in str(error)
