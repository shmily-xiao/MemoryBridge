"""
MemoryRefiner - 记忆提炼器

实现记忆生命周期管理：
- Context → Short-term → Long-term 自动升级
- 基于重要性评分
- 时间维度追踪
- 记忆合并去重
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ..core.memory import Memory, MemoryType, MemoryPriority
from ..core.service import MemoryService


@dataclass
class ImportanceScore:
    """记忆重要性评分"""
    reference_count: float = 0.0  # 引用次数 (0-1)
    user_instruction: float = 0.0  # 用户指令权重 (0-1)
    emotional_intensity: float = 0.0  # 情感强度 (0-1)
    recency: float = 0.0  # 时效性 (0-1)
    temporal_context: float = 0.0  # 时间上下文相关性 (0-1)
    
    def calculate(self, weights: Optional[Dict[str, float]] = None) -> float:
        """计算加权总分"""
        weights = weights or {
            "reference": 0.25,
            "instruction": 0.35,
            "emotional": 0.10,
            "recency": 0.15,
            "temporal": 0.15,
        }
        
        score = (
            self.reference_count * weights["reference"] +
            self.user_instruction * weights["instruction"] +
            self.emotional_intensity * weights["emotional"] +
            self.recency * weights["recency"] +
            self.temporal_context * weights["temporal"]
        )
        return min(1.0, max(0.0, score))  # 限制在 0-1 之间


class MemoryRefiner:
    """记忆提炼器
    
    负责记忆的生命周期管理：
    1. 评估记忆重要性
    2. 决定记忆升级 (Short → Long)
    3. 记忆合并去重
    4. 时间维度追踪
    """
    
    # 升级阈值
    PROMOTE_THRESHOLD = 0.7  # 重要性 > 0.7 升级为长期记忆
    DEMOTE_THRESHOLD = 0.3   # 重要性 < 0.3 降级或清理
    
    def __init__(
        self,
        short_term_storage: Optional[MemoryService] = None,
        long_term_storage: Optional[MemoryService] = None,
    ):
        """初始化记忆提炼器
        
        Args:
            short_term_storage: 短期记忆存储
            long_term_storage: 长期记忆存储
        """
        self.short_term_storage = short_term_storage
        self.long_term_storage = long_term_storage
    
    def calculate_importance(
        self,
        memory: Memory,
        reference_count: int = 0,
        user_instruction: bool = False,
        emotional_keywords: Optional[List[str]] = None,
    ) -> ImportanceScore:
        """计算记忆重要性评分
        
        Args:
            memory: 记忆对象
            reference_count: 被引用次数
            user_instruction: 是否用户明确指令记住
            emotional_keywords: 情感关键词列表
        
        Returns:
            ImportanceScore 对象
        """
        # 1. 引用次数评分 (对数增长)
        ref_score = min(1.0, reference_count * 0.2)
        
        # 2. 用户指令评分
        instruction_score = 1.0 if user_instruction else 0.0
        
        # 3. 情感强度评分
        emotional_score = 0.0
        if emotional_keywords:
            content_lower = memory.content.lower()
            matches = sum(1 for kw in emotional_keywords if kw.lower() in content_lower)
            emotional_score = min(1.0, matches * 0.3)
        
        # 4. 时效性评分 (新记忆优先)
        now = datetime.now(timezone.utc)
        created = memory.created_at
        if isinstance(created, datetime):
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            days_old = (now - created).days
            recency_score = max(0.0, 1.0 - (days_old * 0.05))  # 20 天后降为 0
        else:
            recency_score = 0.5
        
        # 5. 时间上下文相关性
        temporal_score = self._calculate_temporal_relevance(memory)
        
        return ImportanceScore(
            reference_count=ref_score,
            user_instruction=instruction_score,
            emotional_intensity=emotional_score,
            recency=recency_score,
            temporal_context=temporal_score,
        )
    
    def _calculate_temporal_relevance(self, memory: Memory) -> float:
        """计算时间上下文相关性
        
        检测记忆内容中的时间相关词汇
        """
        temporal_keywords = [
            "今天", "明天", "昨天", "现在", "最近", "目前",
            "今年", "明年", "去年", "当前", "将来", "过去",
            "today", "tomorrow", "yesterday", "now", "recently",
        ]
        
        content_lower = memory.content.lower()
        matches = sum(1 for kw in temporal_keywords if kw in content_lower)
        
        # 有时间关键词，相关性更高
        if matches > 0:
            return min(1.0, matches * 0.3)
        
        # 检查元数据中的时间上下文
        if memory.metadata.get("temporal_context"):
            return 0.8
        
        return 0.3  # 默认中等相关性
    
    async def promote_to_long_term(
        self,
        memory_id: str,
        importance_score: Optional[float] = None,
    ) -> Optional[Memory]:
        """将记忆升级为长期记忆
        
        Args:
            memory_id: 记忆 ID
            importance_score: 重要性评分（不提供则自动计算）
        
        Returns:
            升级后的记忆，失败返回 None
        """
        if not self.short_term_storage or not self.long_term_storage:
            raise ValueError("Storage not configured")
        
        # 获取短期记忆
        memory = await self.short_term_storage.get(memory_id)
        if not memory:
            return None
        
        # 计算重要性评分
        if importance_score is None:
            score = self.calculate_importance(memory)
            importance_score = score.calculate()
        
        # 检查是否达到升级阈值
        if importance_score < self.PROMOTE_THRESHOLD:
            return None
        
        # 添加到长期存储
        promoted = await self.long_term_storage.add(
            content=memory.content,
            memory_type=MemoryType.LONG_TERM,
            priority=memory.priority,
            tags=memory.tags,
            metadata={
                **memory.metadata,
                "promoted_from_short": True,
                "importance_score": importance_score,
                "promoted_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        # 从短期存储删除
        await self.short_term_storage.delete(memory_id)
        
        return promoted
    
    async def demote_to_short_term(
        self,
        memory_id: str,
    ) -> Optional[Memory]:
        """将记忆降级为短期记忆
        
        Args:
            memory_id: 记忆 ID
        
        Returns:
            降级后的记忆，失败返回 None
        """
        if not self.short_term_storage or not self.long_term_storage:
            raise ValueError("Storage not configured")
        
        # 获取长期记忆
        memory = await self.long_term_storage.get(memory_id)
        if not memory:
            return None
        
        # 添加到短期存储
        demoted = await self.short_term_storage.add(
            content=memory.content,
            memory_type=MemoryType.SESSION,
            priority=memory.priority,
            tags=memory.tags,
            metadata={
                **memory.metadata,
                "demoted_from_long": True,
                "demoted_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        # 从长期存储删除
        await self.long_term_storage.delete(memory_id)
        
        return demoted
    
    async def merge_similar_memories(
        self,
        memory_ids: List[str],
        storage: MemoryService,
    ) -> Optional[Memory]:
        """合并相似记忆
        
        Args:
            memory_ids: 要合并的记忆 ID 列表
            storage: 存储实例
        
        Returns:
            合并后的记忆
        """
        if len(memory_ids) < 2:
            return None
        
        # 获取所有记忆
        memories = []
        for mid in memory_ids:
            memory = await storage.get(mid)
            if memory:
                memories.append(memory)
        
        if len(memories) < 2:
            return None
        
        # 合并内容（简单拼接，可以改进为 AI 摘要）
        merged_content = " | ".join([m.content for m in memories])
        merged_tags = list(set(tag for m in memories for tag in m.tags))
        
        # 创建合并后的记忆
        merged = await storage.add(
            content=merged_content,
            memory_type=memories[0].memory_type,
            priority=max(m.priority for m in memories),
            tags=merged_tags,
            metadata={
                "merged_from": memory_ids,
                "merged_at": datetime.now(timezone.utc).isoformat(),
                "merged_count": len(memories),
            }
        )
        
        # 删除原始记忆
        for mid in memory_ids:
            await storage.delete(mid)
        
        return merged
    
    async def cleanup_old_memories(
        self,
        storage: MemoryService,
        max_age_days: int = 30,
        memory_type: Optional[MemoryType] = None,
    ) -> int:
        """清理过期记忆
        
        Args:
            storage: 存储实例
            max_age_days: 最大保留天数
            memory_type: 记忆类型过滤
        
        Returns:
            清理的记忆数量
        """
        # 获取所有记忆
        memories = await storage.list(limit=1000, memory_type=memory_type)
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        cleaned = 0
        
        for memory in memories:
            created = memory.created_at
            if isinstance(created, datetime):
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                if created < cutoff_date:
                    # 检查是否是重要记忆（P0/P1 保留）
                    if memory.priority not in (MemoryPriority.P0, MemoryPriority.P1):
                        await storage.delete(memory.id)
                        cleaned += 1
        
        return cleaned
    
    def __repr__(self) -> str:
        return f"MemoryRefiner(promote_threshold={self.PROMOTE_THRESHOLD})"
