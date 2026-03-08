"""
会话管理模块

[MS-Agent 参考: 会话持久化和恢复]

支持会话的保存、加载和历史管理
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class SessionMessage(BaseModel):
    """会话消息"""

    role: str = Field(..., description="角色: user/assistant/tool")
    content: str = Field(default="", description="消息内容")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """
    会话模型

    存储一次完整的对话会话
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(default="新会话", description="会话名称")
    model: str = Field(default="", description="使用的模型")
    mode: str = Field(default="build", description="会话模式")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    messages: List[SessionMessage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """
        添加消息

        Args:
            role: 角色
            content: 内容
            metadata: 元数据
        """
        msg = SessionMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()

    def clear_messages(self) -> None:
        """清除所有消息"""
        self.messages.clear()
        self.updated_at = datetime.now().isoformat()

    def to_agent_messages(self) -> List[Dict[str, Any]]:
        """
        转换为 Agent 消息格式

        Returns:
            List[Dict]: Agent 可用的消息列表
        """
        result = []
        for msg in self.messages:
            result.append({
                "role": msg.role,
                "content": msg.content,
            })
        return result

    def get_summary(self) -> str:
        """
        获取会话摘要

        Returns:
            str: 会话摘要
        """
        first_user_msg = ""
        for msg in self.messages:
            if msg.role == "user" and msg.content:
                first_user_msg = msg.content[:50]
                break

        return f"{self.name} ({len(self.messages)} 条消息) - {first_user_msg}..."


class SessionManager:
    """
    会话管理器

    负责会话的持久化、加载和管理

    Attributes:
        storage_dir: 会话存储目录
        sessions: 当前加载的会话列表
        current_session: 当前活动会话
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        初始化会话管理器

        Args:
            storage_dir: 会话存储目录，默认为 ~/.chaos-code/sessions
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".chaos-code" / "sessions"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.sessions: Dict[str, Session] = {}
        self.current_session: Optional[Session] = None

    def create_session(
        self,
        name: str = "新会话",
        model: str = "",
        mode: str = "build",
    ) -> Session:
        """
        创建新会话

        Args:
            name: 会话名称
            model: 使用的模型
            mode: 会话模式

        Returns:
            Session: 新创建的会话
        """
        session = Session(
            name=name,
            model=model,
            mode=mode,
        )
        self.sessions[session.id] = session
        self.current_session = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话

        Args:
            session_id: 会话 ID

        Returns:
            Optional[Session]: 会话实例，如果不存在则返回 None
        """
        return self.sessions.get(session_id)

    def get_current_session(self) -> Optional[Session]:
        """获取当前活动会话"""
        return self.current_session

    def set_current_session(self, session_id: str) -> bool:
        """
        设置当前活动会话

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        if session_id in self.sessions:
            self.current_session = self.sessions[session_id]
            return True
        return False

    def save_session(self, session: Session) -> Path:
        """
        保存会话到文件

        Args:
            session: 会话实例

        Returns:
            Path: 保存的文件路径
        """
        file_path = self.storage_dir / f"{session.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)
        return file_path

    def load_session(self, session_id: str) -> Optional[Session]:
        """
        从文件加载会话

        Args:
            session_id: 会话 ID

        Returns:
            Optional[Session]: 加载的会话，如果不存在则返回 None
        """
        file_path = self.storage_dir / f"{session_id}.json"
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = Session(**data)
        self.sessions[session.id] = session
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        # 从内存中删除
        if session_id in self.sessions:
            del self.sessions[session_id]

        # 删除文件
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def list_sessions(self) -> List[Session]:
        """
        列出所有已保存的会话

        Returns:
            List[Session]: 会话列表
        """
        sessions = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                session = Session(**data)
                if session.id not in self.sessions:
                    self.sessions[session.id] = session
                sessions.append(session)
            except (json.JSONDecodeError, Exception):
                continue

        # 按更新时间排序
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def search_sessions(self, query: str) -> List[Session]:
        """
        搜索会话

        Args:
            query: 搜索关键词

        Returns:
            List[Session]: 匹配的会话列表
        """
        all_sessions = self.list_sessions()
        query_lower = query.lower()

        results = []
        for session in all_sessions:
            # 搜索名称
            if query_lower in session.name.lower():
                results.append(session)
                continue

            # 搜索消息内容
            for msg in session.messages:
                if query_lower in msg.content.lower():
                    results.append(session)
                    break

        return results

    def export_session(self, session_id: str, export_path: Path) -> bool:
        """
        导出会话

        Args:
            session_id: 会话 ID
            export_path: 导出路径

        Returns:
            bool: 是否成功
        """
        session = self.get_session(session_id) or self.load_session(session_id)
        if not session:
            return False

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)
        return True

    def import_session(self, import_path: Path) -> Optional[Session]:
        """
        导入会话

        Args:
            import_path: 导入文件路径

        Returns:
            Optional[Session]: 导入的会话
        """
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = Session(**data)
        self.sessions[session.id] = session
        self.save_session(session)
        return session

    def get_session_count(self) -> int:
        """获取会话总数"""
        return len(self.list_sessions())

    def clear_all_sessions(self) -> int:
        """
        清除所有会话

        Returns:
            int: 清除的会话数量
        """
        count = 0
        for file_path in self.storage_dir.glob("*.json"):
            file_path.unlink()
            count += 1

        self.sessions.clear()
        self.current_session = None
        return count
