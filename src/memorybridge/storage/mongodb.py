"""
MongoDB 存储后端实现

使用 MongoDB 作为存储后端，支持：
- 大规模数据存储
- 灵活的查询
- 水平扩展
- 全文搜索索引
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.memory import Memory, MemoryPriority, MemoryType
from ..core.service import MemoryService


class MongoDBStorage(MemoryService):
    """MongoDB 存储后端实现

    特点:
    - 支持大规模数据
    - 灵活的查询能力
    - 支持索引优化
    - 适合分布式部署

    Requires:
        pip install pymongo
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        database: str = "memorybridge",
        collection: str = "memories",
    ):
        """初始化 MongoDB 存储

        Args:
            connection_string: MongoDB 连接字符串
                (默认：mongodb://localhost:27017)
            database: 数据库名称 (默认：memorybridge)
            collection: 集合名称 (默认：memories)
        """
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure
        except ImportError:
            raise ImportError(
                "pymongo not installed. Install with: pip install pymongo"
            )

        self.connection_string = connection_string or "mongodb://localhost:27017"
        self.database_name = database
        self.collection_name = collection

        # 连接 MongoDB
        try:
            self.client = MongoClient(
                self.connection_string, serverSelectionTimeoutMS=5000
            )
            # 测试连接
            self.client.admin.command("ping")
        except ConnectionFailure as e:
            raise ConnectionFailure(
                f"Failed to connect to MongoDB: {e}"
            ) from e

        self.db = self.client[database]
        self.collection = self.db[collection]

        # 创建索引
        self._create_indexes()

    def _create_indexes(self) -> None:
        """创建必要的索引"""
        from pymongo import ASCENDING, DESCENDING, TEXT

        # 基础索引
        self.collection.create_index([("memory_type", ASCENDING)])
        self.collection.create_index([("priority", ASCENDING)])
        self.collection.create_index([("created_at", DESCENDING)])
        self.collection.create_index([("updated_at", DESCENDING)])

        # 全文搜索索引
        self.collection.create_index([("content", TEXT)])

        # 标签索引
        self.collection.create_index([("tags", ASCENDING)])

        # 复合索引
        self.collection.create_index(
            [("memory_type", ASCENDING), ("created_at", DESCENDING)]
        )
        self.collection.create_index(
            [("priority", ASCENDING), ("created_at", DESCENDING)]
        )

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

        # 插入文档
        doc = {
            "_id": memory.id,
            "content": memory.content,
            "memory_type": memory.memory_type.value,
            "priority": memory.priority.value,
            "metadata": memory.metadata,
            "tags": memory.tags,
            "embedding": memory.embedding,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
        }

        self.collection.insert_one(doc)
        return memory

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """搜索记忆

        支持:
        - 全文搜索 ($text)
        - 精确匹配
        - 正则表达式
        """
        filters = filters or {}

        # 构建查询条件
        query_filter: Dict[str, Any] = {}

        # 全文搜索
        if query:
            query_filter["$text"] = {"$search": query}

        # 类型过滤
        if "memory_type" in filters:
            query_filter["memory_type"] = filters["memory_type"]

        # 优先级过滤
        if "priority" in filters:
            query_filter["priority"] = filters["priority"]

        # 标签过滤
        if "tags" in filters:
            tags_filter = filters["tags"]
            if isinstance(tags_filter, list):
                query_filter["tags"] = {"$in": tags_filter}
            else:
                query_filter["tags"] = tags_filter

        # 执行查询
        cursor = self.collection.find(query_filter).sort(
            "created_at", -1
        ).limit(limit)

        return [self._doc_to_memory(doc) for doc in cursor]

    async def get(self, memory_id: str) -> Optional[Memory]:
        """获取单条记忆"""
        doc = self.collection.find_one({"_id": memory_id})
        if doc:
            return self._doc_to_memory(doc)
        return None

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        result = self.collection.delete_one({"_id": memory_id})
        return result.deleted_count > 0

    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """更新记忆"""
        # 先获取现有记忆
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

        # 更新到数据库
        update_data = {
            "content": memory.content,
            "metadata": memory.metadata,
            "tags": memory.tags,
            "updated_at": memory.updated_at,
        }

        self.collection.update_one(
            {"_id": memory_id},
            {"$set": update_data},
        )

        return memory

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        memory_type: Optional[MemoryType] = None,
    ) -> List[Memory]:
        """列出记忆"""
        query_filter = {}
        if memory_type:
            query_filter["memory_type"] = memory_type.value

        cursor = self.collection.find(query_filter).sort(
            "created_at", -1
        ).skip(offset).limit(limit)

        return [self._doc_to_memory(doc) for doc in cursor]

    async def export(self, format: str = "json") -> str:
        """导出记忆"""
        cursor = self.collection.find({}).sort("created_at", 1)
        memories = [self._doc_to_memory(doc).to_dict() for doc in cursor]

        if format == "json":
            return json.dumps(memories, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def import_memories(self, data: str, format: str = "json") -> int:
        """导入记忆"""
        if format != "json":
            raise ValueError(f"Unsupported format: {format}")

        memories_data = json.loads(data)
        count = 0

        for mem_dict in memories_data:
            try:
                memory = Memory.from_dict(mem_dict)
                doc = {
                    "_id": memory.id,
                    "content": memory.content,
                    "memory_type": memory.memory_type.value,
                    "priority": memory.priority.value,
                    "metadata": memory.metadata,
                    "tags": memory.tags,
                    "embedding": memory.embedding,
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at,
                }
                self.collection.replace_one(
                    {"_id": memory.id}, doc, upsert=True
                )
                count += 1
            except Exception as e:
                print(f"Failed to import memory: {e}")
                continue

        return count

    async def count(self, memory_type: Optional[MemoryType] = None) -> int:
        """统计记忆数量"""
        query_filter = {}
        if memory_type:
            query_filter["memory_type"] = memory_type.value
        return self.collection.count_documents(query_filter)

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行聚合查询

        Args:
            pipeline: MongoDB 聚合管道

        Returns:
            聚合结果列表
        """
        cursor = self.collection.aggregate(pipeline)
        return list(cursor)

    async def drop_database(self) -> None:
        """删除整个数据库（危险操作！）"""
        self.client.drop_database(self.database_name)

    def _doc_to_memory(self, doc: Dict[str, Any]) -> Memory:
        """将 MongoDB 文档转换为 Memory 对象"""
        return Memory(
            id=doc["_id"],
            content=doc["content"],
            memory_type=MemoryType(doc["memory_type"]),
            priority=MemoryPriority(doc["priority"]),
            metadata=doc.get("metadata", {}),
            tags=doc.get("tags", []),
            embedding=doc.get("embedding"),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at"),
        )

    def __repr__(self) -> str:
        return (
            f"MongoDBStorage(database='{self.database_name}', "
            f"collection='{self.collection_name}')"
        )
