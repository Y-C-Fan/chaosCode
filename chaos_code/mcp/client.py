"""
MCP 客户端实现

[Anthropic MCP 规范参考: https://spec.modelcontextprotocol.io]

支持通过 stdio 和 HTTP 两种传输方式连接 MCP 服务器
"""

import asyncio
import json
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from chaos_code.mcp.protocol import (
    InitializeParams,
    InitializeResult,
    JSONRPCRequest,
    JSONRPCResponse,
    ListToolsResult,
    MCPClientInfo,
    MCPCapabilities,
    MCPErrorCode,
    MCPTool,
    ReadResourceResult,
    ToolCallParams,
    ToolResult,
)


class MCPError(Exception):
    """MCP 错误"""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error [{code}]: {message}")


class Transport(ABC):
    """
    MCP 传输层抽象基类

    定义了 MCP 客户端与服务端之间的通信接口
    """

    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    async def send(self, request: JSONRPCRequest) -> None:
        """发送请求"""
        pass

    @abstractmethod
    async def receive(self) -> JSONRPCResponse:
        """接收响应"""
        pass

    @abstractmethod
    async def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """发送通知（无需响应）"""
        pass


class StdioTransport(Transport):
    """
    stdio 传输层

    通过标准输入/输出与 MCP 服务器进程通信

    这是最常用的 MCP 传输方式，服务器作为子进程启动
    """

    def __init__(
        self,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        cwd: Optional[str] = None,
    ):
        """
        初始化 stdio 传输

        Args:
            command: 服务器命令
            args: 命令参数
            env: 环境变量
            cwd: 工作目录
        """
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.cwd = cwd

        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def connect(self) -> None:
        """启动子进程并建立连接"""
        # 准备环境变量
        process_env = os.environ.copy()
        process_env.update(self.env)

        # 启动子进程
        self._process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=process_env,
            cwd=self.cwd,
        )

        self._reader = self._process.stdout
        self._writer = self._process.stdin

    async def disconnect(self) -> None:
        """终止子进程"""
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            self._process = None
            self._reader = None
            self._writer = None

    async def send(self, request: JSONRPCRequest) -> None:
        """发送 JSON-RPC 请求"""
        if not self._writer:
            raise MCPError(MCPErrorCode.SERVER_NOT_INITIALIZED, "未连接到服务器")

        # 序列化并发送
        data = request.model_dump_json() + "\n"
        self._writer.write(data.encode("utf-8"))
        await self._writer.drain()

    async def receive(self) -> JSONRPCResponse:
        """接收 JSON-RPC 响应"""
        if not self._reader:
            raise MCPError(MCPErrorCode.SERVER_NOT_INITIALIZED, "未连接到服务器")

        # 读取一行 JSON
        line = await self._reader.readline()
        if not line:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "连接已关闭")

        try:
            data = json.loads(line.decode("utf-8"))
            return JSONRPCResponse(**data)
        except json.JSONDecodeError as e:
            raise MCPError(MCPErrorCode.PARSE_ERROR, f"JSON 解析错误: {e}")

    async def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """发送通知"""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            id=None,  # 通知没有 ID
            method=method,
            params=params,
        )
        await self.send(request)


class HTTPTransport(Transport):
    """
    HTTP 传输层

    通过 HTTP SSE (Server-Sent Events) 与 MCP 服务器通信

    注意：HTTP 传输方式在 MCP 规范中仍处于实验阶段
    """

    def __init__(self, url: str, headers: Dict[str, str] = None):
        """
        初始化 HTTP 传输

        Args:
            url: 服务器 URL
            headers: HTTP 头
        """
        self.url = url
        self.headers = headers or {}

        self._request_id = 0
        self._pending: Dict[Union[int, str], asyncio.Future] = {}

    async def connect(self) -> None:
        """建立 SSE 连接"""
        # 使用 httpx 或 aiohttp 建立 SSE 连接
        # 这里简化实现，实际需要更复杂的 SSE 处理
        import httpx

        self._client = httpx.AsyncClient(base_url=self.url, headers=self.headers)

    async def disconnect(self) -> None:
        """关闭连接"""
        if hasattr(self, "_client"):
            await self._client.aclose()

    async def send(self, request: JSONRPCRequest) -> None:
        """发送 HTTP 请求"""
        self._request_id += 1
        if request.id is None:
            request.id = self._request_id

        response = await self._client.post(
            "/message",
            json=request.model_dump(),
        )
        # HTTP 传输的响应处理不同，这里简化
        response.raise_for_status()

    async def receive(self) -> JSONRPCResponse:
        """接收响应（HTTP 传输通常通过 SSE）"""
        # SSE 处理逻辑
        raise NotImplementedError("HTTP transport requires SSE implementation")

    async def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """发送通知"""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            id=None,
            method=method,
            params=params,
        )
        await self.send(request)


