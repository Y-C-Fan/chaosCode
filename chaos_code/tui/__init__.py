"""
TUI 界面模块

[原创选型: textual TUI 框架]
[Gemini CLI 参考: 界面布局和交互]

## 使用方式

### CLI 命令
```bash
# 启动 TUI 界面
chaos-code tui

# 指定模型和模式
chaos-code tui -m gpt-4o --mode build
```

### 快捷键
- `Ctrl+Q`: 退出
- `Ctrl+L`: 清屏
- `Ctrl+N`: 新会话
- `F1`: 帮助

### 命令
- `/help`: 显示帮助
- `/clear`: 清除对话
- `/new`: 新会话
- `/model`: 显示当前模型
- `/mode`: 显示当前模式
"""

from chaos_code.tui.app import ChaosCodeApp, MessageList, InputArea, StatusBar, run_tui

__all__ = [
    "ChaosCodeApp",
    "MessageList",
    "InputArea",
    "StatusBar",
    "run_tui",
]
