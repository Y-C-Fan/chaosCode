# ChaosCode 技术亮点

## 概述

ChaosCode 是一个 AI 编程助手 CLI 工具，在设计和实现上融合了多个优秀开源项目的精华，同时也有自己独特的创新。本文档详细介绍项目的技术亮点。

---

## 🌟 核心亮点

### 1. 多参考融合架构

**借鉴三个优秀项目的精华**：

| 来源 | 借鉴内容 | 创新点 |
|------|----------|--------|
| OpenCode | Agent 架构、工具系统、权限控制、build/plan 模式 | Python 原生实现，更轻量 |
| Gemini CLI | 确认机制、Subagent 架构、Schema 验证 | 简化的确认流程 |
| MS-Agent | MCP 协议、多 LLM 后端、Memory 系统 | 更清晰的模块划分 |

**创新价值**：不是简单复制，而是将三个项目的优点有机融合，形成 Python 生态下的完整解决方案。

---

### 2. 三级权限控制系统

**设计亮点**：

```
┌─────────────────────────────────────────┐
│           Permission Level              │
├───────────┬───────────┬─────────────────┤
│   ALLOW   │   DENY    │    CONFIRM      │
│  (允许)   │  (禁止)   │   (需确认)      │
└───────────┴───────────┴─────────────────┘
            ↓
┌─────────────────────────────────────────┐
│          Permission Rule                │
├─────────────────────────────────────────┤
│ • 工具名匹配（支持通配符 *）            │
│ • 参数匹配（支持正则表达式）            │
│ • 优先级排序（高优先级规则优先）        │
│ • 记忆缓存（避免重复确认）              │
└─────────────────────────────────────────┘
```

**代码示例**：

```python
# 灵活的规则定义
PermissionRule(
    name="危险命令确认",
    level=PermissionLevel.CONFIRM,
    tools=["bash"],
    params={"command": "~^(rm|dd|mkfs).*"},  # 正则匹配
    priority=20,
)
```

**优势**：
- 细粒度控制（工具级别 + 参数级别）
- 灵活匹配（通配符 + 正则）
- 用户友好（记忆缓存避免重复确认）

---

### 3. MCP 协议完整实现

**完整实现 Anthropic MCP 规范**：

```
MCP Architecture
        │
        ├── Protocol Layer (JSON-RPC 2.0)
        │   ├── Request/Response Models
        │   ├── Error Handling
        │   └── Content Types
        │
        ├── Transport Layer
        │   ├── StdioTransport (子进程通信)
        │   └── HTTPTransport (HTTP/SSE)
        │
        └── Application Layer
            ├── Tools (工具调用)
            ├── Resources (资源访问)
            └── Prompts (提示模板)
```

**关键代码**：

```python
class MCPClient:
    async def connect(self) -> InitializeResult:
        """连接并完成握手"""

    async def list_tools(self) -> List[MCPTool]:
        """发现服务器提供的工具"""

    async def call_tool(self, name: str, args: dict) -> ToolResult:
        """调用远程工具"""
```

**创新点**：
- 原生 Python 实现，无额外依赖
- 自动工具发现和适配
- 多服务器统一管理
- 工具名自动添加前缀避免冲突

---

### 4. 双模式 Agent 设计

**build/plan 模式切换**：

| 模式 | 权限范围 | 使用场景 |
|------|----------|----------|
| build | 全功能 | 实际编码、文件操作、命令执行 |
| plan | 只读 | 代码分析、架构设计、方案规划 |

**实现原理**：

```python
class PlannerAgent(Agent):
    @staticmethod
    def _create_readonly_permission_manager():
        """Planner 模式内置只读权限"""
        rules = [
            PermissionRule(level=PermissionLevel.ALLOW, tools=["read", "glob", "grep"]),
            PermissionRule(level=PermissionLevel.DENY, tools=["write", "edit", "bash"]),
        ]
        return PermissionManager(config=PermissionConfig(rules=rules))
```

**优势**：
- 安全可控：plan 模式绝对不会修改文件
- 灵活切换：根据任务选择合适模式
- 清晰提示：系统提示明确告知模式限制

---

### 5. 三级记忆系统

**创新的记忆架构**：

```
┌─────────────────────────────────────────────────┐
│                 Memory System                    │
├─────────────────┬───────────────┬───────────────┤
│   Short-term    │   Long-term   │   Project     │
│   (会话内)      │   (跨会话)    │   (项目级)    │
├─────────────────┼───────────────┼───────────────┤
│ • 临时信息      │ • 用户偏好    │ • 项目配置    │
│ • 对话上下文    │ • 重要决策    │ • 技术栈信息  │
│ • 任务状态      │ • 知识积累    │ • 代码规范    │
└─────────────────┴───────────────┴───────────────┘
```

**核心 API**：

```python
memory = MemoryManager()

# 记住
memory.remember(
    "用户偏好使用 Python 3.10+",
    memory_type=MemoryType.LONG_TERM,
    importance=8,
    tags=["preference", "python"],
)

# 回忆
results = memory.recall("Python", memory_type=MemoryType.LONG_TERM)

# 生成 Agent 上下文
context = memory.get_context_for_agent(project_path="/path/to/project")
```