class MCPClient:
    """
    MCP 客户端

    负责与 MCP 服务器通信，提供工具调用和资源访问功能

    使用示例:
        client = MCPClient(StdioTransport("python", ["-m", "my_mcp_server"]))
        await client.connect()
        tools = await client.list_tools()
        result = await client.call_tool("my_tool", {"arg": "value"})
        await client.disconnect()
    """

    def __init__(
        self,
        transport: Transport,
        client_info: Optional[MCPClientInfo] = None,
        capabilities: Optional[MCPCapabilities] = None,
    ):
        """
        初始化 MCP 客户端

        Args:
            transport: 传输层实例
            client_info: 客户端信息
            capabilities: 客户端能力
        """
        self.transport = transport
        self.client_info = client_info or MCPClientInfo()
        self.capabilities = capabilities or MCPCapabilities()

        self._request_id = 0
        self._server_info: Optional[InitializeResult] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @property
    def server_info(self) -> Optional[InitializeResult]:
        """服务器信息"""
        return self._server_info

    async def connect(self) -> InitializeResult:
        """
        连接到 MCP 服务器并完成初始化握手

        Returns:
            InitializeResult: 服务器信息
        """
        # 建立传输层连接
        await self.transport.connect()

        # 发送初始化请求
        init_params = InitializeParams(
            protocolVersion="2024-11-05",
            capabilities=self.capabilities,
            clientInfo=self.client_info,
        )

        response = await self._send_request("initialize", init_params.model_dump())

        if response.error:
            await self.transport.disconnect()
            raise MCPError(response.error.code, response.error.message, response.error.data)

        self._server_info = InitializeResult(**response.result)
        self._connected = True

        # 发送 initialized 通知
        await self.transport.send_notification("notifications/initialized", {})

        return self._server_info

    async def disconnect(self) -> None:
        """断开连接"""
        if self._connected:
            await self.transport.disconnect()
            self._connected = False
            self._server_info = None

    async def list_tools(self) -> List[MCPTool]:
        """
        获取服务器提供的工具列表

        Returns:
            List[MCPTool]: 工具列表
        """
        if not self._connected:
            raise MCPError(MCPErrorCode.SERVER_NOT_INITIALIZED, "未连接到服务器")

        response = await self._send_request("tools/list", {})

        if response.error:
            raise MCPError(response.error.code, response.error.message)

        result = ListToolsResult(**response.result)
        return result.tools

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> ToolResult:
        """
        调用工具

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            ToolResult: 工具执行结果
        """
        if not self._connected:
            raise MCPError(MCPErrorCode.SERVER_NOT_INITIALIZED, "未连接到服务器")

        params = ToolCallParams(name=name, arguments=arguments)

        response = await self._send_request("tools/call", params.model_dump())

        if response.error:
            raise MCPError(response.error.code, response.error.message, response.error.data)

        return ToolResult(**response.result)

    async def list_resources(self) -> List:
        """
        获取服务器提供的资源列表

        Returns:
            List[Resource]: 资源列表
        """
        if not self._connected:
            raise MCPError(MCPErrorCode.SERVER_NOT_INITIALIZED, "未连接到服务器")

        from chaos_code.mcp.protocol import ListResourcesResult

        response = await self._send_request("resources/list", {})

        if response.error:
            raise MCPError(response.error.code, response.error.message)

        result = ListResourcesResult(**response.result)
        return result.resources

    async def read_resource(self, uri: str) -> ReadResourceResult:
        """
        读取资源

        Args:
            uri: 资源 URI

        Returns:
            ReadResourceResult: 资源内容
        """
        if not self._connected:
            raise MCPError(MCPErrorCode.SERVER_NOT_INITIALIZED, "未连接到服务器")

        response = await self._send_request("resources/read", {"uri": uri})

        if response.error:
            raise MCPError(response.error.code, response.error.message)

        return ReadResourceResult(**response.result)

    async def _send_request(
        self,
        method: str,
        params: Dict[str, Any],
    ) -> JSONRPCResponse:
        """
        发送 JSON-RPC 请求

        Args:
            method: 方法名
            params: 参数

        Returns:
            JSONRPCResponse: 响应
        """
        self._request_id += 1
        request = JSONRPCRequest(
            jsonrpc="2.0",
            id=self._request_id,
            method=method,
            params=params,
        )

        await self.transport.send(request)
        return await self.transport.receive()

    async def __aenter__(self) -> "MCPClient":
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.disconnect()


