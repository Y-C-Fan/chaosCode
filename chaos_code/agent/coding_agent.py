"""
Coding Agent - 编程助手

[OpenCode 参考: CodingAgent 实现]
"""

from typing import Optional

from chaos_code.agent.base import Agent, AgentMode
from chaos_code.llm import LLM
from chaos_code.tools import ToolRegistry


class CodingAgent(Agent):
    """
    编程 Agent [OpenCode 参考]

    全功能的编程助手，可以：
    - 执行终端命令
    - 读写编辑文件
    - 搜索文件和内容
    - 完成各种编程任务
    """

    def __init__(
        self,
        llm: LLM,
        tools: ToolRegistry,
        max_turns: int = 20,
        system_prompt: Optional[str] = None,
    ) -> None:
        super().__init__(
            llm=llm,
            tools=tools,
            max_turns=max_turns,
            mode=AgentMode.BUILD,
            system_prompt=system_prompt,
        )

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是 ChaosCode，一个专业的 AI 编程助手。

## 核心能力
- 执行终端命令（bash）
- 读取和写入文件
- 编辑现有代码
- 搜索文件和代码内容
- 分析和理解项目结构

## 工作原则
1. **理解优先**: 在修改代码前，先阅读并理解现有代码
2. **精确修改**: 使用 edit 工具进行精确的字符串替换，避免大范围重写
3. **安全执行**: 危险操作（如删除文件）需要谨慎
4. **清晰沟通**: 解释你的操作和决策理由

## 工具使用指南
- `read`: 读取文件内容，了解现有代码
- `write`: 创建新文件
- `edit`: 编辑现有文件，使用 old_string/new_string 进行替换
- `bash`: 执行终端命令
- `glob`: 搜索文件
- `grep`: 搜索代码内容

请根据用户需求，使用合适的工具完成任务。每次只做必要的修改，保持代码简洁。"""


# 为了兼容性，保留 Agent 别名
__all__ = ["CodingAgent"]
