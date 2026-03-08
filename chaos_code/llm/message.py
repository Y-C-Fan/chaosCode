"""
消息类型定义

[OpenCode + MS-Agent 参考: 消息结构设计]
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """工具调用请求 [OpenCode 参考]"""

    id: str = Field(..., description="工具调用唯一标识")
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式"""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """转换为 Anthropic 格式"""
        return {
            "id": self.id,
            "type": "tool_use",
            "name": self.name,
            "input": self.arguments,
        }


class ToolResult(BaseModel):
    """工具执行结果 [OpenCode + MS-Agent 参考]"""

    tool_call_id: str = Field(..., description="对应的工具调用 ID")
    content: str = Field(..., description="执行结果内容")
    is_error: bool = Field(default=False, description="是否为错误结果")

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式"""
        return {
            "tool_call_id": self.tool_call_id,
            "role": "tool",
            "content": self.content,
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """转换为 Anthropic 格式"""
        result_type = "tool_result" if not self.is_error else "error"
        return {
            "type": "tool_result",
            "tool_use_id": self.tool_call_id,
            "content": self.content,
            "is_error": self.is_error,
        }


class Message(BaseModel):
    """
    通用消息类型 [OpenCode + MS-Agent 参考]

    支持 OpenAI 和 Anthropic 两种格式
    """

    role: Literal["user", "assistant", "system", "tool"] = Field(
        ..., description="消息角色"
    )
    content: str = Field(default="", description="消息内容")
    tool_calls: Optional[List[ToolCall]] = Field(
        default=None, description="工具调用列表"
    )
    tool_call_id: Optional[str] = Field(
        default=None, description="工具调用 ID（仅 role=tool 时）"
    )
    name: Optional[str] = Field(default=None, description="工具名称（仅 role=tool 时）")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式 [OpenCode 参考]"""
        msg: Dict[str, Any] = {
            "role": self.role,
            "content": self.content if self.content else None,
        }

        if self.tool_calls:
            msg["tool_calls"] = [tc.to_openai_format() for tc in self.tool_calls]

        if self.role == "tool" and self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        if self.name:
            msg["name"] = self.name

        # 移除 None 值
        return {k: v for k, v in msg.items() if v is not None}

    def to_anthropic_format(self) -> Dict[str, Any]:
        """转换为 Anthropic 格式 [MS-Agent 参考]"""
        if self.role == "system":
            return {"role": "system", "content": self.content}

        if self.role == "tool":
            # Anthropic 的工具结果格式
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": self.tool_call_id,
                        "content": self.content,
                    }
                ],
            }

        msg: Dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }

        if self.tool_calls:
            msg["content"] = []
            if self.content:
                msg["content"].append({"type": "text", "text": self.content})
            for tc in self.tool_calls:
                msg["content"].append(tc.to_anthropic_format())

        return msg

    @classmethod
    def user(cls, content: str) -> "Message":
        """创建用户消息"""
        return cls(role="user", content=content)

    @classmethod
    def assistant(
        cls,
        content: str = "",
        tool_calls: Optional[List[ToolCall]] = None,
    ) -> "Message":
        """创建助手消息"""
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def system(cls, content: str) -> "Message":
        """创建系统消息"""
        return cls(role="system", content=content)

    @classmethod
    def tool_result(
        cls,
        tool_call_id: str,
        content: str,
        is_error: bool = False,
        name: Optional[str] = None,
    ) -> "Message":
        """创建工具结果消息"""
        return cls(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            metadata={"is_error": is_error},
        )
