"""
ChaosCode TUI 应用

[原创选型: textual TUI 框架]
[Gemini CLI 参考: 界面布局和交互]

使用 Textual 实现终端用户界面
"""

from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
)

from chaos_code import __version__
from chaos_code.config import settings


class MessageList(Static):
    """
    消息列表组件

    显示对话历史，包括用户消息和助手回复
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._messages = []

    def add_message(self, role: str, content: str) -> None:
        """
        添加消息

        Args:
            role: 角色 (user/assistant/tool)
            content: 消息内容
        """
        from rich.text import Text

        # 格式化消息
        if role == "user":
            prefix = "👤 你"
            style = "bold green"
        elif role == "assistant":
            prefix = "🤖 助手"
            style = "bold blue"
        else:
            prefix = "🔧 工具"
            style = "dim yellow"

        # 创建富文本
        text = Text()
        text.append(prefix + ": ", style=style)
        text.append(content)

        # 添加到 RichLog
        try:
            log_widget = self.query_one(RichLog)
            log_widget.write(text)
        except Exception:
            pass

    def clear_messages(self) -> None:
        """清除所有消息"""
        try:
            log_widget = self.query_one(RichLog)
            log_widget.clear()
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield RichLog(id="message-log", wrap=True, highlight=True)


class InputArea(Container):
    """
    输入区域组件

    包含输入框和发送按钮
    """

    def compose(self) -> ComposeResult:
        yield Input(placeholder="输入消息，按 Enter 发送...", id="message-input")
        yield Button("发送", id="send-button", variant="primary")


class StatusBar(Static):
    """
    状态栏组件

    显示当前模型、模式等信息
    """

    model = reactive("")
    mode = reactive("")
    status = reactive("就绪")

    def __init__(self, model: str = "", mode: str = "", **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.mode = mode

    def watch_model(self, old_value: str, new_value: str) -> None:
        self._update_display()

    def watch_mode(self, old_value: str, new_value: str) -> None:
        self._update_display()

    def watch_status(self, old_value: str, new_value: str) -> None:
        self._update_display()

    def _update_display(self) -> None:
        self.update(f"模型: {self.model} | 模式: {self.mode} | 状态: {self.status}")

    def compose(self) -> ComposeResult:
        yield Label(self._get_status_text(), id="status-label")

    def _get_status_text(self) -> str:
        return f"模型: {self.model} | 模式: {self.mode} | 状态: {self.status}"


class ChaosCodeApp(App):
    """
    ChaosCode TUI 应用

    主要功能:
    - 聊天界面布局
    - 消息显示
    - 输入交互
    - 快捷键支持
    """

    CSS = """
    Screen {
        background: $surface;
    }

    .main-container {
        layout: vertical;
        height: 100%;
    }

    .message-area {
        height: 1fr;
        border: solid $primary;
        margin: 1;
    }

    .input-area {
        height: auto;
        dock: bottom;
        padding: 1;
    }

    #message-input {
        width: 1fr;
    }

    #send-button {
        width: auto;
        min-width: 10;
    }

    .status-bar {
        dock: bottom;
        height: 1;
        background: $primary-background;
        color: $text;
        padding: 0 1;
    }

    RichLog {
        height: 100%;
        scrollbar-size: 1 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "退出", show=True),
        Binding("ctrl+c", "quit", "退出", show=False),
        Binding("ctrl+l", "clear", "清屏", show=True),
        Binding("ctrl+n", "new_session", "新会话", show=True),
        Binding("f1", "help", "帮助", show=True),
    ]

    def __init__(
        self,
        model: Optional[str] = None,
        mode: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.model = model or settings.default_model
        self.mode = mode or settings.default_mode
        self._agent = None
        self._running = False

    def compose(self) -> ComposeResult:
        """组合界面组件"""
        yield Header(show_clock=True)
        with Container(classes="main-container"):
            with Container(classes="message-area"):
                yield MessageList()
            with Container(classes="input-area"):
                yield InputArea()
        yield StatusBar(model=self.model, mode=self.mode, classes="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """界面挂载时的初始化"""
        self.title = f"ChaosCode v{__version__}"
        self.sub_title = "AI 编程助手"

        # 聚焦到输入框
        self.query_one("#message-input", Input).focus()

        # 显示欢迎消息
        message_list = self.query_one(MessageList)
        message_list.add_message(
            "assistant",
            "欢迎使用 ChaosCode！我是你的 AI 编程助手。有什么我可以帮你的吗？",
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理输入提交事件"""
        if event.input.id == "message-input":
            self._handle_user_input(event.value)
            event.input.clear()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        if event.button.id == "send-button":
            input_widget = self.query_one("#message-input", Input)
            self._handle_user_input(input_widget.value)
            input_widget.clear()

    def _handle_user_input(self, text: str) -> None:
        """
        处理用户输入

        Args:
            text: 用户输入的文本
        """
        if not text.strip():
            return

        # 显示用户消息
        message_list = self.query_one(MessageList)
        message_list.add_message("user", text)

        # 处理特殊命令
        if text.startswith("/"):
            self._handle_command(text)
            return

        # 调用 Agent
        self._call_agent(text)

    def _handle_command(self, command: str) -> None:
        """
        处理命令

        Args:
            command: 命令字符串
        """
        cmd = command.lower().strip()
        message_list = self.query_one(MessageList)

        if cmd in ("/help", "/h"):
            help_text = """
可用命令:
  /help, /h    - 显示帮助
  /clear       - 清除对话
  /new         - 开始新会话
  /model       - 显示当前模型
  /mode        - 显示当前模式

快捷键:
  Ctrl+Q       - 退出
  Ctrl+L       - 清屏
  Ctrl+N       - 新会话
  F1           - 帮助
"""
            message_list.add_message("assistant", help_text)
        elif cmd in ("/clear",):
            message_list.clear_messages()
            message_list.add_message("assistant", "对话已清除")
        elif cmd in ("/new",):
            self.action_new_session()
        elif cmd in ("/model",):
            message_list.add_message("assistant", f"当前模型: {self.model}")
        elif cmd in ("/mode",):
            message_list.add_message("assistant", f"当前模式: {self.mode}")
        else:
            message_list.add_message("assistant", f"未知命令: {command}")

    def _call_agent(self, user_input: str) -> None:
        """
        调用 Agent 处理用户输入

        Args:
            user_input: 用户输入
        """
        import asyncio

        from chaos_code.agent import CodingAgent, PlannerAgent
        from chaos_code.llm import create_llm
        from chaos_code.permission import create_default_manager
        from chaos_code.tools import default_tools

        async def run_agent():
            try:
                # 更新状态
                status_bar = self.query_one(StatusBar)
                status_bar.status = "思考中..."

                # 创建 LLM 和 Agent
                llm = create_llm(
                    self.model,
                    api_key=settings.api_key,
                    base_url=settings.api_base,
                )
                tools = default_tools()
                permission_manager = create_default_manager()

                if self.mode == "plan":
                    agent = PlannerAgent(llm, tools)
                else:
                    agent = CodingAgent(llm, tools, permission_manager=permission_manager)

                # 运行 Agent
                message_list = self.query_one(MessageList)
                assistant_response = ""

                async for msg in agent.run(user_input):
                    if msg.role == "assistant" and msg.content:
                        assistant_response += msg.content
                    elif msg.role == "tool":
                        # 工具调用结果
                        if msg.name:
                            message_list.add_message("tool", f"[{msg.name}] {msg.content[:100]}...")

                # 显示助手响应
                if assistant_response:
                    message_list.add_message("assistant", assistant_response)

                # 更新状态
                status_bar.status = "就绪"

            except Exception as e:
                status_bar = self.query_one(StatusBar)
                status_bar.status = f"错误: {str(e)[:30]}"
                message_list = self.query_one(MessageList)
                message_list.add_message("assistant", f"发生错误: {e}")

        # 运行异步任务
        asyncio.create_task(run_agent())

    def action_quit(self) -> None:
        """退出应用"""
        self.exit()

    def action_clear(self) -> None:
        """清除对话"""
        message_list = self.query_one(MessageList)
        message_list.clear_messages()
        message_list.add_message("assistant", "对话已清除")

    def action_new_session(self) -> None:
        """开始新会话"""
        message_list = self.query_one(MessageList)
        message_list.clear_messages()
        message_list.add_message("assistant", "新会话已开始，有什么我可以帮你的？")

    def action_help(self) -> None:
        """显示帮助"""
        self._handle_command("/help")


def run_tui(model: Optional[str] = None, mode: Optional[str] = None) -> None:
    """
    启动 TUI 应用

    Args:
        model: 使用的模型
        mode: 运行模式
    """
    app = ChaosCodeApp(model=model, mode=mode)
    app.run()


if __name__ == "__main__":
    run_tui()
