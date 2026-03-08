"""
工具基类定义

[OpenCode 参考: 工具接口设计]
[Gemini CLI 参考: should_confirm 确认机制]
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from chaos_code.llm.base import ToolSchema


class ToolResult(BaseModel):
    """
    工具执行结果 [MS-Agent 参考]

    Attributes:
        success: 是否成功
        output: 输出内容
        error: 错误信息
        metadata: 额外元数据
    """

    success: bool = Field(..., description="执行是否成功")
    output: str = Field(default="", description="输出内容")
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"[错误] {self.error}"


class ToolContext(BaseModel):
    """
    工具执行上下文 [OpenCode 参考]

    包含执行工具所需的环境信息
    """

    working_directory: str = Field(default=".", description="工作目录")
    session_id: Optional[str] = Field(default=None, description="会话 ID")
    user_id: Optional[str] = Field(default=None, description="用户 ID")
    env: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    max_output_length: int = Field(default=10000, description="最大输出长度")

    class Config:
        arbitrary_types_allowed = True


class ToolBase(ABC):
    """
    工具基类 [OpenCode 整体架构 + Gemini CLI 确认机制]

    所有工具必须继承此类并实现 execute 方法

    Attributes:
        name: 工具名称
        description: 工具描述
        parameters_schema: 参数 JSON Schema
    """

    name: str = "base_tool"
    description: str = "基础工具"
    parameters_schema: Dict[str, Any] = {}

    def get_schema(self) -> ToolSchema:
        """获取工具 Schema"""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.parameters_schema,
        )

    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """
        执行工具 [OpenCode + MS-Agent 参考]

        Args:
            params: 工具参数
            context: 执行上下文

        Returns:
            ToolResult: 执行结果
        """
        pass

    def should_confirm(self, params: Dict[str, Any]) -> bool:
        """
        是否需要用户确认 [Gemini CLI 参考]

        危险操作（如删除文件、执行 shell 命令）应返回 True

        Args:
            params: 工具参数

        Returns:
            bool: 是否需要确认
        """
        return False

    def get_description(self, params: Dict[str, Any]) -> str:
        """
        获取本次调用的描述 [Gemini CLI 参考]

        用于在确认对话框中显示

        Args:
            params: 工具参数

        Returns:
            str: 调用描述
        """
        return f"执行 {self.name}"

    def _truncate_output(self, output: str, max_length: int) -> str:
        """截断输出"""
        if len(output) > max_length:
            return output[:max_length] + f"\n... (已截断，共 {len(output)} 字符)"
        return output

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
