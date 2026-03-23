"""
分层存储策略

根据记忆的类型、优先级和访问时间，自动将数据存储到不同的存储层：
- 热数据层：MongoDB（高频访问的记忆）
- 温数据层：SQLite（中频访问的记忆）
- 冷数据层：OSS（低频访问的归档记忆）
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.memory import Memory, MemoryPriority, MemoryType
from ..core.service import MemoryService
from .oss_backup import OSSBackup


class TieredStorage(MemoryService):
    """分层存储实现

    存储策略:
    - P0/P1 优先级 + Session 类型 → MongoDB (热数据)
    - P2 优先级 + Long-term 类型 → SQLite (温数据)
    - P3 优先级 或 30 天未访问 → OSS (冷数据)

    Args:
        hot_storage: 热数据存储 (MongoDB)
        warm_storage: 温数据存储 (SQLite)
        cold_storage: 冷数据存储 (OSS Backup)
        auto_tier_days: 自动降级天数 (默认 30 天)
    """

    def __init__(
        self,
        hot_storage: MemoryService,
        warm_storage: MemoryService,
        cold_storage: Optional[OSSBackup] = None,
        auto_tier_days: int = 30,
    ):
        self.hot_storage = hot_storage
        self.warm_storage = warm_storage
        self.cold_storage = cold_storage
        self.auto_tier_days = auto_tier_days

        # 存储位置映射
        self._location_map: Dict[str, str] = {}  # memory_id -> storage_type

    def _get_storage_for_memory(self, memory: Memory) -> str:
        """根据记忆属性决定存储位置

        Returns:
            "hot", "warm", or "cold"
        """
        # P0/P1 优先级 → 热存储
        if memory.priority in (MemoryPriority.P0, MemoryPriority.P1):
            return "hot"

        # Session 类型 → 热存储
        if memory.memory_type == MemoryType.SESSION:
            return "hot"

        # P3 优先级 → 冷存储
        if memory.priority == MemoryPriority.P3:
            return "cold" if self.cold_storage else "warm"

        # P2 优先级 → 温存储
        return "warm"

    def _get_storage(self, storage_type: str) -> MemoryService:
        """获取存储实例"""
        if storage_type == "hot":
            return self.hot_storage
        elif storage_type == "warm":
            return self.warm_storage
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")

    async def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        priority: MemoryPriority = MemoryPriority.P1,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """添加记忆"""
        memory = Memory(
            content=content,
            memory_type=memory_type,
            priority=priority,
            metadata=metadata or {},
            tags=tags or [],
        )

        # 决定存储位置
        storage_type = self._get_storage_for_memory(memory)
        storage = self._get_storage(storage_type)

        # 存储记忆
        stored_memory = await storage.add(
            content=content,
            metadata=metadata,
            memory_type=memory_type,
            priority=priority,
            tags=tags,
        )

        # 记录位置
        self._location_map[stored_memory.id] = storage_type

        return stored_memory

    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取记忆（自动从对应存储层读取）"""
        # 先查位置映射
        storage_type = self._location_map.get(memory_id)

        if storage_type:
            storage = self._get_storage(storage_type)
            memory = await storage.get(memory_id)
            
            # 访问热度提升：如果从冷存储访问，可以考虑迁移到温存储
            return memory

        # 位置未知，尝试所有存储层
        for storage_type in ["hot", "warm"]:
            storage = self._get_storage(storage_type)
            memory = await storage.get(memory_id)
            if memory:
                self._location_map[memory_id] = storage_type
                return memory

        return None

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """搜索记忆（搜索所有存储层）"""
        results = []

        # 搜索热存储
        hot_results = await self.hot_storage.search(query, limit=limit, filters=filters)
        results.extend(hot_results)

        # 搜索温存储
        warm_results = await self.warm_storage.search(query, limit=limit, filters=filters)
        results.extend(warm_results)

        # 去重（按 ID）
        seen_ids = set()
        unique_results = []
        for memory in results:
            if memory.id not in seen_ids:
                seen_ids.add(memory.id)
                unique_results.append(memory)

        # 按创建时间排序
        unique_results.sort(key=lambda m: m.created_at, reverse=True)

        return unique_results[:limit]

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        storage_type = self._location_map.get(memory_id)
        
        if storage_type:
            storage = self._get_storage(storage_type)
            success = await storage.delete(memory_id)
            if success:
                del self._location_map[memory_id]
            return success

        # 位置未知，尝试所有存储层
        for storage_type in ["hot", "warm"]:
            storage = self._get_storage(storage_type)
            if await storage.delete(memory_id):
                return True

        return False

    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """更新记忆（可能触发存储层迁移）"""
        # 获取现有记忆
        memory = await self.get(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")

        # 更新字段
        if content is not None:
            memory.content = content
        if metadata is not None:
            memory.metadata = metadata
        if tags is not None:
            memory.tags = tags
        memory.updated_at = datetime.utcnow()

        # 检查是否需要迁移存储层
        new_storage_type = self._get_storage_for_memory(memory)
        current_storage_type = self._location_map.get(memory_id, "warm")

        if new_storage_type != current_storage_type:
            # 需要迁移
            await self._migrate_memory(memory, new_storage_type)
        else:
            # 原地更新
            storage = self._get_storage(current_storage_type)
            await storage.update(
                memory_id=memory_id,
                content=content,
                metadata=metadata,
                tags=tags,
            )

        return memory

    async def _migrate_memory(self, memory: Memory, target_storage_type: str) -> None:
        """迁移记忆到不同存储层"""
        # 从源存储删除
        await self.delete(memory.id)

        # 添加到目标存储
        await self.add(
            content=memory.content,
            metadata=memory.metadata,
            memory_type=memory.memory_type,
            priority=memory.priority,
            tags=memory.tags,
        )

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        memory_type: Optional[MemoryType] = None,
        priority: Optional[MemoryPriority] = None,
    ) -> List[Memory]:
        """列出记忆（从所有存储层）"""
        results = []

        # 列出热存储
        hot_results = await self.hot_storage.list(
            limit=limit, offset=offset, memory_type=memory_type, priority=priority
        )
        results.extend(hot_results)

        if len(results) < limit:
            # 还需要更多，从温存储获取
            warm_results = await self.warm_storage.list(
                limit=limit - len(results),
                offset=0,
                memory_type=memory_type,
                priority=priority,
            )
            results.extend(warm_results)

        return results[:limit]

    async def export(self, format: str = "json") -> str:
        """导出所有记忆"""
        all_memories = []

        # 导出热存储
        hot_data = await self.hot_storage.export(format)
        if format == "json":
            all_memories.extend(json.loads(hot_data))

        # 导出温存储
        warm_data = await self.warm_storage.export(format)
        if format == "json":
            all_memories.extend(json.loads(warm_data))

        # 去重
        seen_ids = set()
        unique_memories = []
        for mem in all_memories:
            if mem["id"] not in seen_ids:
                seen_ids.add(mem["id"])
                unique_memories.append(mem)

        return json.dumps(unique_memories, indent=2, ensure_ascii=False)

    async def import_memories(self, data: str, format: str = "json") -> int:
        """导入记忆"""
        if format != "json":
            raise ValueError(f"Unsupported format: {format}")

        memories_data = json.loads(data)
        count = 0

        for mem_dict in memories_data:
            try:
                memory = Memory.from_dict(mem_dict)
                await self.add(
                    content=memory.content,
                    metadata=memory.metadata,
                    memory_type=memory.memory_type,
                    priority=memory.priority,
                    tags=memory.tags,
                )
                count += 1
            except Exception as e:
                print(f"Failed to import memory: {e}")
                continue

        return count

    async def count(self, memory_type: Optional[MemoryType] = None) -> int:
        """统计记忆总数"""
        hot_count = await self.hot_storage.count(memory_type)
        warm_count = await self.warm_storage.count(memory_type)
        return hot_count + warm_count

    async def tiering_report(self) -> Dict[str, Any]:
        """生成分层存储报告"""
        return {
            "hot_count": await self.hot_storage.count(),
            "warm_count": await self.warm_storage.count(),
            "cold_count": 0,  # OSS 不支持 count
            "total_count": await self.count(),
            "location_map_size": len(self._location_map),
            "auto_tier_days": self.auto_tier_days,
        }

    async def optimize_tiers(self) -> Dict[str, int]:
        """优化存储分层（迁移过期数据）

        Returns:
            迁移统计
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=self.auto_tier_days)
        migrated = {"hot_to_warm": 0, "warm_to_cold": 0}

        # 检查热存储中的旧数据
        hot_memories = await self.hot_storage.list(limit=1000)
        for memory in hot_memories:
            if memory.created_at < cutoff_date and memory.priority == MemoryPriority.P2:
                # 迁移到温存储
                await self._migrate_memory(memory, "warm")
                migrated["hot_to_warm"] += 1

        return migrated

    def __repr__(self) -> str:
        return f"TieredStorage(hot={self.hot_storage}, warm={self.warm_storage})"
