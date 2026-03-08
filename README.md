# ChaosCode

An AI-powered coding assistant CLI tool built with Python, inspired by the best practices from OpenCode, Gemini CLI, and MS-Agent.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🤖 **Intelligent Agent**: Build mode (full features) and Plan mode (read-only planning)
- 🛠️ **Rich Tools**: Built-in bash, read, write, edit, glob, grep tools
- 🔐 **Permission System**: Three-level permission control with interactive confirmation
- 🔌 **MCP Protocol**: Full support for Anthropic Model Context Protocol
- 💻 **TUI Interface**: Modern terminal interface powered by Textual
- 💾 **Session Management**: Session persistence and history browsing
- 🧠 **Memory System**: Short-term, long-term, and project-level memory

## 📦 Installation

```bash
# Install from source (development mode)
git clone https://github.com/chaos-code/chaos-code.git
cd chaos-code
pip install -e .
```

## 🚀 Quick Start

### Configuration

Create a `.env` file in the project root:

```bash
# Alibaba Cloud Tongyi Qianwen
CHAOS_CODE_API_KEY=sk-xxx
CHAOS_CODE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
CHAOS_CODE_DEFAULT_MODEL=openai/qwen-plus

# OpenAI
# OPENAI_API_KEY=sk-...

# Anthropic
# ANTHROPIC_API_KEY=sk-ant-...
```

Supported models:
- Alibaba Tongyi: `openai/qwen-plus`, `openai/qwen-turbo`, `openai/qwen-max`
- OpenAI: `gpt-4o`, `gpt-4o-mini`
- Anthropic: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- DeepSeek: `deepseek/deepseek-chat`

### Basic Usage

```bash
# Show version
chaos-code --version

# Show help
chaos-code --help

# Single chat
chaos-code chat "Help me create a Python project structure"

# Read-only planning mode
chaos-code chat "Analyze code structure" --mode plan

# Auto-confirm all operations
chaos-code chat "Execute operations" -y

# Interactive REPL
chaos-code repl

# TUI interface
chaos-code tui
```

## 📖 Usage Guide

### CLI Commands

#### chat - Single Conversation

```bash
# Basic usage
chaos-code chat "Your question"

# Specify model
chaos-code chat "Analyze this project" -m gpt-4o

# Specify mode (build/plan)
chaos-code chat "Analyze code structure" --mode plan

# Auto-confirm
chaos-code chat "Execute operation" -y
```

#### repl - Interactive Mode

```bash
chaos-code repl

# Commands inside REPL
/help    # Show help
/clear   # Clear conversation history
/exit    # Exit
```

#### tui - Terminal Interface

```bash
chaos-code tui

# Keyboard shortcuts
Ctrl+Q   # Quit
Ctrl+L   # Clear screen
Ctrl+N   # New session
F1       # Help
```

### Agent Modes

| Mode | Description | Permissions |
|------|-------------|-------------|
| `build` | Full-featured mode | All operations allowed (dangerous ops need confirmation) |
| `plan` | Read-only planning mode | Only read operations, no write/execute |

### Permission System

Three-level permission control:

| Level | Description |
|-------|-------------|
| `allow` | Execute without confirmation |
| `deny` | Block execution |
| `confirm` | Require user confirmation |

Default rules:
- Read operations → Allow
- Write operations → Confirm
- Dangerous commands (rm -rf, etc.) → Confirm

### MCP Configuration

Create a `mcp.json` file:

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

Set environment variable:
```bash
CHAOS_CODE_MCP_CONFIG_PATH=mcp.json
```

## 🏗️ Project Structure

```
chaos_code/
├── cli/                     # CLI commands
├── agent/                   # Agent core
├── llm/                     # LLM integration
├── tools/                   # Tool system
│   ├── bash.py              # Terminal execution
│   ├── file_read.py         # File reading
│   ├── file_write.py        # File writing
│   ├── file_edit.py         # File editing
│   ├── glob.py              # File search
│   └── grep.py              # Content search
├── permission/              # Permission system
├── mcp/                     # MCP protocol
├── tui/                     # TUI interface
├── session/                 # Session management
├── config/                  # Configuration
└── utils/                   # Utilities
```

## 🔧 Advanced Usage

### Session Management

```python
from chaos_code.session import SessionManager

manager = SessionManager()

# Create session
session = manager.create_session(name="Development Discussion")

# Add messages
session.add_message("user", "Help me analyze the project")

# Save session
manager.save_session(session)

# List historical sessions
sessions = manager.list_sessions()
```

### Memory System

```python
from chaos_code.session import MemoryManager, MemoryType

memory = MemoryManager()

# Add long-term memory
memory.remember(
    "User prefers Python development",
    memory_type=MemoryType.LONG_TERM,
    importance=8,
    tags=["preference", "language"],
)

# Search memories
results = memory.recall("Python")

# Get Agent context
context = memory.get_context_for_agent()
```

### Custom Tools

```python
from chaos_code.tools.base import ToolBase, ToolContext, ToolResult

class MyTool(ToolBase):
    name = "my_tool"
    description = "Custom tool"
    parameters_schema = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    }

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        return ToolResult(success=True, output="Result")
```

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=chaos_code
```

## 📚 Documentation

- [Development Guide](docs/DEVELOPMENT.md) - Detailed architecture and development guide
- [Highlights](docs/HIGHLIGHTS.md) - Technical highlights

## 🙏 Acknowledgments

This project incorporates design elements from the following excellent projects:

| Project | Key Contributions |
|---------|-------------------|
| [OpenCode](https://github.com/opencode-ai/opencode) | Agent architecture, tool system, permission control, build/plan mode |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | Tool confirmation mechanism, Subagent architecture |
| [MS-Agent](https://github.com/microsoft/autogen) | MCP protocol, multi-LLM backend, Memory system |

## 📄 License

MIT License
