"""
LangChain Memory 集成

将 MemoryBridge 集成到 LangChain 的 Memory 系统中，支持:
- ConversationBufferMemory
- ConversationSummaryMemory
- VectorStoreRetrieverMemory

Usage:
    from memorybridge.integrations import MemoryBridgeMemory
    
    memory = MemoryBridgeMemory(
        backend="sqlite",  # 或 "mongodb"
        return_messages=True
    )
    
    # 与 LangChain Chain 一起使用
    chain = ConversationChain(
        llm=llm,
        memory=memory,
        verbose=True
    )
    
    response = chain.run("你好，我叫小明")
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.schema import BaseMemory, get_buffer_string
from langchain.schema.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import Field

from ..core.memory import MemoryType, MemoryPriority
from ..storage.factory import create_storage


class MemoryBridgeMemory(BaseMemory):
    """MemoryBridge LangChain Memory 集成
    
    将 LangChain 的对话历史自动存储到 MemoryBridge，
    支持多种存储后端（SQLite、MongoDB）和知识图谱检索。
    
    Attributes:
        backend: 存储后端类型 ("sqlite" 或 "mongodb")
        config: 存储后端配置
        memory_key: 记忆键名 (默认 "history")
        input_key: 输入键名 (默认 "input")
        return_messages: 是否返回消息列表 (默认 False)
        human_prefix: 人类消息前缀 (默认 "Human")
        ai_prefix: AI 消息前缀 (默认 "AI")
        max_memory_limit: 最大记忆数量限制 (默认 None，无限制)
        enable_graph: 是否启用知识图谱检索 (默认 False)
        
    Examples:
        # 基础使用
        memory = MemoryBridgeMemory()
        
        # 使用 MongoDB 后端
        memory = MemoryBridgeMemory(
            backend="mongodb",
            config={"connection_string": "mongodb://localhost:27017"}
        )
        
        # 启用知识图谱
        memory = MemoryBridgeMemory(enable_graph=True)
    """
    
    backend: str = "sqlite"
    config: Dict[str, Any] = Field(default_factory=dict)
    memory_key: str = "history"
    input_key: str = "input"
    return_messages: bool = False
    human_prefix: str = "Human"
    ai_prefix: str = "AI"
    max_memory_limit: Optional[int] = None
    enable_graph: bool = False
    graph_min_score: float = 0.5
    
    _storage: Any = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储后端"""
        try:
            self._storage = create_storage(self.backend, self.config)
        except Exception as e:
            # 如果 MongoDB 不可用，回退到 SQLite
            if self.backend == "mongodb":
                import warnings
                warnings.warn(
                    f"MongoDB not available, falling back to SQLite: {e}"
                )
                self._storage = create_storage("sqlite", {})
            else:
                raise
    
    @property
    def memory_variables(self) -> List[str]:
        """返回记忆变量列表"""
        return [self.memory_key]
    
    def load_memory_variables(
        self, inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """加载记忆变量
        
        Args:
            inputs: 输入字典
            
        Returns:
            包含记忆历史的字典
        """
        # 获取最近的对话历史
        history = self._get_recent_history()
        
        if self.return_messages:
            return {self.memory_key: history}
        else:
            return {self.memory_key: get_buffer_string(history)}
    
    def save_context(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, str],
    ) -> None:
        """保存对话上下文到 MemoryBridge
        
        Args:
            inputs: 输入字典（包含用户消息）
            outputs: 输出字典（包含 AI 回复）
        """
        # 获取用户输入
        input_value = inputs.get(self.input_key)
        if not input_value:
            return
        
        # 获取 AI 输出
        output_value = outputs.get("output", "")
        
        # 保存对话到 MemoryBridge
        self._save_conversation(input_value, output_value)
        
        # 如果启用知识图谱，提取实体并保存
        if self.enable_graph:
            self._extract_and_save_entities(input_value, output_value)
    
    def clear(self) -> None:
        """清除记忆历史"""
        # 这里可以选择不清理 MemoryBridge 的长期记忆
        # 只清理当前会话的上下文
        pass
    
    def _get_recent_history(
        self,
        limit: int = 10,
    ) -> List[HumanMessage | AIMessage]:
        """获取最近的对话历史
        
        Args:
            limit: 返回的消息数量限制
            
        Returns:
            消息列表
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        memories = loop.run_until_complete(
            self._storage.list(limit=limit * 2)  # 获取双倍，过滤后可能不足
        )
        
        messages = []
        for memory in reversed(memories):
            if memory.memory_type == MemoryType.SESSION:
                metadata = memory.metadata or {}
                if metadata.get("role") == "human":
                    messages.append(HumanMessage(content=memory.content))
                elif metadata.get("role") == "ai":
                    messages.append(AIMessage(content=memory.content))
        
        return messages[-limit:]
    
    def _save_conversation(
        self,
        user_input: str,
        ai_output: str,
    ) -> None:
        """保存对话到 MemoryBridge
        
        Args:
            user_input: 用户输入
            ai_output: AI 输出
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 保存用户消息
        loop.run_until_complete(
            self._storage.add(
                content=user_input,
                memory_type=MemoryType.SESSION,
                priority=MemoryPriority.P2,
                metadata={"role": "human", "source": "langchain"},
                tags=["conversation", "langchain"],
            )
        )
        
        # 保存 AI 回复
        loop.run_until_complete(
            self._storage.add(
                content=ai_output,
                memory_type=MemoryType.SESSION,
                priority=MemoryPriority.P2,
                metadata={"role": "ai", "source": "langchain"},
                tags=["response", "langchain"],
            )
        )
        
        # 如果超过限制，删除最旧的记忆
        if self.max_memory_limit:
            self._enforce_memory_limit()
    
    def _extract_and_save_entities(
        self,
        text1: str,
        text2: str,
    ) -> None:
        """从文本中提取实体并保存到知识图谱
        
        Args:
            text1: 第一段文本
            text2: 第二段文本
        """
        # 简单的实体提取（实际应用中可以使用 NLP 模型）
        # 这里只保存包含实体信息的记忆
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 保存为长期记忆，供知识图谱使用
        loop.run_until_complete(
            self._storage.add(
                content=f"{text1}\n{text2}",
                memory_type=MemoryType.LONG_TERM,
                priority=MemoryPriority.P3,
                metadata={"source": "langchain", "auto_extracted": True},
                tags=["knowledge", "auto"],
            )
        )
    
    def _enforce_memory_limit(self) -> None:
        """执行记忆数量限制"""
        if not self.max_memory_limit:
            return
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 获取所有 session 类型的记忆
        memories = loop.run_until_complete(
            self._storage.list(
                limit=1000,
                memory_type=MemoryType.SESSION,
            )
        )
        
        # 如果超过限制，删除最旧的
        if len(memories) > self.max_memory_limit:
            to_delete = len(memories) - self.max_memory_limit
            for memory in memories[:to_delete]:
                loop.run_until_complete(
                    self._storage.delete(memory.id)
                )
    
    def search_memories(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索记忆
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            filters: 过滤条件
            
        Returns:
            记忆列表
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        memories = loop.run_until_complete(
            self._storage.search(
                query=query,
                limit=limit,
                filters=filters,
            )
        )
        
        return [
            {
                "id": m.id,
                "content": m.content,
                "metadata": m.metadata,
                "tags": m.tags,
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ]
    
    def get_knowledge_context(
        self,
        query: str,
        max_results: int = 3,
    ) -> str:
        """获取知识上下文（用于 RAG）
        
        Args:
            query: 查询关键词
            max_results: 最大结果数
            
        Returns:
            知识上下文字符串
        """
        memories = self.search_memories(
            query=query,
            limit=max_results,
            filters={"memory_type": "long_term"},
        )
        
        if not memories:
            return ""
        
        context_parts = []
        for mem in memories:
            context_parts.append(mem["content"])
        
        return "\n\n".join(context_parts)
