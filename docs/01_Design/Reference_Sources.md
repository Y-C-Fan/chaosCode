# ChaosCode 设计参考来源标注

本文档明确标注 ChaosCode 项目设计中各功能的参考来源。

---

## 参考项目概览

| 项目 | 语言 | 主要参考价值 |
|------|------|-------------|
| **OpenCode** | TypeScript/Bun | Agent 架构、权限系统、工具定义 |
| **Gemini CLI** | TypeScript | 工具确认机制、Schema 验证、Subagent |
| **MS-Agent** | Python | LLM 集成、MCP 协议、Callback 系统 |

---

## 一、架构设计参考

### 1.1 Agent 架构

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| Agent 基类 + 工具注册表模式 | **OpenCode** | Agent 持有 ToolRegistry，工具调用循环 |
| CodingAgent / PlannerAgent 双模式 | **OpenCode** | build 模式（全功能）和 plan 模式（只读规划）|
| 工具调用循环（tool_calls 处理） | **MS-Agent** | LLMAgent 中的消息处理流程 |
| Callback 生命周期钩子 | **MS-Agent** | `callbacks: List[Callback]` 设计 |

### 1.2 模块划分

| 模块 | 参考来源 | 说明 |
|------|----------|------|
| `tools/` 目录结构 | **OpenCode** | bash.ts, edit.ts, read.ts, write.ts, glob.ts, grep.ts |
| `llm/` 多后端抽象 | **MS-Agent** | 支持 OpenAI、Anthropic、DeepSeek 等多后端 |
| `mcp/` MCP 协议模块 | **MS-Agent** | MCP 客户端和服务端实现 |
| `permission/` 权限系统 | **OpenCode** | 细粒度的工具调用权限控制 |

---

## 二、工具系统参考

### 2.1 工具定义

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| 工具标准化定义（name, description, parameters_schema） | **OpenCode** | TypeScript 接口转 Python 类 |
| `should_confirm()` 方法 | **Gemini CLI** | `ToolInvocation.shouldConfirmExecute()` |
| `get_description()` 方法 | **Gemini CLI** | `ToolInvocation.getDescription()` |
| ToolResult 结构 | **MS-Agent** | success, output, error, metadata |

### 2.2 核心工具

| 工具 | 参考来源 | 说明 |
|------|----------|------|
| BashTool | **OpenCode** | 终端命令执行，支持超时和后台运行 |
| ReadTool | **OpenCode** | 文件读取，支持行号和分页 |
| WriteTool | **OpenCode** | 文件写入 |
| EditTool | **OpenCode** | 字符串替换编辑 |
| GlobTool | **OpenCode** | 文件模式匹配搜索 |
| GrepTool | **OpenCode** | 内容正则搜索 |
| WebFetchTool | **OpenCode** | 网页内容获取 |
| WebSearchTool | **OpenCode** | 网页搜索 |

### 2.3 工具基类设计

```python
# 参考 OpenCode 的工具接口 + Gemini CLI 的确认机制
class ToolBase(ABC):
    name: str                    # [OpenCode]
    description: str             # [OpenCode]
    parameters_schema: Dict      # [OpenCode]

    async def execute()          # [OpenCode, MS-Agent]
    def should_confirm()         # [Gemini CLI]
    def get_description()        # [Gemini CLI]
```

---

## 三、LLM 集成参考

### 3.1 消息类型

| 类型 | 参考来源 | 说明 |
|------|----------|------|
| Message (role, content) | **OpenCode + MS-Agent** | 通用消息结构 |
| ToolCall | **OpenCode** | 工具调用请求 |
| ToolResult | **OpenCode** | 工具执行结果 |

### 3.2 多后端支持

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| litellm 统一后端 | **MS-Agent** | MS-Agent 使用类似抽象层 |
| OpenAI 格式兼容 | **OpenCode + MS-Agent** | 两者都支持 OpenAI API 格式 |
| Anthropic 格式支持 | **OpenCode** | 支持 Claude 系列模型 |

---

## 四、权限与安全系统参考

### 4.1 权限控制

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| 细粒度权限规则 | **OpenCode** | 按工具、路径、操作类型配置权限 |
| 用户配置权限策略 | **OpenCode** | 配置文件定义允许/禁止的操作 |
| 危险操作确认机制 | **Gemini CLI** | Confirmation Bus 处理危险操作 |

### 4.2 Agent 模式

