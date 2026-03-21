"""
Memory 数据模型

定义记忆的核心数据结构和枚举类型
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class MemoryType(str, Enum):
    """记忆类型枚举"""

    SESSION = "session"  # Session 级短期记忆
    LONG_TERM = "long_term"  # 中长期记忆


class MemoryPriority(str, Enum):
    """记忆优先级枚举

    P0: 最高 - 用户偏好、安全相关
    P1: 高 - 知识点、任务历史
    P2: 中 - 对话摘要
    P3: 低 - 临时上下文
    """

    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


@dataclass
class Memory:
    """记忆数据模型

    Attributes:
        id: 记忆唯一标识符 (UUID)
        content: 记忆内容
        memory_type: 记忆类型 (session/long_term)
        priority: 优先级 (p0/p1/p2/p3)
        metadata: 元数据 (来源、用户 ID 等)
        tags: 标签列表
        embedding: 向量嵌入 (用于语义搜索)
        created_at: 创建时间
        updated_at: 更新时间
    """

    content: str
    memory_type: MemoryType = MemoryType.LONG_TERM
    priority: MemoryPriority = MemoryPriority.P1
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            包含所有字段的字典
        """
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """从字典创建 Memory 对象

        Args:
            data: 包含记忆数据的字典

        Returns:
            Memory 对象
        """
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            priority=MemoryPriority(data["priority"]),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else None
            ),
            embedding=data.get("embedding"),
        )

    def update(self, content: Optional[str] = None, **kwargs) -> "Memory":
        """更新记忆内容

        Args:
            content: 新的内容 (可选)
            **kwargs: 其他要更新的字段

        Returns:
            更新后的 Memory 对象
        """
        if content is not None:
            self.content = content

        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

        self.updated_at = datetime.utcnow()
        return self

    def __str__(self) -> str:
        """字符串表示"""
        return f"Memory(id={self.id[:8]}, type={self.memory_type.value}, priority={self.priority.value})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (
            f"Memory(id='{self.id}', content='{self.content[:50]}...', "
            f"type={self.memory_type.value}, priority={self.priority.value})"
        )
