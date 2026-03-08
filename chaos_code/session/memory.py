"""
Memory 记忆系统

[MS-Agent 参考: Memory 系统]

支持短期记忆和长期记忆的管理
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class MemoryType(str):
    """记忆类型"""

    SHORT_TERM = "short_term"  # 短期记忆（会话内）
    LONG_TERM = "long_term"    # 长期记忆（跨会话）
    PROJECT = "project"        # 项目级记忆


class MemoryItem(BaseModel):
    """单个记忆项"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = Field(..., description="记忆内容")
    memory_type: str = Field(default=MemoryType.SHORT_TERM, description="记忆类型")
    importance: int = Field(default=1, ge=1, le=10, description="重要性 1-10")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = Field(default=None, description="过期时间")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list, description="标签")

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > datetime.fromisoformat(self.expires_at)


class MemoryStore(BaseModel):
    """记忆存储"""

    session_id: Optional[str] = Field(default=None, description="关联的会话 ID")
    project_path: Optional[str] = Field(default=None, description="项目路径")
    memories: List[MemoryItem] = Field(default_factory=list)

    def add_memory(
        self,
        content: str,
        memory_type: str = MemoryType.SHORT_TERM,
        importance: int = 5,
        tags: List[str] = None,
        expires_at: Optional[str] = None,
    ) -> MemoryItem:
        """
        添加记忆

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性
            tags: 标签
            expires_at: 过期时间

        Returns:
            MemoryItem: 创建的记忆项
        """
        item = MemoryItem(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            expires_at=expires_at,
        )
        self.memories.append(item)
        return item

    def get_memories(
        self,
        memory_type: Optional[str] = None,
        tags: List[str] = None,
        min_importance: int = 1,
    ) -> List[MemoryItem]:
        """
        获取记忆

        Args:
            memory_type: 记忆类型过滤
            tags: 标签过滤
            min_importance: 最小重要性

        Returns:
            List[MemoryItem]: 记忆列表
        """
        # 先清理过期的记忆
        self.memories = [m for m in self.memories if not m.is_expired()]

        result = []
        for memory in self.memories:
            # 类型过滤
            if memory_type and memory.memory_type != memory_type:
                continue

            # 重要性过滤
            if memory.importance < min_importance:
                continue

            # 标签过滤
            if tags and not any(t in memory.tags for t in tags):
                continue

            result.append(memory)

        # 按重要性排序
        result.sort(key=lambda m: m.importance, reverse=True)
        return result

    def search_memories(self, query: str) -> List[MemoryItem]:
        """
        搜索记忆

        Args:
            query: 搜索关键词

        Returns:
            List[MemoryItem]: 匹配的记忆
        """
        # 先清理过期的记忆
        self.memories = [m for m in self.memories if not m.is_expired()]

        query_lower = query.lower()
        results = []

        for memory in self.memories:
            if query_lower in memory.content.lower():
                results.append(memory)
            elif any(query_lower in tag.lower() for tag in memory.tags):
                results.append(memory)

        return results

    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            bool: 是否成功
        """
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                self.memories.pop(i)
                return True
        return False

    def clear_memories(self, memory_type: Optional[str] = None) -> int:
        """
        清除记忆

        Args:
            memory_type: 记忆类型，None 表示清除所有

        Returns:
            int: 清除的数量
        """
        if memory_type is None:
            count = len(self.memories)
            self.memories.clear()
            return count

        count = 0
        self.memories = [
            m for m in self.memories
            if m.memory_type != memory_type
        ]
        return count


class MemoryManager:
    """
    记忆管理器

    管理短期记忆、长期记忆和项目级记忆

    Attributes:
        storage_dir: 记忆存储目录
        session_store: 当前会话的短期记忆
        long_term_store: 长期记忆
        project_stores: 项目级记忆缓存
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        初始化记忆管理器

        Args:
            storage_dir: 存储目录，默认为 ~/.chaos-code/memory
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".chaos-code" / "memory"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 短期记忆（会话级）
        self.session_store: Optional[MemoryStore] = None

        # 长期记忆
        self.long_term_store: Optional[MemoryStore] = None

        # 项目级记忆缓存
        self.project_stores: Dict[str, MemoryStore] = {}

    def init_session_memory(self, session_id: str) -> MemoryStore:
        """
        初始化会话记忆

        Args:
            session_id: 会话 ID

        Returns:
            MemoryStore: 会话记忆存储
        """
        self.session_store = MemoryStore(session_id=session_id)
        return self.session_store

    def get_long_term_memory(self) -> MemoryStore:
        """
        获取长期记忆

        Returns:
            MemoryStore: 长期记忆存储
        """
        if self.long_term_store is None:
            # 尝试加载
            file_path = self.storage_dir / "long_term.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.long_term_store = MemoryStore(**data)
            else:
                self.long_term_store = MemoryStore()

        return self.long_term_store

    def get_project_memory(self, project_path: str) -> MemoryStore:
        """
        获取项目级记忆

        Args:
            project_path: 项目路径

        Returns:
            MemoryStore: 项目记忆存储
        """
        if project_path not in self.project_stores:
            # 尝试加载
            project_hash = abs(hash(project_path)) % (10 ** 8)
            file_path = self.storage_dir / f"project_{project_hash}.json"

            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.project_stores[project_path] = MemoryStore(**data)
            else:
                store = MemoryStore(project_path=project_path)
                self.project_stores[project_path] = store

        return self.project_stores[project_path]

    def remember(
        self,
        content: str,
        memory_type: str = MemoryType.SHORT_TERM,
        importance: int = 5,
        tags: List[str] = None,
        project_path: Optional[str] = None,
    ) -> MemoryItem:
        """
        添加记忆

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性
            tags: 标签
            project_path: 项目路径（仅项目级记忆需要）

        Returns:
            MemoryItem: 创建的记忆项
        """
        if memory_type == MemoryType.SHORT_TERM:
            if self.session_store is None:
                self.init_session_memory("default")
            return self.session_store.add_memory(content, memory_type, importance, tags)

        elif memory_type == MemoryType.LONG_TERM:
            store = self.get_long_term_memory()
            return store.add_memory(content, memory_type, importance, tags)

        elif memory_type == MemoryType.PROJECT:
            if not project_path:
                raise ValueError("项目级记忆需要提供 project_path")
            store = self.get_project_memory(project_path)
            return store.add_memory(content, memory_type, importance, tags)

        raise ValueError(f"未知的记忆类型: {memory_type}")

    def recall(
        self,
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: List[str] = None,
        project_path: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        回忆（检索记忆）

        Args:
            query: 搜索关键词
            memory_type: 记忆类型过滤
            tags: 标签过滤
            project_path: 项目路径

        Returns:
            List[MemoryItem]: 记忆列表
        """
        results = []

        # 短期记忆
        if memory_type is None or memory_type == MemoryType.SHORT_TERM:
            if self.session_store:
                if query:
                    results.extend(self.session_store.search_memories(query))
                else:
                    results.extend(self.session_store.get_memories(tags=tags))

        # 长期记忆
        if memory_type is None or memory_type == MemoryType.LONG_TERM:
            store = self.get_long_term_memory()
            if query:
                results.extend(store.search_memories(query))
            else:
                results.extend(store.get_memories(tags=tags))

        # 项目级记忆
        if (memory_type is None or memory_type == MemoryType.PROJECT) and project_path:
            store = self.get_project_memory(project_path)
            if query:
                results.extend(store.search_memories(query))
            else:
                results.extend(store.get_memories(tags=tags))

        # 按重要性排序
        results.sort(key=lambda m: m.importance, reverse=True)
        return results

    def forget(self, memory_id: str) -> bool:
        """
        遗忘（删除记忆）

        Args:
            memory_id: 记忆 ID

        Returns:
            bool: 是否成功
        """
        # 尝试从各个存储中删除
        if self.session_store and self.session_store.delete_memory(memory_id):
            return True

        if self.long_term_store and self.long_term_store.delete_memory(memory_id):
            return True

        for store in self.project_stores.values():
            if store.delete_memory(memory_id):
                return True

        return False

    def save_all(self) -> None:
        """保存所有记忆到文件"""
        # 保存长期记忆
        if self.long_term_store:
            file_path = self.storage_dir / "long_term.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.long_term_store.model_dump(), f, ensure_ascii=False, indent=2)

        # 保存项目级记忆
        for project_path, store in self.project_stores.items():
            project_hash = abs(hash(project_path)) % (10 ** 8)
            file_path = self.storage_dir / f"project_{project_hash}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(store.model_dump(), f, ensure_ascii=False, indent=2)

    def clear_session_memory(self) -> int:
        """
        清除会话记忆

        Returns:
            int: 清除的数量
        """
        if self.session_store:
            return self.session_store.clear_memories()
        return 0

    def get_context_for_agent(self, project_path: Optional[str] = None) -> str:
        """
        获取供 Agent 使用的上下文

        将相关记忆整理成文本格式供 Agent 参考

        Args:
            project_path: 项目路径

        Returns:
            str: 格式化的记忆上下文
        """
        context_parts = []

        # 长期记忆
        long_term = self.get_long_term_memory()
        long_memories = long_term.get_memories(min_importance=7)
        if long_memories:
            context_parts.append("## 重要记忆")
            for m in long_memories[:5]:  # 最多 5 条
                context_parts.append(f"- {m.content}")

        # 项目级记忆
        if project_path:
            project_store = self.get_project_memory(project_path)
            project_memories = project_store.get_memories(min_importance=5)
            if project_memories:
                context_parts.append(f"\n## 项目记忆 ({project_path})")
                for m in project_memories[:5]:
                    context_parts.append(f"- {m.content}")

        # 会话记忆
        if self.session_store:
            session_memories = self.session_store.get_memories()
            if session_memories:
                context_parts.append("\n## 本次会话记忆")
                for m in session_memories:
                    context_parts.append(f"- {m.content}")

        return "\n".join(context_parts) if context_parts else ""
