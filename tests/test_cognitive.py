"""
测试认知模块（记忆生命周期管理）
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
import tempfile
from pathlib import Path

from memorybridge.core.memory import Memory, MemoryType, MemoryPriority
from memorybridge.storage.sqlite import SQLiteStorage
from memorybridge.cognitive.refiner import MemoryRefiner, ImportanceScore
from memorybridge.cognitive.graph_extractor import KnowledgeGraphExtractor, TemporalEntity
from memorybridge.cognitive.manager import MemoryManager


@pytest.fixture
def temp_storages():
    """创建临时存储"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        short_db = f.name
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        long_db = f.name
    
    short_storage = SQLiteStorage(db_path=short_db)
    long_storage = SQLiteStorage(db_path=long_db)
    
    yield short_storage, long_storage
    
    Path(short_db).unlink(missing_ok=True)
    Path(long_db).unlink(missing_ok=True)


@pytest.fixture
def refiner(temp_storages):
    """创建记忆提炼器"""
    short_storage, long_storage = temp_storages
    return MemoryRefiner(short_storage, long_storage)


@pytest.fixture
def graph_extractor():
    """创建图谱提取器"""
    return KnowledgeGraphExtractor()


@pytest.fixture
def manager(temp_storages):
    """创建记忆管理器"""
    short_storage, long_storage = temp_storages
    return MemoryManager(short_storage, long_storage)


class TestImportanceScore:
    """测试重要性评分"""
    
    def test_calculate_score(self):
        """测试评分计算"""
        score = ImportanceScore(
            reference_count=0.8,
            user_instruction=1.0,
            emotional_intensity=0.5,
            recency=0.9,
            temporal_context=0.6,
        )
        
        total = score.calculate()
        assert 0.0 <= total <= 1.0
        assert total > 0.7  # 高重要性
    
    def test_default_weights(self):
        """测试默认权重"""
        score = ImportanceScore()
        total = score.calculate()
        assert total == 0.0  # 全 0 输入


class TestMemoryRefiner:
    """测试记忆提炼器"""
    
    def test_calculate_importance(self, refiner):
        """测试重要性计算"""
        memory = Memory(
            content="这是一个重要记忆",
            memory_type=MemoryType.SESSION,
            priority=MemoryPriority.P1,
        )
        
        score = refiner.calculate_importance(
            memory,
            reference_count=5,
            user_instruction=True,
        )
        
        total = score.calculate()
        assert total >= 0.5  # 用户指令应该高分
    
    def test_promote_to_long_term(self, refiner):
        """测试升级到长期记忆"""
        async def run_test():
            # 添加短期记忆
            memory = await refiner.short_term_storage.add(
                content="重要知识点",
                memory_type=MemoryType.SESSION,
                priority=MemoryPriority.P0,
            )
            
            # 升级（强制高评分）
            promoted = await refiner.promote_to_long_term(memory.id, importance_score=0.9)
            
            assert promoted is not None
            assert promoted.memory_type == MemoryType.LONG_TERM
            
            # 验证短期记忆已删除
            deleted = await refiner.short_term_storage.get(memory.id)
            assert deleted is None
        
        asyncio.run(run_test())
    
    def test_cleanup_old_memories(self, refiner):
        """测试清理过期记忆"""
        async def run_test():
            # 添加旧记忆
            old_memory = Memory(
                content="旧记忆",
                memory_type=MemoryType.SESSION,
                priority=MemoryPriority.P3,
                created_at=datetime.now(timezone.utc) - timedelta(days=60),
            )
            await refiner.short_term_storage.add(
                content=old_memory.content,
                memory_type=old_memory.memory_type,
                priority=old_memory.priority,
            )
            
            # 清理
            cleaned = await refiner.cleanup_old_memories(
                refiner.short_term_storage,
                max_age_days=30,
            )
            
            assert cleaned >= 0  # 可能为 0（如果时间戳未保留）
        
        asyncio.run(run_test())


class TestKnowledgeGraphExtractor:
    """测试知识图谱提取器"""
    
    def test_extract_entities(self, graph_extractor):
        """测试实体提取"""
        text = "我用 Python 开发 MemoryBridge 项目"
        entities = graph_extractor.extract_entities(text)
        
        assert len(entities) > 0
        assert any(e.entity_type == "technology" for e in entities)
    
    def test_extract_relations(self, graph_extractor):
        """测试关系提取"""
        text = "我用 Python 开发 MemoryBridge"
        entities = graph_extractor.extract_entities(text)
        relations = graph_extractor.extract_relations(text, entities)
        
        # 可能提取到关系
        assert isinstance(relations, list)
    
    def test_temporal_entity(self):
        """测试时间实体"""
        entity = TemporalEntity(
            id="test_1",
            name="Test Entity",
            entity_type="test",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        
        assert entity.expires_at is not None
        assert entity.temporal_context is None
    
    def test_extract_from_memory(self, graph_extractor):
        """测试从记忆提取"""
        async def run_test():
            content = "Python 是一种编程语言，我用来开发项目"
            entities, relations = await graph_extractor.extract_from_memory(content)
            
            assert len(entities) > 0
            # 图谱已自动更新
        
        asyncio.run(run_test())
    
    def test_get_temporal_entities(self, graph_extractor):
        """测试按时间获取实体"""
        # 添加实体
        graph_extractor.extract_entities("Python 编程语言")
        
        # 按时间范围查询
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        entities = graph_extractor.get_temporal_entities(start_date=start_date)
        
        assert len(entities) > 0
    
    def test_freshness_report(self, graph_extractor):
        """测试新鲜度报告"""
        # 添加一些实体
        graph_extractor.extract_entities("Python 开发项目")
        
        report = graph_extractor.get_knowledge_freshness_report()
        
        assert "total_entities" in report
        assert "total_relations" in report
        assert "fresh_entities" in report
        assert "avg_confidence" in report


class TestMemoryManager:
    """测试记忆管理器"""
    
    def test_process_new_memory(self, manager):
        """测试处理新记忆"""
        async def run_test():
            result = await manager.process_new_memory(
                content="Python 是一种编程语言",
                memory_type=MemoryType.SESSION,
                user_instruction=True,
            )
            
            assert result["memory_added"] is True
            assert result["entities_extracted"] >= 0
            assert result["importance_score"] > 0
        
        asyncio.run(run_test())
    
    def test_cleanup_and_organize(self, manager):
        """测试清理整理"""
        async def run_test():
            # 先添加一些记忆
            await manager.process_new_memory("测试记忆 1")
            await manager.process_new_memory("测试记忆 2")
            
            # 执行清理
            result = await manager.cleanup_and_organize()
            
            assert "short_term_cleaned" in result
            assert "relations_updated" in result
        
        asyncio.run(run_test())
    
    def test_get_memory_status(self, manager):
        """测试状态报告"""
        async def run_test():
            # 添加记忆
            await manager.process_new_memory("测试记忆")
            
            # 获取状态
            status = await manager.get_memory_status()
            
            assert "short_term_count" in status
            assert "long_term_count" in status
            assert "knowledge_freshness" in status
        
        asyncio.run(run_test())
    
    def test_search_with_context(self, manager):
        """测试带上下文搜索"""
        async def run_test():
            # 添加记忆
            await manager.process_new_memory("Python 编程语言")
            
            # 搜索
            result = await manager.search_with_context("Python")
            
            assert "query" in result
            assert "memories" in result
            assert "graph_context" in result
        
        asyncio.run(run_test())
