"""
MemoryManager - 记忆管理器

统筹管理记忆生命周期和知识图谱维护
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from ..core.memory import Memory, MemoryType, MemoryPriority
from ..core.service import MemoryService
from .refiner import MemoryRefiner
from .graph_extractor import KnowledgeGraphExtractor


class MemoryManager:
    """记忆管理器
    
    统筹管理：
    - 记忆生命周期（Context → Short → Long）
    - 知识图谱自动维护
    - 定期清理和整理
    - 时间维度追踪
    """
    
    def __init__(
        self,
        short_term_storage: Optional[MemoryService] = None,
        long_term_storage: Optional[MemoryService] = None,
        refiner: Optional[MemoryRefiner] = None,
        graph_extractor: Optional[KnowledgeGraphExtractor] = None,
    ):
        """初始化记忆管理器
        
        Args:
            short_term_storage: 短期记忆存储
            long_term_storage: 长期记忆存储
            refiner: 记忆提炼器
            graph_extractor: 图谱提取器
        """
        self.short_term_storage = short_term_storage
        self.long_term_storage = long_term_storage
        self.refiner = refiner or MemoryRefiner(short_term_storage, long_term_storage)
        self.graph_extractor = graph_extractor or KnowledgeGraphExtractor()
        
        # 自动处理配置
        self.auto_promote_enabled = True
        self.auto_cleanup_enabled = True
        self.cleanup_interval_days = 7
    
    async def process_new_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SESSION,
        user_instruction: bool = False,
    ) -> Dict:
        """处理新记忆
        
        流程：
        1. 添加到短期记忆
        2. 提取知识图谱
        3. 评估重要性
        4. 决定是否升级
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            user_instruction: 是否用户明确指令记住
        
        Returns:
            处理结果
        """
        result = {
            "memory_added": False,
            "entities_extracted": 0,
            "relations_extracted": 0,
            "promoted_to_long": False,
            "importance_score": 0.0,
        }
        
        # 1. 添加到短期记忆
        if self.short_term_storage:
            memory = await self.short_term_storage.add(
                content=content,
                memory_type=memory_type,
                metadata={
                    "user_instruction": user_instruction,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            result["memory_added"] = True
            result["memory_id"] = memory.id
            
            # 2. 提取知识图谱
            entities, relations = await self.graph_extractor.extract_from_memory(content)
            result["entities_extracted"] = len(entities)
            result["relations_extracted"] = len(relations)
            
            # 3. 评估重要性
            importance = self.refiner.calculate_importance(
                memory,
                reference_count=0,
                user_instruction=user_instruction,
            )
            score = importance.calculate()
            result["importance_score"] = score
            
            # 4. 决定是否升级
            if self.auto_promote_enabled and score >= self.refiner.PROMOTE_THRESHOLD:
                promoted = await self.refiner.promote_to_long_term(memory.id, score)
                if promoted:
                    result["promoted_to_long"] = True
                    result["promoted_memory_id"] = promoted.id
        
        return result
    
    async def cleanup_and_organize(self) -> Dict:
        """执行清理和整理任务
        
        Returns:
            清理结果统计
        """
        result = {
            "short_term_cleaned": 0,
            "long_term_cleaned": 0,
            "memories_merged": 0,
            "relations_updated": 0,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # 1. 清理过期短期记忆（7 天）
        if self.short_term_storage and self.auto_cleanup_enabled:
            result["short_term_cleaned"] = await self.refiner.cleanup_old_memories(
                self.short_term_storage,
                max_age_days=7,
                memory_type=MemoryType.SESSION,
            )
        
        # 2. 清理过期长期记忆（90 天，保留重要记忆）
        if self.long_term_storage and self.auto_cleanup_enabled:
            result["long_term_cleaned"] = await self.refiner.cleanup_old_memories(
                self.long_term_storage,
                max_age_days=90,
                memory_type=MemoryType.LONG_TERM,
            )
        
        # 3. 更新关系置信度
        result["relations_updated"] = len(self.graph_extractor.update_relation_confidence())
        
        return result
    
    async def get_memory_status(self) -> Dict:
        """获取记忆状态报告
        
        Returns:
            状态报告
        """
        short_count = await self.short_term_storage.count() if self.short_term_storage else 0
        long_count = await self.long_term_storage.count() if self.long_term_storage else 0
        
        freshness_report = self.graph_extractor.get_knowledge_freshness_report()
        
        return {
            "short_term_count": short_count,
            "long_term_count": long_count,
            "total_count": short_count + long_count,
            "knowledge_freshness": freshness_report,
            "auto_promote_enabled": self.auto_promote_enabled,
            "auto_cleanup_enabled": self.auto_cleanup_enabled,
            "last_cleanup": None,  # 从配置读取
        }
    
    async def search_with_context(
        self,
        query: str,
        include_graph: bool = True,
    ) -> Dict:
        """带上下文的搜索
        
        Args:
            query: 搜索关键词
            include_graph: 是否包含知识图谱上下文
        
        Returns:
            搜索结果 + 图谱上下文
        """
        result = {
            "query": query,
            "memories": [],
            "graph_context": None,
        }
        
        # 搜索记忆
        if self.long_term_storage:
            memories = await self.long_term_storage.search(query, limit=10)
            result["memories"] = [m.to_dict() for m in memories]
        
        # 获取图谱上下文
        if include_graph:
            # 查找相关实体
            entities = self.graph_extractor.get_temporal_entities()
            related_entities = [
                e.to_dict() for e in entities
                if query.lower() in e.name.lower() or query.lower() in e.entity_type.lower()
            ]
            result["graph_context"] = {
                "entities": related_entities[:5],
                "freshness": self.graph_extractor.get_knowledge_freshness_report(),
            }
        
        return result
    
    def __repr__(self) -> str:
        return f"MemoryManager(auto_promote={self.auto_promote_enabled}, auto_cleanup={self.auto_cleanup_enabled})"