**优势**：
- 分层存储：不同生命周期数据分开管理
- 重要性排序：关键信息优先返回
- 标签分类：灵活检索
- 自动过期：支持时间敏感记忆

---

### 6. 现代化 TUI 界面

**基于 Textual 框架**：

```
┌─────────────────────────────────────────────────┐
│ ChaosCode v0.1.0                     🕐 10:30:00│
├─────────────────────────────────────────────────┤
│                                                 │
│ 👤 你: 帮我分析这个项目                          │
│                                                 │
│ 🤖 助手: 我来帮你分析...                        │
│                                                 │
│ 🔧 工具: [read] 读取 README.md...               │
│                                                 │
├─────────────────────────────────────────────────┤
│ [输入消息...                          ] [发送]  │
├─────────────────────────────────────────────────┤
│ 模型: gpt-4o | 模式: build | 状态: 就绪         │
├─────────────────────────────────────────────────┤
│ ^Q 退出  ^L 清屏  ^N 新会话  F1 帮助            │
└─────────────────────────────────────────────────┘
```

**特点**：
- 响应式布局：自适应终端大小
- 富文本支持：Markdown 渲染
- 实时状态：模型、模式、运行状态
- 快捷键：高效操作

---

### 7. 统一 LLM 后端

**基于 LiteLLM 的多后端支持**：

```python
# 统一接口，自动适配
llm = create_llm(
    "gpt-4o",
    api_key=settings.api_key,
    base_url=settings.api_base,
)

# 支持:
# - OpenAI (gpt-4o, gpt-4o-mini)
# - Anthropic (claude-3-opus, claude-3-sonnet)
# - 阿里云通义千问 (qwen-plus, qwen-max)
# - DeepSeek (deepseek-chat)
# - 更多...
```

**优势**：
- 一套代码，多后端兼容
- 配置简单，环境变量驱动
- 自动处理 API 差异

---

### 8. 会话持久化

**完整的会话管理**：

```python
class SessionManager:
    # 创建会话
    session = manager.create_session(name="开发讨论")

    # 保存到文件 (~/.chaos-code/sessions/)
    manager.save_session(session)

    # 加载历史会话
    sessions = manager.list_sessions()

    # 搜索会话
    results = manager.search_sessions("Python")

    # 导入导出
    manager.export_session(session.id, "backup.json")
```

**存储格式**：

```json
{
  "id": "abc12345",
  "name": "开发讨论",
  "model": "gpt-4o",
  "mode": "build",
  "created_at": "2026-03-08T10:30:00",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

---

## 📊 技术对比

| 特性 | ChaosCode | OpenCode | Gemini CLI | MS-Agent |
|------|-----------|----------|------------|----------|
| 语言 | Python | TypeScript | TypeScript | Python |
| 权限系统 | ✅ 三级 | ✅ 三级 | ✅ 二级 | ❌ |
| MCP 协议 | ✅ 完整 | ❌ | ❌ | ✅ 完整 |
| TUI 界面 | ✅ Textual | ❌ | ❌ | ❌ |
| 会话管理 | ✅ | ✅ | ❌ | ✅ |
| 记忆系统 | ✅ 三级 | ❌ | ❌ | ✅ 二级 |
| 多 LLM | ✅ LiteLLM | ✅ AI SDK | ✅ Gemini | ✅ 多后端 |

---

## 🏆 设计原则

### 1. 模块化

每个功能独立模块，低耦合高内聚：

```
chaos_code/
├── agent/      # Agent 逻辑
├── tools/      # 工具系统
├── permission/ # 权限系统
├── mcp/        # MCP 协议
├── session/    # 会话管理
└── tui/        # TUI 界面
```

### 2. 可扩展

- 新增工具：继承 `ToolBase`
- 新增权限规则：配置 `PermissionRule`
- 新增 MCP 服务器：配置 `mcp.json`
- 新增 LLM 后端：通过 LiteLLM 自动支持

### 3. 安全优先

- 默认确认危险操作
- Plan 模式只读保护
- 权限规则可配置
- 操作可追溯

### 4. 用户友好

- TUI 界面直观
- CLI 命令简洁
- 错误提示清晰
- 文档完善

---

## 📈 代码质量

| 指标 | 数值 |
|------|------|
| 测试用例 | 72 个 |
| 测试覆盖率 | 高 |
| 代码行数 | ~5000 行 |
| 模块数量 | 8 个 |
| 文档完整性 | 完善 |

---

## 🔮 未来展望

- [ ] Subagent 支持（任务分解、委派、聚合）
- [ ] 更多内置工具（webfetch, websearch）
- [ ] LSP 集成（代码补全、跳转）
- [ ] VS Code 插件
- [ ] 更多 MCP 服务器集成

---

## 总结

ChaosCode 的核心价值在于：

1. **融合创新**：吸收多个优秀项目的精华
2. **Python 原生**：轻量级，易扩展，无重依赖
3. **安全可控**：三级权限，危险操作确认
4. **功能完整**：从 CLI 到 TUI，从会话到记忆
5. **架构清晰**：模块化设计，易于维护和扩展

这使得 ChaosCode 成为 Python 生态下一个功能完善、设计优秀的 AI 编程助手工具。
