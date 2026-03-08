"""
权限规则模型

[OpenCode 参考: 细粒度权限控制]
[Gemini CLI 参考: 确认机制]
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Pattern
import re

from pydantic import BaseModel, Field, field_validator


class PermissionLevel(str, Enum):
    """
    权限级别 [OpenCode 参考]

    - ALLOW: 允许执行，无需确认
    - DENY: 禁止执行
    - CONFIRM: 需要用户确认后执行
    """

    ALLOW = "allow"
    DENY = "deny"
    CONFIRM = "confirm"


class RuleScope(str, Enum):
    """
    规则作用域

    - TOOL: 工具级别规则（应用于整个工具）
    - PARAM: 参数级别规则（应用于特定参数值）
    """

    TOOL = "tool"
    PARAM = "param"


class PermissionRule(BaseModel):
    """
    权限规则 [OpenCode 参考]

    定义一条权限规则，可以匹配工具名称和参数

    Attributes:
        name: 规则名称
        level: 权限级别（allow/deny/confirm）
        scope: 规则作用域
        tools: 匹配的工具名称列表（支持通配符 *）
        params: 参数匹配规则（仅 scope=PARAM 时有效）
        description: 规则描述
        priority: 优先级（数值越大优先级越高）
    """

    name: str = Field(..., description="规则名称")
    level: PermissionLevel = Field(..., description="权限级别")
    scope: RuleScope = Field(default=RuleScope.TOOL, description="规则作用域")
    tools: List[str] = Field(default_factory=list, description="匹配的工具列表")
    params: Dict[str, Any] = Field(default_factory=dict, description="参数匹配规则")
    description: str = Field(default="", description="规则描述")
    priority: int = Field(default=0, description="优先级")

    @field_validator("tools", mode="before")
    @classmethod
    def ensure_list(cls, v):
        """确保 tools 是列表"""
        if isinstance(v, str):
            return [v]
        return v

    def matches_tool(self, tool_name: str) -> bool:
        """
        检查是否匹配工具名称

        Args:
            tool_name: 工具名称

        Returns:
            bool: 是否匹配
        """
        for pattern in self.tools:
            if self._match_pattern(pattern, tool_name):
                return True
        return False

    def matches_params(self, params: Dict[str, Any]) -> bool:
        """
        检查是否匹配参数

        Args:
            params: 工具参数

        Returns:
            bool: 是否匹配
        """
        if not self.params:
            return True

        for key, expected_value in self.params.items():
            actual_value = params.get(key)
            if not self._match_value(expected_value, actual_value):
                return False
        return True

    def _match_pattern(self, pattern: str, value: str) -> bool:
        """
        匹配模式（支持通配符）

        Args:
            pattern: 模式字符串
            value: 实际值

        Returns:
            bool: 是否匹配
        """
        # 将通配符 * 转换为正则表达式
        regex_pattern = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
        return bool(re.match(regex_pattern, value, re.IGNORECASE))

    def _match_value(self, expected: Any, actual: Any) -> bool:
        """
        匹配值

        Args:
            expected: 期望值
            actual: 实际值

        Returns:
            bool: 是否匹配
        """
        if expected == "*":
            return actual is not None
        if isinstance(expected, str) and expected.startswith("~"):
            # 正则表达式匹配
            pattern = expected[1:]
            return bool(re.match(pattern, str(actual), re.IGNORECASE))
        return expected == actual


class PermissionDecision(BaseModel):
    """
    权限决策结果

    Attributes:
        level: 最终权限级别
        rule: 匹配的规则（如果有）
        reason: 决策原因
    """

    level: PermissionLevel = Field(..., description="权限级别")
    rule: Optional[PermissionRule] = Field(default=None, description="匹配的规则")
    reason: str = Field(default="", description="决策原因")

    @property
    def is_allowed(self) -> bool:
        """是否允许"""
        return self.level == PermissionLevel.ALLOW

    @property
    def is_denied(self) -> bool:
        """是否拒绝"""
        return self.level == PermissionLevel.DENY

    @property
    def needs_confirmation(self) -> bool:
        """是否需要确认"""
        return self.level == PermissionLevel.CONFIRM


class RuleMatcher:
    """
    规则匹配器

    负责根据工具名称和参数匹配权限规则
    """

    def __init__(self, rules: List[PermissionRule]):
        """
        初始化规则匹配器

        Args:
            rules: 权限规则列表
        """
        # 按优先级排序（高优先级在前）
        self.rules = sorted(rules, key=lambda r: r.priority, reverse=True)

    def match(self, tool_name: str, params: Dict[str, Any]) -> Optional[PermissionRule]:
        """
        匹配最合适的规则

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            Optional[PermissionRule]: 匹配的规则，如果没有匹配则返回 None
        """
        for rule in self.rules:
            # 先检查工具名称
            if not rule.matches_tool(tool_name):
                continue

            # 根据作用域检查参数
            if rule.scope == RuleScope.TOOL:
                # 工具级别规则，只要工具匹配就生效
                return rule
            elif rule.scope == RuleScope.PARAM:
                # 参数级别规则，需要参数也匹配
                if rule.matches_params(params):
                    return rule

        return None
