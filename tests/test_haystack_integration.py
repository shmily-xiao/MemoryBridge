"""
测试 Haystack DocumentStore 集成
"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from memorybridge.integrations.haystack_docstore import HaystackDocumentStore


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def doc_store(temp_db):
    return HaystackDocumentStore(backend="sqlite", db_path=temp_db, index="test_index")


class TestHaystackDocumentStore:
    """测试 Haystack DocumentStore 集成"""
    
    def test_init(self, doc_store):
        assert doc_store.backend == "sqlite"
        assert doc_store.index == "test_index"
    
    def test_write_documents(self, doc_store):
        async def run_test():
            docs = [
                {"content": "Python 是一种编程语言", "meta": {"topic": "programming"}},
                {"content": "机器学习是 AI 的核心", "meta": {"topic": "ai"}},
            ]
            ids = await doc_store.write_documents(docs)
            assert len(ids) == 2
        asyncio.run(run_test())
    
    def test_query(self, doc_store):
        async def run_test():
            docs = [
                {"content": "Python 编程语言教程", "meta": {"topic": "programming"}},
                {"content": "机器学习入门指南", "meta": {"topic": "ai"}},
            ]
            await doc_store.write_documents(docs)
            
            results = await doc_store.query("Python", top_k=5)
            assert len(results) > 0
            assert "Python" in results[0]["content"]
        asyncio.run(run_test())
    
    def test_get_document_by_id(self, doc_store):
        async def run_test():
            docs = [{"content": "测试文档", "meta": {}}]
            ids = await doc_store.write_documents(docs)
            
            doc = await doc_store.get_document_by_id(ids[0])
            assert doc is not None
            assert doc["content"] == "测试文档"
        asyncio.run(run_test())
    
    def test_get_documents_by_ids(self, doc_store):
        async def run_test():
            docs = [
                {"content": "文档 1", "meta": {}},
                {"content": "文档 2", "meta": {}},
            ]
            ids = await doc_store.write_documents(docs)
            
            retrieved = await doc_store.get_documents_by_ids(ids)
            assert len(retrieved) == 2
        asyncio.run(run_test())
    
    def test_delete_documents(self, doc_store):
        async def run_test():
            docs = [{"content": "待删除文档", "meta": {}}]
            ids = await doc_store.write_documents(docs)
            
            count = await doc_store.delete_documents(ids=ids)
            assert count == 1
            
            doc = await doc_store.get_document_by_id(ids[0])
            assert doc is None
        asyncio.run(run_test())
    
    def test_get_document_count(self, doc_store):
        async def run_test():
            initial_count = await doc_store.get_document_count()
            
            docs = [{"content": f"文档{i}", "meta": {}} for i in range(5)]
            await doc_store.write_documents(docs)
            
            final_count = await doc_store.get_document_count()
            assert final_count == initial_count + 5
        asyncio.run(run_test())
    
    def test_get_all_documents(self, doc_store):
        async def run_test():
            docs = [
                {"content": "文档 1", "meta": {"index": "test_index"}},
                {"content": "文档 2", "meta": {"index": "test_index"}},
            ]
            await doc_store.write_documents(docs)
            
            all_docs = await doc_store.get_all_documents(index="test_index")
            assert len(all_docs) == 2
        asyncio.run(run_test())
    
    def test_update_document_meta(self, doc_store):
        async def run_test():
            docs = [{"content": "测试文档", "meta": {"old_key": "old_value"}}]
            ids = await doc_store.write_documents(docs)
            
            await doc_store.update_document_meta(ids[0], {"new_key": "new_value"})
            
            doc = await doc_store.get_document_by_id(ids[0])
            assert doc["meta"]["new_key"] == "new_value"
        asyncio.run(run_test())
    
    def test_query_with_filters(self, doc_store):
        async def run_test():
            docs = [
                {"content": "Python 教程", "meta": {"topic": "programming", "level": "beginner"}},
                {"content": "Python 高级", "meta": {"topic": "programming", "level": "advanced"}},
            ]
            await doc_store.write_documents(docs)
            
            # 按元数据过滤
            results = await doc_store.query(
                "Python",
                filters={"meta": {"level": "beginner"}},
                top_k=5
            )
            assert len(results) >= 1
            assert results[0]["meta"]["level"] == "beginner"
        asyncio.run(run_test())
    
    def test_delete_documents_with_filters(self, doc_store):
        async def run_test():
            docs = [
                {"content": "文档 1", "meta": {"category": "temp"}},
                {"content": "文档 2", "meta": {"category": "permanent"}},
            ]
            await doc_store.write_documents(docs)
            
            # 按过滤条件删除
            count = await doc_store.delete_documents(
                filters={"category": "temp"}
            )
            assert count >= 1
            
            final_count = await doc_store.get_document_count()
            assert final_count == 1
        asyncio.run(run_test())
    
    def test_repr(self, doc_store):
        repr_str = repr(doc_store)
        assert "HaystackDocumentStore" in repr_str
        assert "test_index" in repr_str
