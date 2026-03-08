"""
ChaosCode CLI 主入口

[原创选型: typer + rich CLI 框架]
[OpenCode 参考: build/plan 模式]
"""

import asyncio
import warnings
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# 忽略 litellm 的异步客户端清理警告
warnings.filterwarnings("ignore", message="coroutine 'close_litellm_async_clients'")

from chaos_code import __version__
from chaos_code.config import settings

app = typer.Typer(
    name="chaos-code",
    help="AI 编程助手 CLI 工具 - 借鉴 OpenCode、Gemini CLI、MS-Agent 精华设计",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """显示版本信息"""
    if value:
        console.print(f"[bold blue]ChaosCode[/bold blue] 版本: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="显示版本信息",
    ),
) -> None:
    """
    ChaosCode - AI 编程助手

    借鉴 OpenCode、Gemini CLI、MS-Agent 精华设计的 Python 实现。
    """
    pass


@app.command()
def chat(
    message: str = typer.Argument(..., help="发送给 Agent 的消息"),
    model: str = typer.Option(None, "--model", "-m", help="使用的模型"),
    mode: str = typer.Option(
        None,
        "--mode",
        "-M",
        help="Agent 模式: build(全功能) / plan(只读规划) [OpenCode 参考]",
    ),
    max_turns: int = typer.Option(None, "--max-turns", "-t", help="最大对话轮数"),
    auto_confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="自动确认所有操作（跳过权限确认）",
    ),
) -> None:
    """
    与 Coding Agent 对话

    示例:
        chaos-code chat "帮我创建一个 Python 项目结构"
        chaos-code chat "读取 README.md 并添加使用说明" -m claude-3-opus
        chaos-code chat "分析代码结构" --mode plan
        chaos-code chat "删除临时文件" -y  # 自动确认
    """
    from chaos_code.agent import CodingAgent, PlannerAgent
    from chaos_code.llm import create_llm
    from chaos_code.permission import create_default_manager, PermissionLevel, PermissionConfig
    from chaos_code.tools import default_tools

    # 从配置读取默认值
    model = model or settings.default_model
    mode = mode or settings.default_mode
    max_turns = max_turns or settings.max_turns

    # 显示启动信息
    console.print(Panel.fit(
        f"[bold]模型:[/] {model}\n"
        f"[bold]模式:[/] {mode}\n"
        f"[bold]消息:[/] {message[:50]}{'...' if len(message) > 50 else ''}",
        title="[bold blue]ChaosCode[/bold blue]",
        border_style="blue",
    ))

    # 创建 LLM 和 Agent（使用配置中的 API Key 和 Base URL）
    llm = create_llm(
        model,
        api_key=settings.api_key,
        base_url=settings.api_base,
    )
    tools = default_tools()

    # 创建权限管理器
    if auto_confirm or settings.auto_confirm:
        # 自动确认模式：创建一个允许所有操作的权限管理器
        from chaos_code.permission import PermissionManager
        config = PermissionConfig(default_level=PermissionLevel.ALLOW)
        permission_manager = PermissionManager(config=config)
    else:
        permission_manager = create_default_manager()

    if mode == "plan":
        agent = PlannerAgent(llm, tools, max_turns=max_turns)
    else:
        agent = CodingAgent(llm, tools, max_turns=max_turns, permission_manager=permission_manager)

    # 运行 Agent
    async def run() -> None:
        try:
            async for msg in agent.run(message):
                _print_message(msg)
        except KeyboardInterrupt:
            console.print("\n[yellow]用户中断[/yellow]")
        except Exception as e:
            console.print(f"\n[red]错误: {e}[/red]")

    # 使用 anyio 替代 asyncio.run 以避免 litellm 的警告
    import anyio
    anyio.run(run)


@app.command()
def repl(
    model: str = typer.Option(None, "--model", "-m", help="使用的模型"),
    mode: str = typer.Option(
        None,
        "--mode",
        "-M",
        help="Agent 模式: build(全功能) / plan(只读规划) [OpenCode 参考]",
    ),
) -> None:
    """
    启动交互式 REPL 模式

    [OpenCode + Gemini CLI 交互模式参考]
    """
    from chaos_code.agent import CodingAgent, PlannerAgent
    from chaos_code.llm import create_llm
    from chaos_code.tools import default_tools

    # 从配置读取默认值
    model = model or settings.default_model
    mode = mode or settings.default_mode

    console.print(Panel.fit(
        f"[bold]模型:[/] {model}\n"
        f"[bold]模式:[/] {mode}\n"
        "[dim]输入 /help 查看帮助，/exit 退出[/dim]",
        title="[bold blue]ChaosCode REPL[/bold blue]",
        border_style="blue",
    ))

    llm = create_llm(
        model,
        api_key=settings.api_key,
        base_url=settings.api_base,
    )
    tools = default_tools()

    if mode == "plan":
        agent = PlannerAgent(llm, tools)
    else:
        agent = CodingAgent(llm, tools)

    # REPL 循环
    while True:
        try:
            user_input = console.input("[bold green]你:[/] ").strip()

            if not user_input:
                continue

            # 处理命令
            if user_input.startswith("/"):
                cmd = user_input.lower()
                if cmd in ("/exit", "/quit", "/q"):
                    console.print("[yellow]再见！[/yellow]")
                    break
                elif cmd == "/help":
                    _print_help()
                    continue
                elif cmd == "/clear":
                    agent.messages.clear()
                    console.print("[green]对话历史已清除[/green]")
                    continue
                else:
                    console.print(f"[red]未知命令: {user_input}[/red]")
                    continue

            # 运行 Agent
            async def run() -> None:
                async for msg in agent.run(user_input):
                    _print_message(msg)

            import anyio
            anyio.run(run)

        except KeyboardInterrupt:
            console.print("\n[yellow]使用 /exit 退出[/yellow]")
        except EOFError:
            console.print("\n[yellow]再见！[/yellow]")
            break


def _print_message(msg) -> None:
    """格式化打印消息"""
    from chaos_code.llm import Message

    if not isinstance(msg, Message):
        console.print(str(msg))
        return

    if msg.role == "assistant":
        if msg.content:
            console.print("\n[bold blue]助手:[/]")
            console.print(Markdown(msg.content))
    elif msg.role == "tool":
        # 工具结果简洁显示
        content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
        console.print(f"[dim]{content}[/dim]")


def _print_help() -> None:
    """打印帮助信息"""
    help_text = """
[bold]可用命令:[/]

  /help, /h    显示帮助信息
  /clear       清除对话历史
  /exit, /q    退出 REPL

[bold]使用技巧:[/]

  - 直接输入问题与 AI 对话
  - 使用 --mode plan 进行只读分析
  - 使用 --model 指定不同模型
"""
    console.print(Markdown(help_text))


if __name__ == "__main__":
    app()
