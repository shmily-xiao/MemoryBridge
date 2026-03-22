"""
Haystack DocumentStore 集成

Haystack 是搜索和 RAG 框架，此集成提供：
- DocumentStore 实现
- 文档检索
- 元数据过滤
- 批量操作

Requires:
    pip install farm-haystack
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.memory import Memory, MemoryType, MemoryPriority
from ..storage.factory import create_storage


class HaystackDocumentStore:
    """Haystack DocumentStore 集成
    
    功能：
    - 实现 Haystack BaseDocumentStore 接口
    - 文档持久化
    - 元数据过滤
    - 批量操作
    
    使用示例：
    ```python
    from memorybridge.integrations import HaystackDocumentStore
    from haystack.nodes import Retriever
    
    # 创建 DocumentStore
    doc_store = HaystackDocumentStore(backend="sqlite")
    
    # 写入文档
    docs = [
        {"content": "Python 是一种编程语言", "meta": {"topic": "programming"}},
        {"content": "机器学习是 AI 的核心", "meta": {"topic": "ai"}},
    ]
    await doc_store.write_documents(docs)
    
    # 检索文档
    results = await doc_store.query("Python", top_k=5)
    ```
    """
    
    def __init__(
        self,
        backend: str = "sqlite",
        db_path: Optional[str] = None,
        index: str = "default",
    ):
        """初始化
        
        Args:
            backend: 存储后端
            db_path: 数据库路径
            index: 索引名称
        """
        self.backend = backend
        self.index = index
        config = {"db_path": db_path} if db_path and backend == "sqlite" else {}
        self.storage = create_storage(backend, config)
    
    async def write_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> List[str]:
        """写入文档
        
        Args:
            documents: 文档列表
            batch_size: 批量大小
        
        Returns:
            文档 ID 列表
        """
        ids = []
        for i, doc in enumerate(documents):
            memory = Memory(
                content=doc.get("content", ""),
                memory_type=MemoryType.LONG_TERM,
                priority=MemoryPriority.P2,
                metadata={
                    "source": "haystack",
                    "index": self.index,
                    **(doc.get("meta", {})),
                },
                tags=doc.get("meta", {}).get("tags", []),
            )
            await self.storage.add(memory)
            ids.append(memory.id)
            
            # 批量提交
            if (i + 1) % batch_size == 0:
                await asyncio.sleep(0)  # 让出事件循环
        
        return ids
    
    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """查询文档
        
        Args:
            query: 查询文本
            filters: 过滤条件
            top_k: 返回数量
        
        Returns:
            文档列表
        """
        # 构建过滤条件
        search_filters = {}
        if filters:
            if "index" in filters:
                search_filters["index"] = filters["index"]
            if "meta" in filters:
                search_filters.update(filters["meta"])
        
        # 搜索
        memories = await self.storage.search(query, limit=top_k, filters=search_filters if search_filters else None)
        
        return [
            {
                "id": m.id,
                "content": m.content,
                "meta": m.metadata,
                "score": getattr(m, "score", None),
            }
            for m in memories
        ]
    
    async def get_document_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取文档"""
        memory = await self.storage.get(id)
        if memory:
            return {
                "id": memory.id,
                "content": memory.content,
                "meta": memory.metadata,
            }
        return None
    
    async def get_documents_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """根据 IDs 批量获取文档"""
        docs = []
        for id in ids:
            doc = await self.get_document_by_id(id)
            if doc:
                docs.append(doc)
        return docs
    
    async def delete_documents(
        self,
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """删除文档
        
        Args:
            ids: 文档 ID 列表
            filters: 过滤条件
        
        Returns:
            删除数量
        """
        if ids:
            count = 0
            for id in ids:
                if await self.storage.delete(id):
                    count += 1
            return count
        
        elif filters:
            # 根据过滤条件删除
            memories = await self.storage.list(limit=1000)
            count = 0
            for memory in memories:
                if self._matches_filters(memory, filters):
                    await self.storage.delete(memory.id)
                    count += 1
            return count
        
        return 0
    
    async def get_document_count(self) -> int:
        """获取文档数量"""
        return await self.storage.count()
    
    async def get_all_documents(
        self,
        index: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10000,
    ) -> List[Dict[str, Any]]:
        """获取所有文档"""
        memories = await self.storage.list(limit=limit)
        
        docs = []
        for memory in memories:
            if index and memory.metadata.get("index") != index:
                continue
            if filters and not self._matches_filters(memory, filters):
                continue
            
            docs.append({
                "id": memory.id,
                "content": memory.content,
                "meta": memory.metadata,
            })
        
        return docs
    
    def _matches_filters(self, memory: Memory, filters: Dict[str, Any]) -> bool:
        """检查记忆是否匹配过滤条件"""
        for key, value in filters.items():
            if key == "index":
                if memory.metadata.get("index") != value:
                    return False
            elif key in memory.metadata:
                if memory.metadata[key] != value:
                    return False
        return True
    
    async def update_document_meta(
        self,
        id: str,
        meta: Dict[str, Any],
    ) -> bool:
        """更新文档元数据"""
        memory = await self.storage.get(id)
        if not memory:
            return False
        
        # 合并元数据
        new_meta = {**memory.metadata, **meta}
        await self.storage.update(memory_id=id)
        return True
    
    def __repr__(self) -> str:
        return f"HaystackDocumentStore(backend='{self.backend}', index='{self.index}')"
