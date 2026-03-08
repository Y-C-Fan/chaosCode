"""
LLM 抽象基类

[MS-Agent 参考: LLM 后端抽象设计]
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from chaos_code.llm.message import Message, ToolCall


class ToolSchema(BaseModel):
    """工具 Schema 定义 [OpenCode 参考]"""

    name: str
    description: str
    parameters: Dict[str, Any]


class LLMResponse(BaseModel):
    """LLM 响应 [MS-Agent 参考]"""

    message: Message
    finish_reason: str = "stop"
    usage: Dict[str, int] = {}
    model: str = ""


class LLM(ABC):
    """
    LLM 抽象基类 [MS-Agent 参考]

    支持多后端：OpenAI、Anthropic、DeepSeek 等
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        生成响应

        Args:
            messages: 消息历史
            tools: 可用工具列表
            **kwargs: 额外参数

        Returns:
            LLMResponse: 响应结果
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        **kwargs,
    ):
        """
        流式生成响应

        Args:
            messages: 消息历史
            tools: 可用工具列表
            **kwargs: 额外参数

        Yields:
            响应片段
        """
        pass

    def _convert_tools_to_openai(
        self, tools: Optional[List[ToolSchema]]
    ) -> Optional[List[Dict[str, Any]]]:
        """转换工具为 OpenAI 格式 [OpenCode 参考]"""
        if not tools:
            return None

        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def _convert_tools_to_anthropic(
        self, tools: Optional[List[ToolSchema]]
    ) -> Optional[List[Dict[str, Any]]]:
        """转换工具为 Anthropic 格式 [MS-Agent 参考]"""
        if not tools:
            return None

        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    def _parse_tool_calls_openai(self, response: Dict[str, Any]) -> List[ToolCall]:
        """解析 OpenAI 格式的工具调用 [OpenCode 参考]"""
        tool_calls = []
        message = response.get("choices", [{}])[0].get("message", {})

        for tc in message.get("tool_calls", []):
            if tc.get("type") == "function":
                func = tc.get("function", {})
                tool_calls.append(
                    ToolCall(
                        id=tc.get("id", ""),
                        name=func.get("name", ""),
                        arguments=func.get("arguments", {}),
                    )
                )

        return tool_calls

    def _parse_tool_calls_anthropic(self, content: List[Dict[str, Any]]) -> List[ToolCall]:
        """解析 Anthropic 格式的工具调用 [MS-Agent 参考]"""
        tool_calls = []

        for block in content:
            if block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id", ""),
                        name=block.get("name", ""),
                        arguments=block.get("input", {}),
                    )
                )

        return tool_calls

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
