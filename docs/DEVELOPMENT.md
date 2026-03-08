# ChaosCode 开发文档

## 项目概述

**ChaosCode** 是一个基于 Python 的 AI 编程助手 CLI 工具，借鉴 OpenCode、Gemini CLI、MS-Agent 三个优秀开源项目的精华设计。

### 项目定位

- **语言**: Python 3.8+
- **界面**: CLI + TUI (Terminal User Interface)
- **架构**: 模块化、可扩展
- **核心功能**: 代码编辑、文件操作、终端执行、LLM 集成、MCP 协议支持

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  chat   │  │  repl   │  │   tui   │  │  tools  │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       Agent Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CodingAgent  │  │ PlannerAgent │  │  Permission  │      │
│  │  (build模式) │  │  (plan模式)  │  │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        Tool Layer                            │
│  ┌────┐ ┌─────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│  │Bash│ │Read │ │Write │ │Edit  │ │Glob  │ │Grep  │       │
│  └────┘ └─────┘ └──────┘ └──────┘ └──────┘ └──────┘       │
│  ┌─────────────────────────────────────────────────┐       │
│  │              MCP Tool Adapter                    │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       LLM Layer                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │              LiteLLM Provider                    │       │
│  │   OpenAI | Anthropic | DeepSeek | 通义千问      │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure                            │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ Config │ │Session │ │Memory  │ │ MCP    │ │ Utils  │    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 模块说明

| 模块 | 路径 | 功能 | 参考来源 |
|------|------|------|----------|
| CLI | `cli/` | 命令行入口 | 原创选型 typer + rich |
| Agent | `agent/` | Agent 核心逻辑 | OpenCode + MS-Agent |
| LLM | `llm/` | LLM 集成 | MS-Agent (litellm) |
| Tools | `tools/` | 工具系统 | OpenCode |
| Permission | `permission/` | 权限系统 | OpenCode + Gemini CLI |
| MCP | `mcp/` | MCP 协议 | Anthropic MCP 规范 |
| TUI | `tui/` | 终端界面 | 原创选型 textual |
| Session | `session/` | 会话管理 | MS-Agent |
| Config | `config/` | 配置系统 | 原创选型 pydantic |

---

## 核心模块详解

### 1. Agent 模块

Agent 是系统的核心，负责协调 LLM 和工具执行。

#### 1.1 Agent 基类

```python
class Agent(ABC):
    def __init__(
        self,
        llm: LLM,
        tools: ToolRegistry,
        max_turns: int = 20,
        mode: AgentMode = AgentMode.BUILD,
        permission_manager: PermissionManager = None,
    ):
        self.llm = llm
        self.tools = tools
        self.permission_manager = permission_manager

    async def run(self, user_input: str) -> AsyncGenerator[Message, None]:
        """主循环：LLM调用 -> 工具执行 -> 结果返回"""
        self.messages.append(Message.user(user_input))

        for _ in range(self.max_turns):
            response = await self._call_llm()
            yield response.message

            if response.message.tool_calls:
                for tool_call in response.message.tool_calls:
                    result = await self._execute_tool(tool_call)
                    yield result
            else:
                break
```

#### 1.2 Agent 模式

| 模式 | 说明 | 权限 |
|------|------|------|
| BUILD | 全功能模式 | 允许所有操作（需确认危险操作） |
| PLAN | 只读规划模式 | 仅允许读取，禁止写入和执行 |

### 2. 工具系统

#### 2.1 工具基类

```python
class ToolBase(ABC):
    name: str
    description: str
    parameters_schema: Dict[str, Any]

    @abstractmethod
    async def execute(self, params: Dict, context: ToolContext) -> ToolResult:
        pass

    def should_confirm(self, params: Dict) -> bool:
        """是否需要用户确认"""
        return False
```

#### 2.2 内置工具

