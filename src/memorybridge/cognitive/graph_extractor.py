"""
KnowledgeGraphExtractor - 知识图谱提取器

从对话/记忆中自动提取实体和关系，支持时间维度追踪
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from ..graph.networkx_graph import NetworkXGraph


@dataclass
class TemporalEntity:
    """带时间维度的实体"""
    id: str
    name: str
    entity_type: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    properties: Dict = field(default_factory=dict)
    temporal_context: Optional[str] = None  # 时间上下文，如 "2026-Q1"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "properties": self.properties,
            "temporal_context": self.temporal_context,
        }


@dataclass
class TemporalRelation:
    """带时间维度的关系"""
    from_id: str
    to_id: str
    relation_type: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_verified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 0.95  # 置信度
    decay_rate: float = 0.01  # 每月衰减率
    properties: Dict = field(default_factory=dict)
    
    def update_confidence(self) -> float:
        """根据时间衰减更新置信度"""
        now = datetime.now(timezone.utc)
        months_old = (now - self.last_verified).days / 30.0
        self.confidence = max(0.1, self.confidence * (1 - self.decay_rate * months_old))
        return self.confidence
    
    def to_dict(self) -> Dict:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation_type": self.relation_type,
            "created_at": self.created_at.isoformat(),
            "last_verified": self.last_verified.isoformat(),
            "confidence": self.confidence,
            "decay_rate": self.decay_rate,
            "properties": self.properties,
        }


class KnowledgeGraphExtractor:
    """知识图谱提取器
    
    从文本中自动提取实体和关系，支持：
    - 命名实体识别（简化版）
    - 关系抽取
    - 时间维度追踪
    - 置信度管理
    """
    
    # 实体类型映射（简化版，实际可用 NLP 模型）
    ENTITY_PATTERNS = {
        "person": r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # 人名
        "organization": r"\b[A-Z][a-zA-Z]+\s+(Inc|Ltd|Corp|Company|Organization)\b",
        "technology": r"\b(Python|JavaScript|Java|Rust|Go|MemoryBridge|OpenClaw|AI|ML)\b",
        "project": r"\b[A-Z][a-zA-Z]+\s*(Project|App|System|Platform)?\b",
        "date": r"\b(\d{4}-\d{2}-\d{2}|today|tomorrow|yesterday|recently)\b",
        "location": r"\b(Beijing|Shanghai|New York|London|China|USA)\b",
    }
    
    # 关系模式
    RELATION_PATTERNS = {
        "uses": r"(使用|uses|using|with)\s+(.+)",
        "develops": r"(开发|develops|developing|built|created)\s+(.+)",
        "works_at": r"(工作于|works at|works for|employed by)\s+(.+)",
        "located_in": r"(位于|located in|based in)\s+(.+)",
        "related_to": r"(相关|related to|associated with)\s+(.+)",
        "part_of": r"(属于|part of|belongs to)\s+(.+)",
    }
    
    def __init__(self, graph: Optional[NetworkXGraph] = None):
        """初始化提取器
        
        Args:
            graph: 知识图谱实例
        """
        self.graph = graph or NetworkXGraph()
        self._entity_cache: Dict[str, TemporalEntity] = {}
        self._relation_cache: List[TemporalRelation] = []
    
    def extract_entities(self, text: str) -> List[TemporalEntity]:
        """从文本中提取实体
        
        Args:
            text: 输入文本
        
        Returns:
            实体列表
        """
        entities = []
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # 清理实体名称
                name = match.strip() if isinstance(match, str) else match[0]
                
                # 创建实体
                entity = TemporalEntity(
                    id=f"{entity_type}_{name.lower().replace(' ', '_')}",
                    name=name,
                    entity_type=entity_type,
                    properties={
                        "source": "text_extraction",
                        "original_text": text[:100],
                    },
                    temporal_context=datetime.now().strftime("%Y-%m")
                )
                
                entities.append(entity)
                self._entity_cache[entity.id] = entity
        
        return entities
    
    def extract_relations(
        self,
        text: str,
        entities: List[TemporalEntity],
    ) -> List[TemporalRelation]:
        """从文本中提取关系
        
        Args:
            text: 输入文本
            entities: 已提取的实体列表
        
        Returns:
            关系列表
        """
        relations = []
        
        for relation_type, pattern in self.RELATION_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # 尝试匹配实体
                target = match.strip() if isinstance(match, str) else match[0]
                
                # 查找源实体和目标实体
                for entity in entities:
                    if entity.name.lower() in text.lower():
                        # 查找目标实体
                        for target_entity in entities:
                            if target_entity.name.lower() in target.lower():
                                relation = TemporalRelation(
                                    from_id=entity.id,
                                    to_id=target_entity.id,
                                    relation_type=relation_type,
                                    properties={
                                        "source": "text_extraction",
                                        "original_text": text[:100],
                                    }
                                )
                                relations.append(relation)
                                self._relation_cache.append(relation)
        
        return relations
    
    async def extract_from_memory(
        self,
        content: str,
        auto_save: bool = True,
    ) -> Tuple[List[TemporalEntity], List[TemporalRelation]]:
        """从记忆内容提取知识图谱
        
        Args:
            content: 记忆内容
            auto_save: 是否自动保存到图谱
        
        Returns:
            (实体列表，关系列表)
        """
        # 提取实体
        entities = self.extract_entities(content)
        
        # 提取关系
        relations = self.extract_relations(content, entities)
        
        # 自动保存到图谱
        if auto_save and entities:
            await self._save_to_graph(entities, relations)
        
        return entities, relations
    
    async def _save_to_graph(
        self,
        entities: List[TemporalEntity],
        relations: List[TemporalRelation],
    ) -> None:
        """保存实体和关系到图谱"""
        # 保存实体
        for entity in entities:
            try:
                self.graph.add_entity(
                    name=entity.name,
                    entity_type=entity.entity_type,
                    properties=entity.to_dict(),
                )
            except ValueError:
                # 实体已存在，更新
                existing = self.graph.get_entity_by_name(entity.name)
                if existing:
                    # 更新实体时间戳
                    entity.updated_at = datetime.now(timezone.utc)
        
        # 保存关系
        for relation in relations:
            try:
                # 查找实体 ID
                from_entity = self.graph.get_entity_by_name(
                    next((e.name for e in entities if e.id == relation.from_id), None)
                )
                to_entity = self.graph.get_entity_by_name(
                    next((e.name for e in entities if e.id == relation.to_id), None)
                )
                
                if from_entity and to_entity:
                    self.graph.add_relation(
                        from_id=from_entity["id"],
                        to_id=to_entity["id"],
                        relation_type=relation.relation_type,
                        properties=relation.to_dict(),
                    )
            except ValueError:
                continue
    
    def get_temporal_entities(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TemporalEntity]:
        """按时间范围获取实体
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            实体列表
        """
        entities = list(self._entity_cache.values())
        
        if start_date:
            entities = [e for e in entities if e.created_at >= start_date]
        if end_date:
            entities = [e for e in entities if e.created_at <= end_date]
        
        return entities
    
    def get_expiring_entities(self, days: int = 30) -> List[TemporalEntity]:
        """获取即将过期的实体
        
        Args:
            days: 天数阈值
        
        Returns:
            即将过期的实体列表
        """
        from datetime import timedelta
        threshold = datetime.now(timezone.utc) + timedelta(days=days)
        
        return [
            e for e in self._entity_cache.values()
            if e.expires_at and e.expires_at < threshold
        ]
    
    def update_relation_confidence(self) -> Dict[str, float]:
        """更新所有关系的置信度
        
        Returns:
            关系 ID 到置信度的映射
        """
        confidence_map = {}
        
        for relation in self._relation_cache:
            confidence = relation.update_confidence()
            key = f"{relation.from_id}-{relation.to_id}-{relation.relation_type}"
            confidence_map[key] = confidence
        
        return confidence_map
    
    def get_knowledge_freshness_report(self) -> Dict:
        """获取知识新鲜度报告
        
        Returns:
            报告字典
        """
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        one_month_ago = now - timedelta(days=30)
        six_months_ago = now - timedelta(days=180)
        
        entities = list(self._entity_cache.values())
        
        return {
            "total_entities": len(entities),
            "total_relations": len(self._relation_cache),
            "fresh_entities": len([e for e in entities if e.created_at > one_month_ago]),
            "stale_entities": len([e for e in entities if e.created_at < six_months_ago]),
            "expiring_soon": len(self.get_expiring_entities()),
            "avg_confidence": sum(r.confidence for r in self._relation_cache) / len(self._relation_cache) if self._relation_cache else 0,
        }
    
    def __repr__(self) -> str:
        return f"KnowledgeGraphExtractor(entities={len(self._entity_cache)}, relations={len(self._relation_cache)})"
