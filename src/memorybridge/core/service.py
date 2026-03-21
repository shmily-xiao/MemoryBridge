"""
Memory Service 抽象接口

定义 Memory 服务的标准 API
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .memory import Memory, MemoryPriority, MemoryType


class MemoryService(ABC):
    """Memory as a Service - 抽象基类

    定义记忆管理的标准接口，所有存储后端必须实现这些方法
    """

    @abstractmethod
    async def add(
        self,
        content: str,
        metadata: Optional[Dict[str, any]] = None,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        priority: MemoryPriority = MemoryPriority.P1,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """添加记忆

        Args:
            content: 记忆内容
            metadata: 元数据 (可选)
            memory_type: 记忆类型 (默认 long_term)
            priority: 优先级 (默认 p1)
            tags: 标签列表 (可选)

        Returns:
            创建的 Memory 对象
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, any]] = None,
    ) -> List[Memory]:
        """搜索记忆

        Args:
            query: 搜索关键词
            limit: 返回数量限制 (默认 10)
            filters: 过滤条件 (可选)

        Returns:
            Memory 对象列表
        """
        pass

    @abstractmethod
    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取单条记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            Memory 对象，不存在返回 None
        """
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """删除记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """更新记忆

        Args:
            memory_id: 记忆 ID
            content: 新内容 (可选)
            metadata: 新元数据 (可选)
            tags: 新标签 (可选)

        Returns:
            更新后的 Memory 对象
        """
        pass

    @abstractmethod
    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        memory_type: Optional[MemoryType] = None,
    ) -> List[Memory]:
        """列出记忆

        Args:
            limit: 返回数量限制 (默认 20)
            offset: 偏移量 (默认 0)
            memory_type: 记忆类型过滤 (可选)

        Returns:
            Memory 对象列表
        """
        pass

    @abstractmethod
    async def export(self, format: str = "json") -> str:
        """导出记忆

        Args:
            format: 导出格式 (json/csv)

        Returns:
            导出的数据字符串
        """
        pass

    @abstractmethod
    async def import_memories(self, data: str, format: str = "json") -> int:
        """导入记忆

        Args:
            data: 导入的数据字符串
            format: 数据格式 (json/csv)

        Returns:
            成功导入的记忆数量
        """
        pass

    @abstractmethod
    async def count(self, memory_type: Optional[MemoryType] = None) -> int:
        """统计记忆数量

        Args:
            memory_type: 记忆类型过滤 (可选)

        Returns:
            记忆数量
        """
        pass
