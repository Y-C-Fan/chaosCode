"""
权限管理器

[OpenCode 参考: 权限检查和配置]
[Gemini CLI 参考: 确认机制]
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from chaos_code.permission.rules import (
    PermissionDecision,
    PermissionLevel,
    PermissionRule,
    RuleMatcher,
)


class PermissionConfig(BaseModel):
    """
    权限配置

    Attributes:
        rules: 权限规则列表
        default_level: 默认权限级别
        confirm_timeout: 确认超时（秒）
    """

    rules: List[PermissionRule] = Field(default_factory=list, description="权限规则列表")
    default_level: PermissionLevel = Field(
        default=PermissionLevel.CONFIRM,
        description="默认权限级别",
    )
    confirm_timeout: int = Field(default=60, description="确认超时（秒）")


class ConfirmationRequest(BaseModel):
    """
    确认请求 [Gemini CLI 参考]

    用于向用户请求操作确认

    Attributes:
        id: 请求 ID
        tool_name: 工具名称
        description: 操作描述
        params: 工具参数
        rule: 触发确认的规则
        timeout: 超时时间（秒）
    """

    id: str = Field(..., description="请求 ID")
    tool_name: str = Field(..., description="工具名称")
    description: str = Field(default="", description="操作描述")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    rule: Optional[PermissionRule] = Field(default=None, description="触发确认的规则")
    timeout: int = Field(default=60, description="超时时间（秒）")


class ConfirmationResponse(BaseModel):
    """
    确认响应 [Gemini CLI 参考]

    用户对确认请求的响应

    Attributes:
        request_id: 对应的请求 ID
        approved: 是否批准
        remember: 是否记住选择（应用于后续相同操作）
        reason: 响应原因（可选）
    """

    request_id: str = Field(..., description="请求 ID")
    approved: bool = Field(..., description="是否批准")
    remember: bool = Field(default=False, description="是否记住选择")
    reason: str = Field(default="", description="响应原因")


class PermissionManager:
    """
    权限管理器 [OpenCode 参考]

    管理权限规则、检查权限、处理确认请求

    Attributes:
        config: 权限配置
        matcher: 规则匹配器
        confirm_handler: 确认处理回调函数
        remember_cache: 记住的决策缓存
    """

    def __init__(
        self,
        config: Optional[PermissionConfig] = None,
        confirm_handler: Optional[Callable[[ConfirmationRequest], ConfirmationResponse]] = None,
    ):
        """
        初始化权限管理器

        Args:
            config: 权限配置，如果为 None 则使用默认配置
            confirm_handler: 确认处理回调函数
        """
        self.config = config or PermissionConfig()
        self.matcher = RuleMatcher(self.config.rules)
        self.confirm_handler = confirm_handler
        self.remember_cache: Dict[str, PermissionLevel] = {}

    def check_permission(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> PermissionDecision:
        """
        检查权限

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            PermissionDecision: 权限决策结果
        """
        # 先检查记忆缓存
        cache_key = self._get_cache_key(tool_name, params)
        if cache_key in self.remember_cache:
            level = self.remember_cache[cache_key]
            return PermissionDecision(
                level=level,
                reason=f"使用记住的决策: {level.value}",
            )

        # 匹配规则
        rule = self.matcher.match(tool_name, params)

        if rule:
            return PermissionDecision(
                level=rule.level,
                rule=rule,
                reason=f"匹配规则: {rule.name}",
            )

        # 使用默认级别
        return PermissionDecision(
            level=self.config.default_level,
            reason="使用默认权限级别",
        )

    async def request_confirmation(
        self,
        tool_name: str,
        params: Dict[str, Any],
        description: str = "",
    ) -> PermissionDecision:
        """
        请求确认

        Args:
            tool_name: 工具名称
            params: 工具参数
            description: 操作描述

        Returns:
            PermissionDecision: 权限决策结果
        """
        import uuid

        # 创建确认请求
        request = ConfirmationRequest(
            id=str(uuid.uuid4())[:8],
            tool_name=tool_name,
            description=description,
            params=params,
            timeout=self.config.confirm_timeout,
        )

        # 如果有确认处理回调，调用它
        if self.confirm_handler:
            response = self.confirm_handler(request)
        else:
            # 默认行为：在 CLI 中交互式确认
            response = await self._interactive_confirm(request)

        # 处理响应
        if response.approved:
            level = PermissionLevel.ALLOW
        else:
            level = PermissionLevel.DENY

        # 如果用户选择记住，缓存决策
        if response.remember:
            cache_key = self._get_cache_key(tool_name, params)
            self.remember_cache[cache_key] = level

        return PermissionDecision(
            level=level,
            reason=f"用户{'批准' if response.approved else '拒绝'}操作",
        )

    async def _interactive_confirm(self, request: ConfirmationRequest) -> ConfirmationResponse:
        """
        交互式确认（CLI）

        Args:
            request: 确认请求

        Returns:
            ConfirmationResponse: 确认响应
        """
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        # 显示确认提示
        console.print(Panel.fit(
            f"[bold]工具:[/] {request.tool_name}\n"
            f"[bold]描述:[/] {request.description or '执行操作'}\n"
            f"[bold]参数:[/] {request.params}",
            title="[bold yellow]需要确认[/bold yellow]",
            border_style="yellow",
        ))

        # 等待用户输入
        while True:
            try:
                response = console.input(
                    "[bold]是否允许执行? [Y/n/a(始终允许)/d(始终拒绝)]:[/] "
                ).strip().lower()

                if response in ("y", "yes", ""):
                    return ConfirmationResponse(request_id=request.id, approved=True)
                elif response in ("n", "no"):
                    return ConfirmationResponse(request_id=request.id, approved=False)
                elif response in ("a", "always"):
                    return ConfirmationResponse(
                        request_id=request.id,
                        approved=True,
                        remember=True,
                    )
                elif response in ("d", "deny"):
                    return ConfirmationResponse(
                        request_id=request.id,
                        approved=False,
                        remember=True,
                    )
                else:
                    console.print("[red]无效输入，请输入 y/n/a/d[/red]")
            except (KeyboardInterrupt, EOFError):
                return ConfirmationResponse(request_id=request.id, approved=False)

    def _get_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        生成缓存键

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            str: 缓存键
        """
        # 简化参数以生成稳定的键
        import hashlib
        import json

        # 只包含影响决策的关键参数
        key_params = {
            k: str(v)[:100]  # 限制参数值长度
            for k, v in sorted(params.items())
            if k in ("command", "file_path", "pattern", "path")  # 关键参数
        }

        key_str = f"{tool_name}:{json.dumps(key_params, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def add_rule(self, rule: PermissionRule) -> None:
        """
        添加权限规则

        Args:
            rule: 权限规则
        """
        self.config.rules.append(rule)
        self.matcher = RuleMatcher(self.config.rules)

    def clear_remember_cache(self) -> None:
        """清除记忆缓存"""
        self.remember_cache.clear()

    @classmethod
    def load_from_file(cls, config_path: Path) -> "PermissionManager":
        """
        从配置文件加载权限管理器

        Args:
            config_path: 配置文件路径（支持 .json 和 .yaml）

        Returns:
            PermissionManager: 权限管理器实例
        """
        if not config_path.exists():
            return cls()

        content = config_path.read_text(encoding="utf-8")

        if config_path.suffix == ".json":
            data = json.loads(content)
        elif config_path.suffix in (".yaml", ".yml"):
            import yaml

            data = yaml.safe_load(content)
        else:
            raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")

        config = PermissionConfig(**data)
        return cls(config=config)


# 默认权限规则
DEFAULT_RULES = [
    # 读取操作默认允许
    PermissionRule(
        name="允许读取文件",
        level=PermissionLevel.ALLOW,
        tools=["read", "glob", "grep"],
        description="读取文件和搜索操作默认允许",
        priority=10,
    ),
    # 危险命令需要确认
    PermissionRule(
        name="危险命令确认",
        level=PermissionLevel.CONFIRM,
        tools=["bash"],
        params={"command": "~^(rm|dd|mkfs|fdisk|format).*"},
        description="危险命令需要确认",
        priority=20,
    ),
    # 写入文件需要确认
    PermissionRule(
        name="写入文件确认",
        level=PermissionLevel.CONFIRM,
        tools=["write", "edit"],
        description="写入和编辑文件需要确认",
        priority=15,
    ),
]


def create_default_manager() -> PermissionManager:
    """
    创建默认权限管理器

    Returns:
        PermissionManager: 带有默认规则的权限管理器
    """
    config = PermissionConfig(rules=DEFAULT_RULES)
    return PermissionManager(config=config)