| 模式 | 参考来源 | 说明 |
|------|----------|------|
| Build 模式 | **OpenCode** | 全功能模式，可执行所有操作 |
| Plan 模式 | **OpenCode** | 只读规划模式，需要确认才执行 |

---

## 五、MCP 协议参考

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| MCP 客户端连接 | **MS-Agent** | 连接外部 MCP 服务器 |
| MCP 工具调用 | **MS-Agent** | 将 MCP 工具包装为本地工具 |
| MCP 资源访问 | **MS-Agent** | 访问 MCP 提供的资源 |
| MCP 配置格式 | **MS-Agent** | mcp_servers 配置项 |

---

## 六、高级功能参考

### 6.1 Memory 系统

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| 短期记忆（会话内） | **MS-Agent** | Memory Tools 设计 |
| 长期记忆（跨会话） | **MS-Agent** | 持久化存储 |
| 项目级记忆 | **OpenCode** | 项目上下文管理 |

### 6.2 Subagent 架构

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| 任务分解 | **Gemini CLI** | Subagent 任务委派机制 |
| 子 Agent 委派 | **Gemini CLI** | 复杂任务分解为子任务 |
| 结果聚合 | **Gemini CLI** | 收集子 Agent 结果 |

### 6.3 Skills 系统

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| 可扩展技能模块 | **OpenCode** | Skill 系统设计 |
| Anthropic Agent Skills 协议 | **MS-Agent** | 技能定义和加载 |

---

## 七、CLI 与 TUI 参考

### 7.1 CLI 设计

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| typer + rich CLI 框架 | **原创选型** | Python 生态现代 CLI 工具 |
| REPL 交互模式 | **OpenCode + Gemini CLI** | 交互式对话 |

### 7.2 TUI 界面

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| textual 异步 TUI 框架 | **原创选型** | Python 异步 TUI 库 |
| 聊天界面布局 | **Gemini CLI** | React/Ink 的 TUI 布局参考 |
| 工具调用可视化 | **Gemini CLI** | 显示工具执行过程 |

---

## 八、配置与验证参考

| 设计要点 | 参考来源 | 说明 |
|----------|----------|------|
| pydantic 配置验证 | **Gemini CLI (Zod)** | Gemini 用 Zod，Python 用 pydantic |
| JSON Schema 参数验证 | **Gemini CLI** | 工具参数 schema 验证 |

---

## 九、参考来源标注图示

```
ChaosCode 设计来源分布
========================

Agent 系统
├── Agent 基类架构 ─────────────── [OpenCode]
├── 工具调用循环 ───────────────── [OpenCode + MS-Agent]
├── build/plan 双模式 ──────────── [OpenCode]
└── Callback 钩子 ──────────────── [MS-Agent]

工具系统
├── 工具定义接口 ───────────────── [OpenCode]
├── 确认机制 ───────────────────── [Gemini CLI]
├── 核心工具列表 ───────────────── [OpenCode]
└── ToolResult 结构 ───────────── [MS-Agent]

LLM 集成
├── 多后端抽象 ─────────────────── [MS-Agent]
├── litellm 统一层 ─────────────── [原创选型，参考 MS-Agent]
└── 消息类型 ───────────────────── [OpenCode + MS-Agent]

权限系统
├── 细粒度权限规则 ─────────────── [OpenCode]
├── 危险操作确认 ───────────────── [Gemini CLI]
└── 模式切换 ───────────────────── [OpenCode]

MCP 协议
├── 客户端实现 ─────────────────── [MS-Agent]
├── 工具包装 ───────────────────── [MS-Agent]
└── 配置格式 ───────────────────── [MS-Agent]

高级功能
├── Memory 系统 ────────────────── [MS-Agent]
├── Subagent ───────────────────── [Gemini CLI]
└── Skills ─────────────────────── [OpenCode + MS-Agent]

界面
├── CLI 框架 ───────────────────── [原创选型]
├── TUI 框架 ───────────────────── [原创选型]
└── 布局设计 ───────────────────── [Gemini CLI 参考]
```

---

## 十、总结

| 参考项目 | 主要贡献 |
|----------|----------|
| **OpenCode** | Agent 架构、工具系统、权限系统、Agent 模式 |
| **Gemini CLI** | 工具确认机制、Subagent 架构、Schema 验证 |
| **MS-Agent** | Python 实现参考、MCP 协议、多 LLM 后端、Memory 系统 |

**原创选型**：
- typer + rich (CLI 框架)
- textual (TUI 框架)
- pydantic (配置验证)
- litellm (LLM 统一层)