# ============== MCP 服务器配置 ==============

class MCPServerConfig(BaseModel):
    """MCP 服务器配置"""

    name: str = Field(..., description="服务器名称")
    command: str = Field(..., description="启动命令")
    args: List[str] = Field(default_factory=list, description="命令参数")
    env: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    cwd: Optional[str] = Field(default=None, description="工作目录")
    disabled: bool = Field(default=False, description="是否禁用")

    def create_transport(self) -> StdioTransport:
        """创建传输层实例"""
        return StdioTransport(
            command=self.command,
            args=self.args,
            env=self.env,
            cwd=self.cwd,
        )


class MCPManager:
    """
    MCP 管理器

    管理多个 MCP 服务器连接，提供统一的工具访问接口
    """

    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._tools: Dict[str, MCPTool] = {}
        self._tool_to_server: Dict[str, str] = {}

    @property
    def clients(self) -> Dict[str, MCPClient]:
        """已连接的客户端"""
        return self._clients

    @property
    def tools(self) -> Dict[str, MCPTool]:
        """可用的工具"""
        return self._tools

    async def connect_server(self, config: MCPServerConfig) -> None:
        """
        连接到 MCP 服务器

        Args:
            config: 服务器配置
        """
        if config.disabled:
            return

        transport = config.create_transport()
        client = MCPClient(transport)

        try:
            await client.connect()
            self._clients[config.name] = client

            # 获取工具列表
            tools = await client.list_tools()
            for tool in tools:
                # 工具名加上服务器前缀避免冲突
                full_name = f"{config.name}.{tool.name}"
                self._tools[full_name] = tool
                self._tool_to_server[full_name] = config.name

        except Exception as e:
            await client.disconnect()
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, f"连接服务器失败: {e}")

    async def disconnect_all(self) -> None:
        """断开所有连接"""
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()
        self._tools.clear()
        self._tool_to_server.clear()

    async def call_tool(
        self,
        full_name: str,
        arguments: Dict[str, Any],
    ) -> ToolResult:
        """
        调用工具

        Args:
            full_name: 完整工具名（服务器.工具名）
            arguments: 工具参数

        Returns:
            ToolResult: 工具执行结果
        """
        if full_name not in self._tool_to_server:
            raise MCPError(MCPErrorCode.METHOD_NOT_FOUND, f"未知工具: {full_name}")

        server_name = self._tool_to_server[full_name]
        client = self._clients.get(server_name)

        if not client:
            raise MCPError(MCPErrorCode.SERVER_NOT_INITIALIZED, f"服务器未连接: {server_name}")

        # 去掉服务器前缀
        tool_name = full_name.split(".", 1)[1]
        return await client.call_tool(tool_name, arguments)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的 Schema

        Returns:
            List[Dict]: 工具 Schema 列表
        """
        schemas = []
        for full_name, tool in self._tools.items():
            schemas.append({
                "name": full_name,
                "description": tool.description,
                "parameters": tool.inputSchema.model_dump(),
            })
        return schemas
