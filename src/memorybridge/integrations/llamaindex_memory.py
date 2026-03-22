"""
LlamaIndex Memory 集成

LlamaIndex 是 RAG 应用框架，此集成提供：
- VectorStore 集成
- Chat Memory 持久化
- 对话历史检索
- 上下文增强

Requires:
    pip install llama-index
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.memory import Memory, MemoryType, MemoryPriority
from ..storage.factory import create_storage


class LlamaIndexMemory:
    """LlamaIndex 记忆集成
    
    功能：
    - 持久化 Chat Memory
    - 向量存储检索
    - 对话历史管理
    - RAG 上下文增强
    
    使用示例：
    ```python
    from memorybridge.integrations import LlamaIndexMemory
    from llama_index.core import VectorStoreIndex, Document
    
    # 创建记忆实例
    memory = LlamaIndexMemory(
        session_id="chat_001",
        backend="sqlite",
    )
    
    # 保存对话
    await memory.add_message("user", "什么是机器学习？")
    await memory.add_message("assistant", "机器学习是...")
    
    # 获取对话历史
    history = await memory.get_chat_history()
    
    # 检索相关记忆
    context = await memory.retrieve_context("机器学习", top_k=3)
    ```
    """
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        backend: str = "sqlite",
        db_path: Optional[str] = None,
        max_messages: int = 100,
        auto_persist: bool = True,
    ):
        """初始化 LlamaIndex 记忆
        
        Args:
            session_id: 会话 ID
            backend: 存储后端
            db_path: 数据库路径
            max_messages: 最大消息数
            auto_persist: 是否自动持久化
        """
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backend = backend
        self.max_messages = max_messages
        self.auto_persist = auto_persist
        
        config = {"db_path": db_path} if db_path and backend == "sqlite" else {}
        self.storage = create_storage(backend, config)
        
        # 消息缓存
        self._messages: List[Dict] = []
    
    async def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Memory:
        """添加对话消息
        
        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 额外元数据
        
        Returns:
            保存的 Memory 对象
        """
        memory_metadata = {
            "source": "llamaindex",
            "session_id": self.session_id,
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }
        
        memory = await self.storage.add(
            content=content,
            memory_type=MemoryType.SESSION,
            priority=MemoryPriority.P2,
            tags=["llamaindex", "chat", role],
            metadata=memory_metadata,
        )
        
        # 更新缓存
        self._messages.append({
            "role": role,
            "content": content,
            "timestamp": memory.created_at,
        })
        
        # 清理过期缓存
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]
        
        return memory
    
    async def get_chat_history(
        self,
        limit: int = 20,
        as_llama_format: bool = True,
    ) -> List[Dict]:
        """获取对话历史
        
        Args:
            limit: 返回数量
            as_llama_format: 是否返回 LlamaIndex 格式
        
        Returns:
            消息列表
        """
        memories = await self.storage.list(limit=limit)
        
        # 按时间排序
        sorted_memories = sorted(memories, key=lambda m: m.created_at)
        
        if as_llama_format:
            # LlamaIndex ChatMessage 格式
            return [
                {
                    "role": m.metadata.get("role", "user"),
                    "content": m.content,
                }
                for m in sorted_memories
            ]
        else:
            return [
                {
                    "role": m.metadata.get("role", "user"),
                    "content": m.content,
                    "timestamp": m.created_at,
                }
                for m in sorted_memories
            ]
    
    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        include_history: bool = True,
    ) -> Dict[str, Any]:
        """检索相关上下文（RAG）
        
        Args:
            query: 查询关键词
            top_k: 返回数量
            include_history: 是否包含对话历史
        
        Returns:
            上下文字典
        """
        context = {
            "query": query,
            "relevant_memories": [],
            "chat_history": [],
        }
        
        # 搜索相关记忆
        memories = await self.storage.search(query, limit=top_k)
        context["relevant_memories"] = [
            {
                "content": m.content,
                "role": m.metadata.get("role", "user"),
                "score": getattr(m, "score", None),
            }
            for m in memories
        ]
        
        # 获取对话历史
        if include_history:
            context["chat_history"] = await self.get_chat_history(limit=10)
        
        return context
    
    async def clear_session(self) -> int:
        """清空当前会话"""
        memories = await self.storage.list(limit=1000)
        count = 0
        for memory in memories:
            if memory.metadata.get("session_id") == self.session_id:
                await self.storage.delete(memory.id)
                count += 1
        self._messages = []
        return count
    
    def to_llama_index_chat_memory(self):
        """转换为 LlamaIndex ChatMemoryBuffer"""
        try:
            from llama_index.core.memory import ChatMemoryBuffer
            from llama_index.core.schema import ChatMessage
            
            # 获取历史
            history = asyncio.run(self.get_chat_history(as_llama_format=True))
            
            # 创建 ChatMessage 列表
            messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in history
            ]
            
            # 创建 ChatMemoryBuffer
            return ChatMemoryBuffer.from_defaults(chat_history=messages)
        
        except ImportError:
            raise ImportError("llama-index not installed. Install with: pip install llama-index")
    
    async def export_session(
        self,
        format: str = "json",
    ) -> str:
        """导出会话"""
        import json
        
        history = await self.get_chat_history(as_llama_format=False)
        
        if format == "json":
            return json.dumps(history, indent=2, ensure_ascii=False, default=str)
        elif format == "markdown":
            lines = [f"# Session: {self.session_id}\n"]
            for msg in history:
                lines.append(f"**{msg['role']}**: {msg['content']}\n")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def __repr__(self) -> str:
        return f"LlamaIndexMemory(session='{self.session_id}', messages={len(self._messages)})"


class LlamaIndexVectorStore:
    """LlamaIndex VectorStore 集成
    
    将 MemoryBridge 向量存储集成到 LlamaIndex
    """
    
    def __init__(self, vector_store=None):
        """初始化
        
        Args:
            vector_store: VectorStore 实例（可选）
        """
        self.vector_store = vector_store
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """添加文档
        
        Args:
            documents: 文档列表 [{"text": "...", "metadata": {...}}]
        
        Returns:
            文档 ID 列表
        """
        if not self.vector_store:
            raise ValueError("VectorStore not configured")
        
        ids = []
        for doc in documents:
            memory = Memory(
                content=doc["text"],
                memory_type=MemoryType.LONG_TERM,
                metadata=doc.get("metadata", {}),
            )
            await self.vector_store.add(memory)
            ids.append(memory.id)
        
        return ids
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """查询文档
        
        Args:
            query: 查询文本
            top_k: 返回数量
        
        Returns:
            相关文档列表
        """
        if not self.vector_store:
            raise ValueError("VectorStore not configured")
        
        memories = await self.vector_store.search(query, limit=top_k)
        
        return [
            {
                "text": m.content,
                "metadata": m.metadata,
                "score": getattr(m, "score", None),
            }
            for m in memories
        ]
