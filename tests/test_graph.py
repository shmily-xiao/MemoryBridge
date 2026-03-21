"""
知识图谱测试
"""

import pytest


class TestNetworkXGraph:
    """NetworkX 知识图谱测试"""

    @pytest.fixture
    def graph(self, tmp_path):
        """创建临时图谱"""
        from src.memorybridge.graph import NetworkXGraph
        db_path = tmp_path / "graph.db"
        return NetworkXGraph(str(db_path))

    def test_add_entity(self, graph):
        """测试添加实体"""
        entity_id = graph.add_entity(
            name="Python",
            entity_type="language",
            properties={"version": "3.10"}
        )

        assert entity_id is not None
        assert len(graph) == 1

    def test_get_entity(self, graph):
        """测试获取实体"""
        entity_id = graph.add_entity(name="Python", entity_type="language")

        entity = graph.get_entity(entity_id)
        assert entity is not None
        assert entity["name"] == "Python"

    def test_get_entity_by_name(self, graph):
        """测试通过名称获取实体"""
        graph.add_entity(name="Python", entity_type="language")

        entity = graph.get_entity_by_name("Python")
        assert entity is not None
        assert entity["name"] == "Python"

    def test_add_relation(self, graph):
        """测试添加关系"""
        from_id = graph.add_entity(name="MemoryBridge", entity_type="project")
        to_id = graph.add_entity(name="Python", entity_type="language")

        relation_id = graph.add_relation(from_id, to_id, "uses")
        assert relation_id is not None

    def test_add_invalid_relation(self, graph):
        """测试添加无效关系"""
        from_id = graph.add_entity(name="A", entity_type="test")
        to_id = graph.add_entity(name="B", entity_type="test")

        with pytest.raises(ValueError):
            graph.add_relation(from_id, to_id, "invalid_type")

    def test_query_relations(self, graph):
        """测试查询关系"""
        from_id = graph.add_entity(name="MemoryBridge", entity_type="project")
        to_id = graph.add_entity(name="Python", entity_type="language")
        graph.add_relation(from_id, to_id, "uses")

        relations = graph.query_relations(from_id)
        assert len(relations) == 1
        assert relations[0]["relation_type"] == "uses"

    def test_find_path(self, graph):
        """测试查找路径（多跳推理）"""
        # A -> B -> C
        a = graph.add_entity(name="A", entity_type="test")
        b = graph.add_entity(name="B", entity_type="test")
        c = graph.add_entity(name="C", entity_type="test")

        graph.add_relation(a, b, "knows")
        graph.add_relation(b, c, "knows")

        paths = graph.find_path(a, c, max_depth=3)
        assert len(paths) > 0
        assert paths[0]["length"] == 2

    def test_list_entities(self, graph):
        """测试列出实体"""
        graph.add_entity(name="Python", entity_type="language")
        graph.add_entity(name="Java", entity_type="language")
        graph.add_entity(name="MemoryBridge", entity_type="project")

        all_entities = graph.list_entities()
        assert len(all_entities) == 3

        languages = graph.list_entities(entity_type="language")
        assert len(languages) == 2

    def test_statistics(self, graph):
        """测试统计信息"""
        graph.add_entity(name="Python", entity_type="language")
        graph.add_entity(name="Java", entity_type="language")
        graph.add_entity(name="MemoryBridge", entity_type="project")

        stats = graph.get_statistics()
        assert stats["entity_count"] == 3
        assert stats["entity_types"] == 2

    def test_export_graph(self, graph):
        """测试导出图谱"""
        graph.add_entity(name="Python", entity_type="language")

        # GraphML
        graphml = graph.export_graph(format="graphml")
        assert "<?xml" in graphml

        # JSON
        json_data = graph.export_graph(format="json")
        assert "nodes" in json_data
