# ChaosCode

一个基于 Python 的 AI 辅助编程 CLI 工具，借鉴 OpenCode、Gemini CLI、MS-Agent 三个优秀开源项目的精华设计。

## 项目定位

- **语言**: Python 3.8+
- **界面**: CLI + TUI (Terminal User Interface)
- **架构**: 模块化、可扩展
- **核心功能**: 代码编辑、文件操作、终端执行、LLM 集成、MCP 协议支持

## 快速开始

### 安装

```bash
# 从源码安装（开发模式）
git clone https://github.com/chaos-code/chaos-code.git
cd chaos-code
pip install -e .
```

### 基本使用

```bash
# 查看版本
chaos-code --version

# 查看帮助
chaos-code --help

# 与 Agent 对话
chaos-code chat "帮我创建一个 Python 项目结构"

# 交互模式
chaos-code repl

# 指定模型
chaos-code chat "分析这个项目" -m openai/qwen-max

# 只读规划模式
chaos-code chat "分析代码结构" --mode plan
```

### 环境配置

在项目根目录创建 `.env` 文件：

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

支持的模型：
- 阿里云通义千问: `openai/qwen-plus`, `openai/qwen-turbo`, `openai/qwen-max`
- OpenAI: `gpt-4o`, `gpt-4o-mini`
- Anthropic: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- DeepSeek: `deepseek/deepseek-chat`

## 项目结构

```
chaos_code/
├── cli/                     # CLI 命令 [原创选型: typer + rich]
├── agent/                   # Agent 核心 [OpenCode 参考]
├── llm/                     # LLM 集成 [MS-Agent 参考]
├── tools/                   # 工具系统 [OpenCode 参考]
│   ├── bash.py              # 终端命令执行
│   ├── file_read.py         # 文件读取
│   ├── file_write.py        # 文件写入
│   ├── file_edit.py         # 文件编辑
│   ├── glob.py              # 文件搜索
│   └── grep.py              # 内容搜索
├── permission/              # 权限系统 [OpenCode + Gemini CLI 参考]
│   ├── rules.py             # 权限规则模型
│   └── manager.py           # 权限管理器
├── mcp/                     # MCP 协议 [Anthropic MCP 规范] ✅ 新增
│   ├── protocol.py          # 协议数据模型
│   ├── client.py            # MCP 客户端
│   └── adapter.py           # 工具适配器
├── session/                 # 会话管理 [待实现]
├── tui/                     # TUI 界面 [原创选型，待实现]
├── config/                  # 配置系统 [原创选型]
└── utils/                   # 工具函数
```

## 参考项目

| 项目 | 语言 | 借鉴要点 |
|------|------|----------|
| **[OpenCode]** | TypeScript/Bun | Agent 架构、工具系统、权限系统、build/plan 模式 |
| **[Gemini CLI]** | TypeScript | 工具确认机制、Subagent 架构、Schema 验证 |
| **[MS-Agent]** | Python | MCP 协议、多 LLM 后端、Memory 系统 |

详细的参考来源标注请参阅: [参考来源文档](docs/01_Design/Reference_Sources.md)

## 开发进度

- [x] **阶段一：MVP 核心功能** ✅ (2026-03-08)
  - [x] 项目结构和 CLI 入口
  - [x] LLM 集成模块（litellm 后端）
  - [x] 工具系统（bash, read, write, edit, glob, grep）
  - [x] Agent 核心（CodingAgent, PlannerAgent）
  - [x] REPL 交互模式
  - [x] 配置系统（.env 支持）
  - [x] 测试用例（15 个测试通过）

- [x] **阶段二：权限与安全系统** ✅ (2026-03-08)
  - [x] 权限规则模型（PermissionRule, PermissionLevel）
  - [x] 权限管理器（PermissionManager）
  - [x] 交互式确认机制
  - [x] Plan 模式只读权限
  - [x] 测试用例（30 个测试通过）

- [x] **阶段三：MCP 协议支持** ✅ (2026-03-08)
  - [x] MCP 协议数据模型（JSON-RPC 2.0）
  - [x] MCP 客户端（Stdio/HTTP 传输）
  - [x] MCP 工具适配器
  - [x] 多服务器管理
  - [x] 测试用例（42 个测试通过）

- [ ] **阶段四：TUI 界面**
- [ ] **阶段五：高级功能**

## 测试

```bash
# 运行测试
pytest tests/ -v

# 安装开发依赖
pip install -e ".[dev]"
```

## 文档

- [开发计划文档](docs/00_TODO/0.1_ChaosCode_Development_Plan.md)
- [参考来源标注](docs/01_Design/Reference_Sources.md)

## 许可证

MIT
