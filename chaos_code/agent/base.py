"""
Agent 基类

[OpenCode 参考: Agent 基础架构]
[MS-Agent 参考: LLMAgent 设计]
"""

import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional

from chaos_code.llm import LLM, LLMResponse, Message
from chaos_code.permission import PermissionManager, PermissionLevel, create_default_manager
from chaos_code.tools import ToolRegistry
from chaos_code.tools.base import ToolContext


class AgentMode(str, Enum):
    """
    Agent 运行模式 [OpenCode 参考]

    - BUILD: 全功能模式，可以执行所有操作
    - PLAN: 只读规划模式，仅分析不执行
    """

    BUILD = "build"
    PLAN = "plan"


class Agent(ABC):
    """
    Agent 基类 [OpenCode 整体架构 + MS-Agent LLMAgent 参考]

    所有 Agent 的基类，定义核心接口和工具调用流程

    Attributes:
        llm: LLM 实例
        tools: 工具注册表
        max_turns: 最大对话轮数
        messages: 消息历史
        mode: 运行模式
    """

    def __init__(
        self,
        llm: LLM,
        tools: ToolRegistry,
        max_turns: int = 20,
        mode: AgentMode = AgentMode.BUILD,
        system_prompt: Optional[str] = None,
        permission_manager: Optional[PermissionManager] = None,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.max_turns = max_turns
        self.mode = mode
        self.messages: List[Message] = []
        self.session_id = str(uuid.uuid4())[:8]
        self._system_prompt = system_prompt

        # 创建工具上下文
        self.context = ToolContext()

        # 权限管理器
        self.permission_manager = permission_manager or create_default_manager()

    @property
    def system_prompt(self) -> str:
        """获取系统提示"""
        if self._system_prompt:
            return self._system_prompt
        return self._get_default_system_prompt()

    @abstractmethod
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        pass

    def add_message(self, message: Message) -> None:
        """添加消息到历史"""
        self.messages.append(message)

    def clear_history(self) -> None:
        """清除消息历史"""
        self.messages.clear()

    async def run(self, user_input: str) -> AsyncGenerator[Message, None]:
        """
        运行 Agent 主循环 [OpenCode 工具调用循环]

        Args:
            user_input: 用户输入

        Yields:
            Message: 每一轮的消息
        """
        # 添加用户消息
        self.messages.append(Message.user(user_input))

        turn_count = 0
        while turn_count < self.max_turns:
            turn_count += 1

            # 调用 LLM
            response = await self._call_llm()

            # 添加助手消息
            self.messages.append(response.message)
            yield response.message

            # 检查是否有工具调用
            if response.message.tool_calls:
                # 执行工具调用
                for tool_call in response.message.tool_calls:
                    result = await self._execute_tool(tool_call)
                    self.messages.append(result)
                    yield result
            else:
                # 没有工具调用，结束循环
                break

    async def _call_llm(self) -> LLMResponse:
        """调用 LLM [MS-Agent 参考]"""
        # 构建消息列表（包含系统提示）
        messages = [Message.system(self.system_prompt)] + self.messages

        # 获取工具 schemas
        tools = self.tools.get_schemas() if self.mode == AgentMode.BUILD else None

        # 调用 LLM
        response = await self.llm.generate(messages=messages, tools=tools)

        return response

    async def _execute_tool(self, tool_call) -> Message:
        """
        执行工具调用 [OpenCode + Gemini CLI 确认机制]

        Args:
            tool_call: 工具调用请求

        Returns:
            Message: 工具执行结果消息
        """
        from chaos_code.llm import ToolCall

        if not isinstance(tool_call, ToolCall):
            # 兼容其他格式
            tool_call = ToolCall(
                id=getattr(tool_call, "id", ""),
                name=getattr(tool_call, "name", ""),
                arguments=getattr(tool_call, "arguments", {}),
            )

        # 获取工具
        tool = self.tools.get(tool_call.name)
        if not tool:
            return Message.tool_result(
                tool_call_id=tool_call.id,
                content=f"错误：未知工具 '{tool_call.name}'",
                is_error=True,
            )

        # 权限检查
        decision = self.permission_manager.check_permission(
            tool_call.name,
            tool_call.arguments,
        )

        # 如果被拒绝
        if decision.is_denied:
            return Message.tool_result(
                tool_call_id=tool_call.id,
                content=f"操作被拒绝: {decision.reason}",
                is_error=True,
                name=tool_call.name,
            )

        # 如果需要确认
        if decision.needs_confirmation:
            # 获取操作描述
            description = tool.get_description(tool_call.arguments)

            # 请求确认
            decision = await self.permission_manager.request_confirmation(
                tool_call.name,
                tool_call.arguments,
                description,
            )

            if decision.is_denied:
                return Message.tool_result(
                    tool_call_id=tool_call.id,
                    content=f"用户拒绝操作: {decision.reason}",
                    is_error=True,
                    name=tool_call.name,
                )

        # 执行工具
        result = await tool.execute(tool_call.arguments, self.context)

        # 返回结果消息
        return Message.tool_result(
            tool_call_id=tool_call.id,
            content=result.output if result.success else f"错误: {result.error}",
            is_error=not result.success,
            name=tool_call.name,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} mode={self.mode.value} session={self.session_id}>"
