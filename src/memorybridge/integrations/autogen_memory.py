"""
AutoGen Memory 集成

Microsoft AutoGen 是多 Agent 对话框架，此集成提供：
- Agent 间共享记忆
- 对话历史持久化
- 跨会话上下文管理
- 群聊记忆管理

Requires:
    pip install pyautogen
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from ..core.memory import Memory, MemoryType, MemoryPriority
from ..storage.factory import create_storage


class AutoGenMemory:
    """AutoGen 记忆集成"""
    
    def __init__(
        self,
        conversation_id: Optional[str] = None,
        agent_name: str = "assistant",
        backend: str = "sqlite",
        db_path: Optional[str] = None,
        max_history: int = 100,
        auto_save: bool = True,
    ):
        self.conversation_id = conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.agent_name = agent_name
        self.backend = backend
        self.max_history = max_history
        self.auto_save = auto_save
        
        config = {"db_path": db_path} if db_path and backend == "sqlite" else {}
        self.storage = create_storage(backend, config)
        self._message_cache: List[Dict] = []
        self._attached_agent = None
    
    async def save_message(
        self,
        sender: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict] = None,
    ) -> Memory:
        """保存对话消息"""
        memory_metadata = {
            "source": "autogen",
            "conversation_id": self.conversation_id,
            "agent_name": self.agent_name,
            "sender": sender,
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }
        
        memory = await self.storage.add(
            content=content,
            memory_type=MemoryType.SESSION,
            priority=MemoryPriority.P2,
            tags=["autogen", "conversation", role],
            metadata=memory_metadata,
        )
        
        self._message_cache.append({
            "sender": sender,
            "content": content,
            "role": role,
            "timestamp": memory.created_at.isoformat(),
        })
        
        if len(self._message_cache) > self.max_history:
            self._message_cache = self._message_cache[-self.max_history:]
        
        return memory
    
    async def get_context(
        self,
        query: Optional[str] = None,
        limit: int = 10,
        include_summary: bool = True,
    ) -> Dict[str, Any]:
        """获取对话上下文"""
        context = {
            "conversation_id": self.conversation_id,
            "agent_name": self.agent_name,
            "messages": [],
            "summary": None,
        }
        
        if query:
            memories = await self.storage.search(query, limit=limit)
            context["messages"] = [
                {
                    "sender": m.metadata.get("sender", "unknown"),
                    "content": m.content,
                    "role": m.metadata.get("role", "user"),
                    "timestamp": m.created_at.isoformat(),
                }
                for m in memories
            ]
        else:
            memories = await self.storage.list(limit=limit)
            context["messages"] = [
                {
                    "sender": m.metadata.get("sender", "unknown"),
                    "content": m.content,
                    "role": m.metadata.get("role", "user"),
                    "timestamp": m.created_at.isoformat(),
                }
                for m in memories
            ]
        
        if include_summary and context["messages"]:
            context["summary"] = await self._generate_summary(context["messages"])
        
        return context
    
    async def _generate_summary(self, messages: List[Dict]) -> str:
        """生成对话摘要"""
        recent = messages[-5:] if len(messages) > 5 else messages
        summary_parts = []
        for msg in recent:
            summary_parts.append(f"{msg['sender']}: {msg['content'][:50]}")
        return " | ".join(summary_parts)
    
    async def get_conversation_history(
        self,
        limit: int = 50,
    ) -> List[Dict]:
        """获取完整对话历史"""
        memories = await self.storage.list(limit=limit)
        # 按创建时间排序（最新的在前）
        sorted_memories = sorted(memories, key=lambda m: m.created_at, reverse=True)
        return [
            {
                "sender": m.metadata.get("sender", "unknown"),
                "content": m.content,
                "role": m.metadata.get("role", "user"),
                "timestamp": m.created_at.isoformat(),
            }
            for m in sorted_memories
        ]
    
    async def clear_history(self) -> int:
        """清空对话历史"""
        memories = await self.storage.list(limit=1000)
        count = 0
        for memory in memories:
            if memory.metadata.get("conversation_id") == self.conversation_id:
                await self.storage.delete(memory.id)
                count += 1
        self._message_cache = []
        return count
    
    def attach_to_agent(self, agent) -> None:
        """附加到 AutoGen Agent"""
        self._attached_agent = agent
        if hasattr(agent, "register_reply"):
            agent.register_reply(self._autogen_reply_hook)
    
    def _autogen_reply_hook(self, recipient, messages, sender, config):
        """AutoGen 回复钩子"""
        if self.auto_save and messages:
            last_message = messages[-1]
            asyncio.create_task(
                self.save_message(
                    sender=sender.name if hasattr(sender, "name") else "unknown",
                    content=last_message.get("content", ""),
                    role="assistant",
                )
            )
        return False, None
    
    async def share_memory_with_agent(
        self,
        target_agent_name: str,
        memory_query: str,
        limit: int = 5,
    ) -> List[Dict]:
        """与其他 Agent 共享记忆"""
        memories = await self.storage.search(memory_query, limit=limit)
        for memory in memories:
            memory.metadata["shared_with"] = target_agent_name
            memory.metadata["shared_at"] = datetime.now(timezone.utc).isoformat()
            await self.storage.update(memory_id=memory.id, metadata=memory.metadata)
        return [m.to_dict() for m in memories]
    
    async def get_shared_memories(
        self,
        from_agent_name: Optional[str] = None,
    ) -> List[Dict]:
        """获取其他 Agent 共享的记忆"""
        memories = await self.storage.list(limit=100)
        shared = []
        for memory in memories:
            if memory.metadata.get("shared_with") == self.agent_name:
                if from_agent_name is None or memory.metadata.get("agent_name") == from_agent_name:
                    shared.append(memory.to_dict())
        return shared
    
    async def export_conversation(
        self,
        format: str = "json",
        output_path: Optional[str] = None,
    ) -> str:
        """导出对话"""
        history = await self.get_conversation_history(limit=1000)
        
        if format == "json":
            data = json.dumps(history, indent=2, ensure_ascii=False, default=str)
        elif format == "markdown":
            data = self._to_markdown(history)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(data)
        
        return data
    
    def _to_markdown(self, messages: List[Dict]) -> str:
        """转换为 Markdown 格式"""
        lines = [
            f"# Conversation: {self.conversation_id}",
            f"**Agent**: {self.agent_name}\n",
        ]
        for msg in messages:
            lines.append(f"**{msg['sender']}** ({msg['role']}): {msg['content']}\n")
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"AutoGenMemory(conversation='{self.conversation_id}', agent='{self.agent_name}')"
