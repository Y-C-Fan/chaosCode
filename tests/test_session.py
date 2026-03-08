"""
会话管理模块测试

[MS-Agent 参考]
"""

import tempfile
from pathlib import Path

import pytest

from chaos_code.session import (
    MemoryItem,
    MemoryManager,
    MemoryStore,
    MemoryType,
    Session,
    SessionManager,
    SessionMessage,
)


class TestSession:
    """测试会话模型"""

    def test_session_creation(self):
        """测试会话创建"""
        session = Session(name="测试会话", model="gpt-4o", mode="build")

        assert session.name == "测试会话"
        assert session.model == "gpt-4o"
        assert session.mode == "build"
        assert len(session.messages) == 0

    def test_session_add_message(self):
        """测试添加消息"""
        session = Session()
        session.add_message("user", "你好")
        session.add_message("assistant", "你好！有什么可以帮助你的？")

        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"

    def test_session_clear_messages(self):
        """测试清除消息"""
        session = Session()
        session.add_message("user", "消息1")
        session.add_message("assistant", "消息2")

        session.clear_messages()

        assert len(session.messages) == 0

    def test_session_to_agent_messages(self):
        """测试转换为 Agent 消息格式"""
        session = Session()
        session.add_message("user", "你好")
        session.add_message("assistant", "你好！")

        agent_messages = session.to_agent_messages()

        assert len(agent_messages) == 2
        assert agent_messages[0]["role"] == "user"
        assert agent_messages[1]["role"] == "assistant"


class TestSessionManager:
    """测试会话管理器"""

    def test_manager_creation(self, tmp_path):
        """测试管理器创建"""
        manager = SessionManager(storage_dir=tmp_path)

        assert manager.storage_dir == tmp_path
        assert len(manager.sessions) == 0

    def test_create_session(self, tmp_path):
        """测试创建会话"""
        manager = SessionManager(storage_dir=tmp_path)
        session = manager.create_session(name="测试", model="gpt-4o")

        assert session.name == "测试"
        assert session.model == "gpt-4o"
        assert manager.current_session == session

    def test_save_and_load_session(self, tmp_path):
        """测试保存和加载会话"""
        manager = SessionManager(storage_dir=tmp_path)

        # 创建并保存
        session = manager.create_session(name="测试")
        session.add_message("user", "测试消息")
        manager.save_session(session)

        # 清除内存
        manager.sessions.clear()
        manager.current_session = None

        # 重新加载
        loaded = manager.load_session(session.id)

        assert loaded is not None
        assert loaded.name == "测试"
        assert len(loaded.messages) == 1

    def test_list_sessions(self, tmp_path):
        """测试列出会话"""
        manager = SessionManager(storage_dir=tmp_path)

        # 创建多个会话
        manager.create_session(name="会话1")
        manager.create_session(name="会话2")
        manager.save_session(manager.sessions[list(manager.sessions.keys())[0]])
        manager.save_session(manager.sessions[list(manager.sessions.keys())[1]])

        sessions = manager.list_sessions()

        assert len(sessions) >= 2

    def test_delete_session(self, tmp_path):
        """测试删除会话"""
        manager = SessionManager(storage_dir=tmp_path)
        session = manager.create_session(name="待删除")
        manager.save_session(session)

        result = manager.delete_session(session.id)

        assert result is True
        assert manager.load_session(session.id) is None


class TestMemoryItem:
    """测试记忆项"""

    def test_memory_item_creation(self):
        """测试记忆项创建"""
        item = MemoryItem(
            content="测试记忆",
            memory_type=MemoryType.LONG_TERM,
            importance=8,
            tags=["test"],
        )

        assert item.content == "测试记忆"
        assert item.memory_type == MemoryType.LONG_TERM
        assert item.importance == 8
        assert "test" in item.tags

    def test_memory_item_not_expired(self):
        """测试未过期的记忆"""
        item = MemoryItem(content="测试")

        assert not item.is_expired()


class TestMemoryStore:
    """测试记忆存储"""

    def test_add_memory(self):
        """测试添加记忆"""
        store = MemoryStore()
        item = store.add_memory(
            content="测试记忆",
            memory_type=MemoryType.SHORT_TERM,
            importance=5,
        )

        assert len(store.memories) == 1
        assert store.memories[0].content == "测试记忆"

    def test_get_memories(self):
        """测试获取记忆"""
        store = MemoryStore()
        store.add_memory("记忆1", importance=8)
        store.add_memory("记忆2", importance=3)
        store.add_memory("记忆3", importance=5)

        # 按重要性过滤
        memories = store.get_memories(min_importance=5)

        assert len(memories) == 2

    def test_search_memories(self):
        """测试搜索记忆"""
        store = MemoryStore()
        store.add_memory("Python 是一门编程语言")
        store.add_memory("Java 也是编程语言")
        store.add_memory("今天天气不错")

        results = store.search_memories("编程")

        assert len(results) == 2

    def test_delete_memory(self):
        """测试删除记忆"""
        store = MemoryStore()
        item = store.add_memory("测试记忆")

        result = store.delete_memory(item.id)

        assert result is True
        assert len(store.memories) == 0


class TestMemoryManager:
    """测试记忆管理器"""

    def test_manager_creation(self, tmp_path):
        """测试管理器创建"""
        manager = MemoryManager(storage_dir=tmp_path)

        assert manager.storage_dir == tmp_path

    def test_short_term_memory(self, tmp_path):
        """测试短期记忆"""
        manager = MemoryManager(storage_dir=tmp_path)
        manager.init_session_memory("test-session")

        manager.remember("短期记忆内容", memory_type=MemoryType.SHORT_TERM)

        memories = manager.recall(memory_type=MemoryType.SHORT_TERM)
        assert len(memories) == 1

    def test_long_term_memory(self, tmp_path):
        """测试长期记忆"""
        manager = MemoryManager(storage_dir=tmp_path)

        manager.remember(
            "长期记忆内容",
            memory_type=MemoryType.LONG_TERM,
            importance=8,
        )

        memories = manager.recall(query="长期", memory_type=MemoryType.LONG_TERM)
        assert len(memories) == 1

    def test_project_memory(self, tmp_path):
        """测试项目级记忆"""
        manager = MemoryManager(storage_dir=tmp_path)

        manager.remember(
            "项目特定信息",
            memory_type=MemoryType.PROJECT,
            project_path="/test/project",
        )

        memories = manager.recall(project_path="/test/project")
        assert len(memories) == 1

    def test_get_context_for_agent(self, tmp_path):
        """测试获取 Agent 上下文"""
        manager = MemoryManager(storage_dir=tmp_path)

        # 添加长期记忆
        manager.remember(
            "重要项目信息",
            memory_type=MemoryType.LONG_TERM,
            importance=8,
        )

        # 添加会话记忆
        manager.init_session_memory("test")
        manager.remember("会话内容", memory_type=MemoryType.SHORT_TERM)

        context = manager.get_context_for_agent()

        assert "重要项目信息" in context
        assert "会话内容" in context

    def test_forget(self, tmp_path):
        """测试遗忘"""
        manager = MemoryManager(storage_dir=tmp_path)
        manager.init_session_memory("test")

        item = manager.remember("待遗忘的内容")
        result = manager.forget(item.id)

        assert result is True
