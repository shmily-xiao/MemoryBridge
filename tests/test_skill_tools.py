"""
Skill 工具测试
"""

import pytest
import json
import tempfile
from pathlib import Path


class TestSkillTools:
    """Skill 工具测试"""

    @pytest.fixture
    def test_db(self, tmp_path):
        """创建临时数据库"""
        db_path = tmp_path / "test.db"
        return str(db_path)

    def test_memory_add(self, test_db):
        """测试添加记忆"""
        from src.memorybridge.skill_tools import memory_add
        
        result = memory_add(
            content="测试内容",
            type="long_term",
            priority="p1",
            tags="测试，python",
            db_path=test_db
        )
        
        assert result["success"] is True
        assert "memory" in result
        assert result["memory"]["content"] == "测试内容"
        assert result["memory"]["memory_type"] == "long_term"
        assert result["memory"]["priority"] == "p1"
        assert result["memory"]["tags"] == ["测试", "python"]

    def test_memory_search(self, test_db):
        """测试搜索记忆"""
        from src.memorybridge.skill_tools import memory_add, memory_search
        
        # 先添加
        memory_add("Python 编程语言", type="long_term", db_path=test_db)
        memory_add("Java 编程语言", type="long_term", db_path=test_db)
        
        # 搜索
        result = memory_search("Python", db_path=test_db)
        
        assert result["success"] is True
        assert result["count"] == 1
        assert "Python" in result["memories"][0]["content"]

    def test_memory_list(self, test_db):
        """测试列出记忆"""
        from src.memorybridge.skill_tools import memory_add, memory_list
        
        # 添加 5 条记忆
        for i in range(5):
            memory_add(f"记忆{i}", db_path=test_db)
        
        # 列出
        result = memory_list(limit=10, db_path=test_db)
        
        assert result["success"] is True
        assert result["count"] == 5

    def test_memory_get(self, test_db):
        """测试获取记忆详情"""
        from src.memorybridge.skill_tools import memory_add, memory_get
        
        # 添加
        add_result = memory_add("测试内容", db_path=test_db)
        memory_id = add_result["memory"]["id"]
        
        # 获取
        result = memory_get(memory_id, db_path=test_db)
        
        assert result["success"] is True
        assert result["memory"]["id"] == memory_id
        assert result["memory"]["content"] == "测试内容"

    def test_memory_get_not_found(self, test_db):
        """测试获取不存在的记忆"""
        from src.memorybridge.skill_tools import memory_get
        
        result = memory_get("non-existent-id", db_path=test_db)
        
        assert result["success"] is False
        assert "error" in result

    def test_memory_update(self, test_db):
        """测试更新记忆"""
        from src.memorybridge.skill_tools import memory_add, memory_update
        
        # 添加
        add_result = memory_add("原始内容", db_path=test_db)
        memory_id = add_result["memory"]["id"]
        
        # 更新
        result = memory_update(memory_id, content="新内容", db_path=test_db)
        
        assert result["success"] is True
        assert result["memory"]["content"] == "新内容"

    def test_memory_delete(self, test_db):
        """测试删除记忆"""
        from src.memorybridge.skill_tools import memory_add, memory_delete
        
        # 添加
        add_result = memory_add("待删除", db_path=test_db)
        memory_id = add_result["memory"]["id"]
        
        # 删除
        result = memory_delete(memory_id, db_path=test_db)
        
        assert result["success"] is True
        assert "已删除" in result["message"]

    def test_memory_status(self, test_db):
        """测试查看状态"""
        from src.memorybridge.skill_tools import memory_add, memory_status
        
        # 添加
        memory_add("记忆 1", type="long_term", db_path=test_db)
        memory_add("记忆 2", type="session", db_path=test_db)
        
        # 状态
        result = memory_status(db_path=test_db)
        
        assert result["success"] is True
        assert result["total"] == 2
        assert result["long_term_count"] == 1
        assert result["session_count"] == 1

    def test_memory_export_import(self, test_db, tmp_path):
        """测试导出导入"""
        from src.memorybridge.skill_tools import memory_add, memory_export, memory_import
        
        # 添加
        memory_add("记忆 1", tags=["test"], db_path=test_db)
        memory_add("记忆 2", db_path=test_db)
        
        # 导出
        export_file = tmp_path / "export.json"
        result = memory_export(output=str(export_file), db_path=test_db)
        
        assert result["success"] is True
        assert export_file.exists()
        
        # 导入到新数据库
        new_db = tmp_path / "new.db"
        result = memory_import(input=str(export_file), db_path=str(new_db))
        
        assert result["success"] is True
        assert result["count"] == 2
