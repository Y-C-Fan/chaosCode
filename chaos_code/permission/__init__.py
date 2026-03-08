"""
权限系统模块

[OpenCode 参考: 细粒度权限控制]
[Gemini CLI 参考: 确认机制]

## 使用示例

```python
from chaos_code.permission import PermissionManager, PermissionLevel, PermissionRule

# 创建权限管理器
manager = PermissionManager.create_default()

# 检查权限
decision = manager.check_permission("bash", {"command": "ls -la"})
print(decision.level)  # PermissionLevel.CONFIRM 或 ALLOW

# 请求确认
decision = await manager.request_confirmation("bash", {"command": "rm -rf /tmp/test"})
```
"""

from chaos_code.permission.rules import (
    PermissionDecision,
    PermissionLevel,
    PermissionRule,
    RuleMatcher,
    RuleScope,
)
from chaos_code.permission.manager import (
    ConfirmationRequest,
    ConfirmationResponse,
    PermissionConfig,
    PermissionManager,
    create_default_manager,
    DEFAULT_RULES,
)

__all__ = [
    # 规则
    "PermissionLevel",
    "PermissionRule",
    "PermissionDecision",
    "RuleScope",
    "RuleMatcher",
    # 管理器
    "PermissionManager",
    "PermissionConfig",
    "ConfirmationRequest",
    "ConfirmationResponse",
    # 工厂函数
    "create_default_manager",
    # 常量
    "DEFAULT_RULES",
]