| 工具 | 功能 | 是否需要确认 |
|------|------|-------------|
| bash | 终端命令执行 | 危险命令需要 |
| read | 文件读取 | 否 |
| write | 文件写入 | 覆盖已有文件需要 |
| edit | 文件编辑 | 是 |
| glob | 文件模式匹配 | 否 |
| grep | 内容搜索 | 否 |

### 3. 权限系统

#### 3.1 权限级别

```python
class PermissionLevel(str, Enum):
    ALLOW = "allow"    # 允许执行
    DENY = "deny"      # 禁止执行
    CONFIRM = "confirm" # 需要确认
```

#### 3.2 权限规则

```python
class PermissionRule(BaseModel):
    name: str                    # 规则名称
    level: PermissionLevel       # 权限级别
    tools: List[str]             # 匹配的工具（支持通配符）
    params: Dict[str, Any]       # 参数匹配规则（支持正则）
    priority: int                # 优先级
```

#### 3.3 默认规则

- 读取操作（read, glob, grep）→ ALLOW
- 写入操作（write, edit）→ CONFIRM
- 危险命令（rm -rf, dd 等）→ CONFIRM

### 4. MCP 协议

#### 4.1 协议架构

MCP 基于 JSON-RPC 2.0，支持：

- **Tools**: 可调用的工具函数
- **Resources**: 可访问的数据资源
- **Prompts**: 预定义的提示模板

#### 4.2 客户端实现

```python
class MCPClient:
    async def connect(self) -> InitializeResult:
        """连接并初始化"""

    async def list_tools(self) -> List[MCPTool]:
        """获取工具列表"""

    async def call_tool(self, name: str, arguments: Dict) -> ToolResult:
        """调用工具"""
```

#### 4.3 传输方式

| 传输方式 | 说明 | 适用场景 |
|----------|------|----------|
| StdioTransport | 子进程标准输入输出 | 本地 MCP 服务器 |
| HTTPTransport | HTTP/SSE | 远程 MCP 服务器 |

### 5. TUI 界面

#### 5.1 组件结构

```
┌─────────────────────────────────────┐
│ Header (时钟、标题)                  │
├─────────────────────────────────────┤
│                                     │
│ MessageList (消息列表)              │
│                                     │
│                                     │
├─────────────────────────────────────┤
│ InputArea (输入框 + 发送按钮)       │
├─────────────────────────────────────┤
│ StatusBar (模型、模式、状态)         │
├─────────────────────────────────────┤
│ Footer (快捷键提示)                  │
└─────────────────────────────────────┘
```

#### 5.2 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+Q | 退出 |
| Ctrl+L | 清屏 |
| Ctrl+N | 新会话 |
| F1 | 帮助 |

### 6. 会话管理

#### 6.1 会话模型

```python
class Session(BaseModel):
    id: str
    name: str
    model: str
    mode: str
    messages: List[SessionMessage]
    created_at: str
    updated_at: str
```

#### 6.2 持久化

- 存储位置: `~/.chaos-code/sessions/`
- 格式: JSON
- 支持导入导出

### 7. 记忆系统

#### 7.1 三级记忆体系

| 类型 | 作用域 | 存储位置 |
|------|--------|----------|
| 短期记忆 | 会话内 | 内存 |
| 长期记忆 | 跨会话 | `~/.chaos-code/memory/long_term.json` |
| 项目级记忆 | 特定项目 | `~/.chaos-code/memory/project_*.json` |

#### 7.2 记忆属性

```python
class MemoryItem(BaseModel):
    content: str           # 记忆内容
    memory_type: str       # 记忆类型
    importance: int        # 重要性 1-10
    tags: List[str]        # 标签
    expires_at: str        # 过期时间
```

---

## 数据流

### 1. 用户输入处理流程

```
用户输入 → CLI/TUI → Agent.run()
    ↓
添加到消息历史
    ↓
调用 LLM (带工具 schemas)
    ↓
LLM 返回响应
    ↓
┌── 有工具调用? ─────────────────┐
│ 是                             │ 否
↓                                ↓
权限检查 → 确认(可选) → 执行工具  返回响应给用户
    ↓
工具结果添加到消息历史
    ↓
继续调用 LLM...
```

