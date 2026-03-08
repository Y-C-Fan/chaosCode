# ChaosCode

一个基于 Python 的 AI 辅助编程 CLI 工具，借鉴 OpenCode、Gemini CLI、MS-Agent 三个优秀开源项目的精华设计。

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 核心特性

- 🤖 **智能 Agent**: 支持 build（全功能）和 plan（只读规划）两种模式
- 🛠️ **丰富工具**: 内置 bash、read、write、edit、glob、grep 等工具
- 🔐 **权限系统**: 三级权限控制，危险操作交互式确认
- 🔌 **MCP 协议**: 支持 Anthropic Model Context Protocol
- 💻 **TUI 界面**: 基于 Textual 的现代化终端界面
- 💾 **会话管理**: 会话持久化、历史浏览
- 🧠 **记忆系统**: 短期/长期/项目级三级记忆

## 📦 安装

```bash
# 从源码安装（开发模式）
git clone https://github.com/Y-C-Fan/chaosCode.git
cd chaosCode
pip install -e .
```

## 🚀 快速开始

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

### 基本使用

```bash
# 查看版本
chaos-code --version

# 查看帮助
chaos-code --help

# 单次对话
chaos-code chat "帮我创建一个 Python 项目结构"

# 只读规划模式
chaos-code chat "分析代码结构" --mode plan

# 自动确认所有操作
chaos-code chat "删除临时文件" -y

# 交互式 REPL
chaos-code repl

# TUI 界面
chaos-code tui
```

## 📖 使用指南

### CLI 命令

#### chat - 单次对话

```bash
# 基本用法
chaos-code chat "你的问题"

# 指定模型
chaos-code chat "分析这个项目" -m gpt-4o

# 指定模式 (build/plan)
chaos-code chat "分析代码结构" --mode plan

# 自动确认
chaos-code chat "执行操作" -y
```

#### repl - 交互式 REPL

```bash
chaos-code repl

# REPL 内命令
/help    # 显示帮助
/clear   # 清除对话历史
/exit    # 退出
```

#### tui - 终端界面

```bash
chaos-code tui

# 快捷键
Ctrl+Q   # 退出
Ctrl+L   # 清屏
Ctrl+N   # 新会话
F1       # 帮助
```

### Agent 模式

| 模式 | 说明 | 权限 |
|------|------|------|
| `build` | 全功能模式 | 允许所有操作（危险操作需确认） |
| `plan` | 只读规划模式 | 仅允许读取，禁止写入和执行 |

### 权限系统

系统内置三级权限：

| 级别 | 说明 |
|------|------|
| `allow` | 允许执行，无需确认 |
| `deny` | 禁止执行 |
| `confirm` | 需要用户确认后执行 |

默认规则：
- 读取操作 → 允许
- 写入操作 → 需确认
- 危险命令（rm -rf 等）→ 需确认

### MCP 配置

创建 `mcp.json` 文件：

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

设置环境变量：
```bash
CHAOS_CODE_MCP_CONFIG_PATH=mcp.json
```

## 🏗️ 项目结构

```
chaos_code/
├── cli/                     # CLI 命令
├── agent/                   # Agent 核心
├── llm/                     # LLM 集成
├── tools/                   # 工具系统
│   ├── bash.py              # 终端命令执行
│   ├── file_read.py         # 文件读取
│   ├── file_write.py        # 文件写入
│   ├── file_edit.py         # 文件编辑
│   ├── glob.py              # 文件搜索
│   └── grep.py              # 内容搜索
├── permission/              # 权限系统
├── mcp/                     # MCP 协议
├── tui/                     # TUI 界面
├── session/                 # 会话管理
├── config/                  # 配置系统
└── utils/                   # 工具函数
```

## 🔧 高级用法

### 会话管理

```python
from chaos_code.session import SessionManager

manager = SessionManager()

# 创建会话
session = manager.create_session(name="开发讨论")

# 添加消息
session.add_message("user", "帮我分析项目")

# 保存会话
manager.save_session(session)

# 列出历史会话
sessions = manager.list_sessions()
```

### 记忆系统

```python
from chaos_code.session import MemoryManager, MemoryType

memory = MemoryManager()

# 添加长期记忆
memory.remember(
    "用户偏好使用 Python 开发",
    memory_type=MemoryType.LONG_TERM,
    importance=8,
    tags=["preference", "language"],
)

# 搜索记忆
results = memory.recall("Python")

# 获取 Agent 上下文
context = memory.get_context_for_agent()
```

### 自定义工具

```python
from chaos_code.tools.base import ToolBase, ToolContext, ToolResult

class MyTool(ToolBase):
    name = "my_tool"
    description = "自定义工具"
    parameters_schema = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    }

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        return ToolResult(success=True, output="结果")
```

## 🧪 测试

```bash
# 运行测试
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=chaos_code
```

## 📚 文档

- [开发文档](docs/DEVELOPMENT.md) - 详细的架构和开发指南
- [亮点文档](docs/HIGHLIGHTS.md) - 项目技术亮点
- [README (English)](README_EN.md) - English version

## 🙏 致谢

本项目借鉴了以下优秀项目的设计：

| 项目 | 借鉴要点 |
|------|----------|
| [OpenCode](https://github.com/opencode-ai/opencode) | Agent 架构、工具系统、权限系统、build/plan 模式 |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | 工具确认机制、Subagent 架构 |
| [MS-Agent](https://github.com/microsoft/autogen) | MCP 协议、多 LLM 后端、Memory 系统 |

## 📄 许可证

MIT License
