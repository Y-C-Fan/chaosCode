"""
MCP 协议数据模型

[Anthropic MCP 规范参考: https://spec.modelcontextprotocol.io]

MCP 基于 JSON-RPC 2.0 协议，定义了以下核心概念：
- Tools: 可调用的工具
- Resources: 可访问的资源
- Prompts: 预定义的提示模板
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ============== JSON-RPC 基础类型 ==============

class JSONRPCVersion(str, Enum):
    """JSON-RPC 版本"""
    V2 = "2.0"


class JSONRPCRequest(BaseModel):
    """JSON-RPC 请求"""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    id: Optional[Union[int, str]] = Field(default=None, description="请求 ID")
    method: str = Field(..., description="方法名")
    params: Optional[Dict[str, Any]] = Field(default=None, description="参数")


class JSONRPCError(BaseModel):
    """JSON-RPC 错误"""

    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")
    data: Optional[Any] = Field(default=None, description="额外错误数据")


class JSONRPCResponse(BaseModel):
    """JSON-RPC 响应"""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC 版本")
    id: Optional[Union[int, str]] = Field(default=None, description="请求 ID")
    result: Optional[Any] = Field(default=None, description="结果")
    error: Optional[JSONRPCError] = Field(default=None, description="错误")


# ============== MCP 协议类型 ==============

class MCPImplementation(BaseModel):
    """实现信息"""

    name: str = Field(..., description="实现名称")
    version: str = Field(..., description="版本号")


class MCPClientInfo(BaseModel):
    """客户端信息"""

    name: str = Field(default="chaos-code", description="客户端名称")
    version: str = Field(default="0.1.0", description="客户端版本")


class MCPCapabilities(BaseModel):
    """MCP 能力"""

    tools: Optional[Dict[str, Any]] = Field(default=None, description="工具能力")
    resources: Optional[Dict[str, Any]] = Field(default=None, description="资源能力")
    prompts: Optional[Dict[str, Any]] = Field(default=None, description="提示能力")


class MCPServerInfo(BaseModel):
    """服务器信息"""

    name: str = Field(..., description="服务器名称")
    version: str = Field(..., description="服务器版本")
    protocolVersion: str = Field(default="2024-11-05", description="协议版本")


class InitializeParams(BaseModel):
    """初始化参数"""

    protocolVersion: str = Field(default="2024-11-05", description="协议版本")
    capabilities: MCPCapabilities = Field(default_factory=MCPCapabilities)
    clientInfo: MCPClientInfo = Field(default_factory=MCPClientInfo)


class InitializeResult(BaseModel):
    """初始化结果"""

    protocolVersion: str = Field(..., description="协议版本")
    capabilities: MCPCapabilities = Field(default_factory=MCPCapabilities)
    serverInfo: MCPServerInfo = Field(..., description="服务器信息")


# ============== MCP 工具类型 ==============

class ToolInputSchema(BaseModel):
    """工具输入 Schema"""

    type: str = Field(default="object", description="类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="属性定义")
    required: List[str] = Field(default_factory=list, description="必需属性")


class MCPTool(BaseModel):
    """MCP 工具定义"""

    name: str = Field(..., description="工具名称")
    description: str = Field(default="", description="工具描述")
    inputSchema: ToolInputSchema = Field(
        default_factory=ToolInputSchema,
        description="输入参数 Schema",
    )


class ToolCallParams(BaseModel):
    """工具调用参数"""

    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="参数")


# ============== MCP 内容类型 ==============

class ContentType(str, Enum):
    """内容类型"""

    TEXT = "text"
    IMAGE = "image"
    RESOURCE = "resource"


class TextContent(BaseModel):
    """文本内容"""

    type: str = Field(default="text", description="类型")
    text: str = Field(..., description="文本内容")


class ImageContent(BaseModel):
    """图片内容"""

    type: str = Field(default="image", description="类型")
    data: str = Field(..., description="Base64 编码的图片数据")
    mimeType: str = Field(default="image/png", description="MIME 类型")


class ResourceLink(BaseModel):
    """资源链接"""

    type: str = Field(default="resource", description="类型")
    uri: str = Field(..., description="资源 URI")
    mimeType: Optional[str] = Field(default=None, description="MIME 类型")


class EmbeddedResource(BaseModel):
    """嵌入资源"""

    type: str = Field(default="resource", description="类型")
    resource: Dict[str, Any] = Field(..., description="资源内容")


# 内容联合类型
MCPContent = Union[TextContent, ImageContent, EmbeddedResource]


class ToolResult(BaseModel):
    """工具执行结果"""

    content: List[MCPContent] = Field(default_factory=list, description="内容列表")
    isError: bool = Field(default=False, description="是否错误")


class ListToolsResult(BaseModel):
    """工具列表结果"""

    tools: List[MCPTool] = Field(default_factory=list, description="工具列表")
    nextCursor: Optional[str] = Field(default=None, description="下一页游标")


# ============== MCP 资源类型 ==============

class ResourceTemplate(BaseModel):
    """资源模板"""

    uriTemplate: str = Field(..., description="URI 模板")
    name: str = Field(..., description="名称")
    description: str = Field(default="", description="描述")
    mimeType: Optional[str] = Field(default=None, description="MIME 类型")


class Resource(BaseModel):
    """资源定义"""

    uri: str = Field(..., description="资源 URI")
    name: str = Field(..., description="名称")
    description: str = Field(default="", description="描述")
    mimeType: Optional[str] = Field(default=None, description="MIME 类型")


class ResourceContents(BaseModel):
    """资源内容"""

    uri: str = Field(..., description="资源 URI")
    mimeType: Optional[str] = Field(default=None, description="MIME 类型")
    text: Optional[str] = Field(default=None, description="文本内容")
    blob: Optional[str] = Field(default=None, description="Base64 编码的二进制内容")


class ListResourcesResult(BaseModel):
    """资源列表结果"""

    resources: List[Resource] = Field(default_factory=list, description="资源列表")
    nextCursor: Optional[str] = Field(default=None, description="下一页游标")


class ReadResourceParams(BaseModel):
    """读取资源参数"""

    uri: str = Field(..., description="资源 URI")


class ReadResourceResult(BaseModel):
    """读取资源结果"""

    contents: List[ResourceContents] = Field(default_factory=list, description="内容列表")


# ============== MCP 错误码 ==============

class MCPErrorCode(int, Enum):
    """MCP 错误码"""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # MCP 特定错误码
    SERVER_NOT_INITIALIZED = -32002
    UNKNOWN_ERROR = -32001