### 2. MCP 工具调用流程

```
Agent 请求 MCP 工具
    ↓
MCPToolAdapter.execute()
    ↓
MCPManager.call_tool()
    ↓
MCPClient.call_tool()
    ↓
Transport.send(JSONRPCRequest)
    ↓
MCP Server 执行
    ↓
Transport.receive(JSONRPCResponse)
    ↓
返回 ToolResult
```

---

## 配置系统

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| CHAOS_CODE_DEFAULT_MODEL | 默认模型 | gpt-4o |
| CHAOS_CODE_API_KEY | API Key | - |
| CHAOS_CODE_API_BASE | API Base URL | - |
| CHAOS_CODE_MAX_TURNS | 最大对话轮数 | 20 |
| CHAOS_CODE_DEFAULT_MODE | 默认模式 | build |
| CHAOS_CODE_AUTO_CONFIRM | 自动确认 | false |
| CHAOS_CODE_MCP_CONFIG_PATH | MCP 配置路径 | - |

### .env 文件示例

```bash
# 阿里云通义千问
CHAOS_CODE_API_KEY=sk-xxx
CHAOS_CODE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
CHAOS_CODE_DEFAULT_MODEL=openai/qwen-plus

# OpenAI
# OPENAI_API_KEY=sk-...

# Anthropic
# ANTHROPIC_API_KEY=sk-ant-...
```

### MCP 配置文件

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"],
      "env": {}
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

---

## 扩展开发

### 添加新工具

```python
from chaos_code.tools.base import ToolBase, ToolContext, ToolResult

class MyTool(ToolBase):
    name = "my_tool"
    description = "我的自定义工具"
    parameters_schema = {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数1"}
        },
        "required": ["param1"]
    }

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        result = do_something(params["param1"])
        return ToolResult(success=True, output=result)

    def should_confirm(self, params: dict) -> bool:
        return True  # 需要确认
```

### 添加新的 MCP 服务器

```python
from chaos_code.mcp import MCPServerConfig, MCPManager

config = MCPServerConfig(
    name="my_server",
    command="python",
    args=["-m", "my_mcp_server"],
)

manager = MCPManager()
await manager.connect_server(config)
```

### 自定义权限规则

```python
from chaos_code.permission import PermissionRule, PermissionLevel

rule = PermissionRule(
    name="禁止删除",
    level=PermissionLevel.DENY,
    tools=["bash"],
    params={"command": "~^rm.*"},
    priority=100,
)

manager.add_rule(rule)
```

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_agent.py -v

# 带覆盖率
pytest tests/ --cov=chaos_code --cov-report=html
```

### 测试结构

```
tests/
├── conftest.py        # 测试配置
├── test_agent.py      # Agent 测试
├── test_tools.py      # 工具测试
├── test_permission.py # 权限系统测试
├── test_mcp.py        # MCP 测试
├── test_tui.py        # TUI 测试
└── test_session.py    # 会话测试
```

---

## 开发历程

| 阶段 | 内容 | 提交 |
|------|------|------|
| 阶段一 | MVP 核心功能 | 0bb7f6c |
| 阶段二 | 权限与安全系统 | 754de64 |
| 阶段三 | MCP 协议支持 | 89f0f96 |
| 阶段四 | TUI 界面 | 93e52a1 |
| 阶段五 | 高级功能 | d660729 |

---

## 参考项目

| 项目 | 语言 | 借鉴要点 |
|------|------|----------|
| [OpenCode](https://github.com/opencode-ai/opencode) | TypeScript/Bun | Agent 架构、工具系统、权限系统、build/plan 模式 |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | TypeScript | 工具确认机制、Subagent 架构、Schema 验证 |
| [MS-Agent](https://github.com/microsoft/autogen) | Python | MCP 协议、多 LLM 后端、Memory 系统 |

---

## 许可证

MIT License
