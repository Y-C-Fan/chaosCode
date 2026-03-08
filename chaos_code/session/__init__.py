"""
会话管理模块

[MS-Agent 参考: 会话持久化和记忆系统]

## 功能

### 会话管理
- 会话创建、保存、加载
- 会话历史浏览
- 会话导入导出

### 记忆系统
- 短期记忆（会话内）
- 长期记忆（跨会话）
- 项目级记忆

## 使用示例

### 会话管理
```python
from chaos_code.session import SessionManager

# 创建会话管理器
manager = SessionManager()

# 创建新会话
session = manager.create_session(name="开发讨论", model="gpt-4o")

# 添加消息
session.add_message("user", "帮我分析这个项目")

# 保存会话
manager.save_session(session)

# 加载历史会话
sessions = manager.list_sessions()
```

### 记忆系统
```python
from chaos_code.session import MemoryManager, MemoryType

# 创建记忆管理器
memory = MemoryManager()

# 记住重要信息
memory.remember(
    "用户偏好使用 Python 进行开发",
    memory_type=MemoryType.LONG_TERM,
    importance=8,
    tags=["preference", "language"],
)

# 回忆
results = memory.recall("Python", memory_type=MemoryType.LONG_TERM)

# 获取 Agent 上下文
context = memory.get_context_for_agent()
```
"""

from chaos_code.session.manager import (
    Session,
    SessionMessage,
    SessionManager,
)
from chaos_code.session.memory import (
    MemoryItem,
    MemoryManager,
    MemoryStore,
    MemoryType,
)

__all__ = [
    # 会话管理
    "Session",
    "SessionMessage",
    "SessionManager",
    # 记忆系统
    "MemoryType",
    "MemoryItem",
    "MemoryStore",
    "MemoryManager",
]
