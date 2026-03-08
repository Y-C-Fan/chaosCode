"""
Bash 工具 - 终端命令执行

[OpenCode 参考: bash.ts 实现]
"""

import asyncio
import os
from typing import Any, Dict

from chaos_code.tools.base import ToolBase, ToolContext, ToolResult


class BashTool(ToolBase):
    """
    终端命令执行工具 [OpenCode 参考]

    支持命令执行、超时控制、后台运行

    安全特性:
        - 需要用户确认（危险操作）
        - 支持命令白名单/黑名单
        - 超时保护
    """

    name = "bash"
    description = "在终端执行 shell 命令"

    parameters_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的 shell 命令",
            },
            "timeout": {
                "type": "number",
                "description": "超时时间（毫秒），默认 120000（2 分钟）",
                "default": 120000,
            },
            "run_in_background": {
                "type": "boolean",
                "description": "是否在后台运行",
                "default": False,
            },
            "cwd": {
                "type": "string",
                "description": "工作目录，默认使用当前工作目录",
            },
        },
        "required": ["command"],
    }

    # 危险命令列表
    DANGEROUS_COMMANDS = [
        "rm -rf",
        "rm -r",
        "dd if=",
        "mkfs",
        "fdisk",
        "format",
        "> /dev/",
        "chmod -R 777",
        "chown -R",
        ":(){ :|:& };:",  # Fork bomb
        "shutdown",
        "reboot",
        "init 0",
        "init 6",
    ]

    def should_confirm(self, params: Dict[str, Any]) -> bool:
        """检查是否需要确认 [Gemini CLI 参考]"""
        command = params.get("command", "").lower()

        # 检查危险命令
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous.lower() in command:
                return True

        # 检查是否修改文件系统
        if any(cmd in command for cmd in ["rm ", "mv ", "cp ", "mkdir ", "rmdir "]):
            return True

        return False

    def get_description(self, params: Dict[str, Any]) -> str:
        """获取执行描述"""
        command = params.get("command", "")
        # 截断长命令
        if len(command) > 60:
            command = command[:60] + "..."
        return f"执行命令: {command}"

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """执行 shell 命令"""
        command = params.get("command", "")
        timeout = params.get("timeout", 120000) / 1000  # 转换为秒
        run_in_background = params.get("run_in_background", False)
        cwd = params.get("cwd", context.working_directory)

        if not command:
            return ToolResult(success=False, error="命令不能为空")

        try:
            # 设置环境变量
            env = os.environ.copy()
            env.update(context.env)

            # 后台运行
            if run_in_background:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=cwd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                return ToolResult(
                    success=True,
                    output=f"命令已在后台启动 (PID: {process.pid})",
                    metadata={"pid": process.pid, "background": True},
                )

            # 同步执行
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    error=f"命令执行超时（{timeout}秒）",
                )

            # 处理输出
            output = ""
            if stdout:
                output += stdout.decode("utf-8", errors="replace")
            if stderr:
                output += stderr.decode("utf-8", errors="replace")

            # 截断输出
            output = self._truncate_output(output, context.max_output_length)

            return ToolResult(
                success=process.returncode == 0,
                output=output,
                error=None if process.returncode == 0 else f"退出码: {process.returncode}",
                metadata={"return_code": process.returncode},
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))
