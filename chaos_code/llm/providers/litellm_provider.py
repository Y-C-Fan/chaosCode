"""
LiteLLM Provider 实现

[MS-Agent 参考: litellm 统一后端]
[原创: 简化实现，专注核心功能]
"""

import json
from typing import Any, Dict, List, Optional

import litellm
from litellm import acompletion

from chaos_code.llm.base import LLM, LLMResponse, ToolSchema
from chaos_code.llm.message import Message, ToolCall


class LiteLLMProvider(LLM):
    """
    LiteLLM 统一后端 [MS-Agent 参考]

    支持 OpenAI、Anthropic、DeepSeek、阿里云通义千问 等多种模型

    模型名称格式:
        - OpenAI: "gpt-4o", "gpt-4o-mini"
        - Anthropic: "claude-3-opus-20240229", "claude-3-sonnet-20240229"
        - DeepSeek: "deepseek/deepseek-chat"
        - 阿里云通义千问: "qwen-plus", "qwen-turbo", "qwen-max" (需要设置 base_url)
        - 其他: 参考 litellm 文档
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> None:
        super().__init__(model, api_key, base_url, **kwargs)
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 配置 litellm
        if api_key:
            self._setup_api_key()

        if base_url:
            litellm.api_base = base_url

        # 启用缓存以提高性能
        litellm.cache = None  # 禁用内置缓存，使用自定义缓存

        # 阿里云通义千问需要设置 drop_params
        litellm.drop_params = True

    def _setup_api_key(self) -> None:
        """根据模型类型设置 API Key"""
        model_lower = self.model.lower()

        if "claude" in model_lower or "anthropic" in model_lower:
            litellm.anthropic_key = self.api_key
        elif "deepseek" in model_lower:
            # DeepSeek 使用 OpenAI 兼容 API
            litellm.openai_key = self.api_key
        elif "qwen" in model_lower:
            # 阿里云通义千问使用 OpenAI 兼容 API
            litellm.openai_key = self.api_key
        elif "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
            litellm.openai_key = self.api_key
        else:
            # 默认设置为 OpenAI key
            litellm.openai_key = self.api_key

    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        生成响应 [litellm 实现]

        Args:
            messages: 消息历史
            tools: 可用工具列表
            **kwargs: 额外参数

        Returns:
            LLMResponse: 响应结果
        """
        # 转换消息格式
        formatted_messages = self._format_messages(messages)

        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        # 添加工具
        if tools:
            request_params["tools"] = self._convert_tools_to_openai(tools)
            request_params["tool_choice"] = kwargs.get("tool_choice", "auto")

        # 调用 litellm
        try:
            response = await acompletion(**request_params)
            return self._parse_response(response)
        except Exception as e:
            # 错误处理
            return LLMResponse(
                message=Message.assistant(f"错误: {str(e)}"),
                finish_reason="error",
                model=self.model,
            )

    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        **kwargs,
    ):
        """
        流式生成响应 [litellm 实现]

        Args:
            messages: 消息历史
            tools: 可用工具列表
            **kwargs: 额外参数

        Yields:
            响应片段 (str 或 ToolCall)
        """
        formatted_messages = self._format_messages(messages)

        request_params = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": True,
        }

        if tools:
            request_params["tools"] = self._convert_tools_to_openai(tools)

        try:
            response = await acompletion(**request_params)

            current_content = ""
            tool_calls_data: Dict[int, Dict[str, Any]] = {}

            async for chunk in response:
                delta = chunk.choices[0].delta

                # 处理文本内容
                if delta.content:
                    current_content += delta.content
                    yield delta.content

                # 处理工具调用
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_data:
                            tool_calls_data[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.function:
                            if tc.function.name:
                                tool_calls_data[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_data[idx]["arguments"] += tc.function.arguments

            # 返回完整的工具调用
            for tc_data in tool_calls_data.values():
                try:
                    args = json.loads(tc_data["arguments"])
                except json.JSONDecodeError:
                    args = {}

                yield ToolCall(
                    id=tc_data["id"],
                    name=tc_data["name"],
                    arguments=args,
                )

        except Exception as e:
            yield f"\n[错误: {str(e)}]"

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """格式化消息列表"""
        formatted = []

        for msg in messages:
            # 系统消息单独处理
            if msg.role == "system":
                formatted.append({"role": "system", "content": msg.content})
                continue

            # 工具结果消息
            if msg.role == "tool":
                formatted.append(msg.to_openai_format())
                continue

            # 普通消息
            formatted.append(msg.to_openai_format())

        return formatted

    def _parse_response(self, response: Any) -> LLMResponse:
        """解析响应"""
        choice = response.choices[0]
        message_data = choice.message

        # 解析工具调用
        tool_calls = []
        if message_data.tool_calls:
            for tc in message_data.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        message = Message(
            role="assistant",
            content=message_data.content or "",
            tool_calls=tool_calls if tool_calls else None,
        )

        usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            message=message,
            finish_reason=choice.finish_reason,
            usage=usage,
            model=response.model,
        )
