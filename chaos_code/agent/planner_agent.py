"""
Planner Agent - 规划助手

[OpenCode 参考: PlannerAgent 实现]
"""

from typing import Optional

from chaos_code.agent.base import Agent, AgentMode
from chaos_code.llm import LLM
from chaos_code.tools import ToolRegistry


class PlannerAgent(Agent):
    """
    规划 Agent [OpenCode 参考]

    只读模式的规划助手，可以：
    - 分析项目结构
    - 阅读代码
    - 制定开发计划
    - 不执行任何修改操作
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
            mode=AgentMode.PLAN,
            system_prompt=system_prompt,
        )

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是 ChaosCode Planner，一个专业的 AI 项目规划助手。

## 核心能力
- 分析项目结构和代码
- 理解代码逻辑和架构
- 制定开发计划
- 提供建议和方案

## 工作模式
你是**只读模式**，只能：
- 读取文件内容
- 搜索文件和代码
- 分析和理解

你**不能**：
- 修改任何文件
- 执行终端命令
- 进行任何写入操作

## 工作原则
1. **全面分析**: 先阅读相关文件，理解上下文
2. **清晰规划**: 提供详细的、分步骤的开发计划
3. **风险评估**: 指出潜在问题和注意事项
4. **最佳实践**: 建议符合项目风格的实现方式

请根据用户需求，分析现有代码并制定详细的开发计划。"""


# 为了兼容性
__all__ = ["PlannerAgent"]
