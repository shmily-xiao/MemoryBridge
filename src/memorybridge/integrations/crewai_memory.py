"""
CrewAI Memory 集成

将 MemoryBridge 集成到 CrewAI 的 Memory 系统中，支持:
- 长期记忆存储
- 跨 Agent 记忆共享
- 任务上下文记忆

Usage:
    from memorybridge.integrations import CrewAIMemory
    
    memory = CrewAIMemory(
        backend="sqlite",
        crew_id="my_crew"
    )
    
    # 与 CrewAI Agent 一起使用
    agent = Agent(
        role='研究员',
        goal='研究主题',
        memory=memory,
        verbose=True
    )
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.memory import MemoryType, MemoryPriority
from ..storage.factory import create_storage


class CrewAIMemory:
    """CrewAI Memory 集成
    
    为 CrewAI Agent 提供长期记忆能力，支持：
    - 任务记忆存储
    - 跨 Agent 记忆共享
    - 上下文检索
    
    Attributes:
        backend: 存储后端类型 ("sqlite" 或 "mongodb")
        config: 存储后端配置
        crew_id: Crew 标识符
        agent_id: Agent 标识符
        enable_shared_memory: 是否启用共享记忆 (默认 True)
        
    Examples:
        # 基础使用
        memory = CrewAIMemory(crew_id="research_crew")
        
        # 多 Agent 共享记忆
        memory = CrewAIMemory(
            crew_id="research_crew",
            enable_shared_memory=True
        )
    """
    
    def __init__(
        self,
        backend: str = "sqlite",
        config: Optional[Dict[str, Any]] = None,
        crew_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        enable_shared_memory: bool = True,
    ):
        """初始化 CrewAI Memory
        
        Args:
            backend: 存储后端类型
            config: 存储后端配置
            crew_id: Crew 标识符
            agent_id: Agent 标识符
            enable_shared_memory: 是否启用共享记忆
        """
        self.backend = backend
        self.config = config or {}
        self.crew_id = crew_id
        self.agent_id = agent_id
        self.enable_shared_memory = enable_shared_memory
        
        self._storage = create_storage(backend, config)
    
    def save(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        priority: MemoryPriority = MemoryPriority.P2,
    ) -> str:
        """保存记忆
        
        Args:
            content: 记忆内容
            metadata: 元数据
            memory_type: 记忆类型
            priority: 优先级
            
        Returns:
            记忆 ID
        """
        # 添加 Crew/Agent 标识到元数据
        full_metadata = metadata.copy() if metadata else {}
        if self.crew_id:
            full_metadata["crew_id"] = self.crew_id
        if self.agent_id:
            full_metadata["agent_id"] = self.agent_id
        full_metadata["source"] = "crewai"
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        memory = loop.run_until_complete(
            self._storage.add(
                content=content,
                metadata=full_metadata,
                memory_type=memory_type,
                priority=priority,
                tags=["crewai", self.crew_id or "default"],
            )
        )
        
        return memory.id
    
    def search(
        self,
        query: str,
        limit: int = 5,
        agent_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """搜索记忆
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            agent_only: 是否只搜索当前 Agent 的记忆
            
        Returns:
            记忆列表
        """
        filters = {}
        if agent_only and self.agent_id:
            # 注意：需要 storage 支持 metadata 过滤
            pass
        
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
    
    def get_context(
        self,
        query: str,
        max_results: int = 3,
        include_crew_memory: bool = True,
    ) -> str:
        """获取上下文（用于 Agent 决策）
        
        Args:
            query: 查询关键词
            max_results: 最大结果数
            include_crew_memory: 是否包含 Crew 共享记忆
            
        Returns:
            上下文字符串
        """
        filters = {}
        if not include_crew_memory:
            filters["crew_id"] = self.crew_id
        
        memories = self.search(
            query=query,
            limit=max_results,
        )
        
        if not memories:
            return ""
        
        context_parts = []
        for mem in memories:
            context_parts.append(mem["content"])
        
        return "\n\n".join(context_parts)
    
    def save_task_result(
        self,
        task_description: str,
        result: str,
        agent_role: Optional[str] = None,
    ) -> str:
        """保存任务结果
        
        Args:
            task_description: 任务描述
            result: 任务结果
            agent_role: Agent 角色
            
        Returns:
            记忆 ID
        """
        content = f"Task: {task_description}\nResult: {result}"
        
        metadata = {
            "type": "task_result",
            "task_description": task_description,
        }
        if agent_role:
            metadata["agent_role"] = agent_role
        
        return self.save(
            content=content,
            metadata=metadata,
            memory_type=MemoryType.LONG_TERM,
            priority=MemoryPriority.P2,
        )
    
    def save_agent_interaction(
        self,
        agent_role: str,
        action: str,
        observation: str,
    ) -> str:
        """保存 Agent 交互
        
        Args:
            agent_role: Agent 角色
            action: 执行的动作
            observation: 观察结果
            
        Returns:
            记忆 ID
        """
        content = f"Agent: {agent_role}\nAction: {action}\nObservation: {observation}"
        
        metadata = {
            "type": "interaction",
            "agent_role": agent_role,
            "action": action,
        }
        
        return self.save(
            content=content,
            metadata=metadata,
            memory_type=MemoryType.SESSION,
            priority=MemoryPriority.P3,
        )
    
    def get_crew_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取 Crew 历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            历史记录列表
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 搜索当前 Crew 的记忆
        memories = loop.run_until_complete(
            self._storage.search(
                query="",
                limit=limit,
                filters={},
            )
        )
        
        # 过滤出当前 Crew 的记忆
        crew_memories = [
            {
                "id": m.id,
                "content": m.content,
                "metadata": m.metadata,
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
            if m.metadata and m.metadata.get("crew_id") == self.crew_id
        ]
        
        return crew_memories[:limit]
    
    def clear_agent_memory(self) -> int:
        """清除 Agent 记忆
        
        Returns:
            删除的记忆数量
        """
        if not self.agent_id:
            return 0
        
        # 注意：需要 storage 支持批量删除
        # 这里简化实现
        return 0


# CrewAI 兼容的 Memory 类（如果 CrewAI 有标准接口）
class CrewAIMemoryAdapter(CrewAIMemory):
    """CrewAI Memory 适配器
    
    提供与 CrewAI 标准 Memory 接口兼容的适配层
    """
    
    def add_memory(self, context: str) -> str:
        """添加记忆（CrewAI 兼容接口）
        
        Args:
            context: 上下文内容
            
        Returns:
            记忆 ID
        """
        return self.save(
            content=context,
            metadata={"type": "context"},
        )
    
    def fetch_context_for_agent(
        self,
        goal: str,
        role: str,
    ) -> str:
        """获取 Agent 上下文（CrewAI 兼容接口）
        
        Args:
            goal: Agent 目标
            role: Agent 角色
            
        Returns:
            上下文字符串
        """
        return self.get_context(query=f"{role} {goal}")
