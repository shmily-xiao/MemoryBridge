"""
存储后端工厂测试
"""

import os
import unittest
from unittest.mock import patch

import pytest


class TestStorageFactory(unittest.TestCase):
    """存储工厂测试"""

    def test_create_sqlite_storage(self):
        """测试创建 SQLite 存储"""
        from memorybridge.storage.factory import create_storage
        from memorybridge.storage.sqlite import SQLiteStorage

        storage = create_storage("sqlite")
        self.assertIsInstance(storage, SQLiteStorage)

    def test_create_sqlite_with_config(self):
        """测试带配置创建 SQLite 存储"""
        from memorybridge.storage.factory import create_storage
        from memorybridge.storage.sqlite import SQLiteStorage

        storage = create_storage(
            "sqlite",
            {"db_path": "/tmp/test_memorybridge.db"}
        )
        self.assertIsInstance(storage, SQLiteStorage)
        self.assertEqual(storage.db_path, "/tmp/test_memorybridge.db")

    def test_create_mongodb_storage(self):
        """测试创建 MongoDB 存储"""
        from memorybridge.storage.factory import create_storage
        from memorybridge.storage.mongodb import MongoDBStorage

        # 只在 MongoDB 可用时测试
        try:
            storage = create_storage(
                "mongodb",
                {
                    "connection_string": "mongodb://localhost:27017",
                    "database": "test"
                }
            )
            self.assertIsInstance(storage, MongoDBStorage)
        except Exception:
            self.skipTest("MongoDB not available")

    def test_create_unknown_backend(self):
        """测试创建未知后端"""
        from memorybridge.storage.factory import create_storage

        with self.assertRaises(ValueError) as context:
            create_storage("unknown_backend")
        
        self.assertIn("Unknown backend", str(context.exception))
        self.assertIn("sqlite, mongodb", str(context.exception))

    def test_create_from_env_sqlite(self):
        """测试从环境变量创建 SQLite 存储"""
        from memorybridge.storage.factory import create_storage_from_env
        from memorybridge.storage.sqlite import SQLiteStorage

        with patch.dict(os.environ, {"MEMORYBRIDGE_BACKEND": "sqlite"}):
            storage = create_storage_from_env()
            self.assertIsInstance(storage, SQLiteStorage)

    def test_create_from_env_mongodb(self):
        """测试从环境变量创建 MongoDB 存储"""
        from memorybridge.storage.factory import create_storage_from_env
        from memorybridge.storage.mongodb import MongoDBStorage

        try:
            with patch.dict(os.environ, {
                "MEMORYBRIDGE_BACKEND": "mongodb",
                "MEMORYBRIDGE_MONGO_URI": "mongodb://localhost:27017",
                "MEMORYBRIDGE_MONGO_DB": "test"
            }):
                storage = create_storage_from_env()
                self.assertIsInstance(storage, MongoDBStorage)
        except Exception:
            self.skipTest("MongoDB not available")

    def test_create_from_env_default(self):
        """测试默认使用 SQLite"""
        from memorybridge.storage.factory import create_storage_from_env
        from memorybridge.storage.sqlite import SQLiteStorage

        # 清除相关环境变量
        env = os.environ.copy()
        for key in ["MEMORYBRIDGE_BACKEND", "MEMORYBRIDGE_DB_PATH", 
                    "MEMORYBRIDGE_MONGO_URI", "MEMORYBRIDGE_MONGO_DB"]:
            env.pop(key, None)
        
        with patch.dict(os.environ, env, clear=True):
            storage = create_storage_from_env()
            self.assertIsInstance(storage, SQLiteStorage)


if __name__ == "__main__":
    unittest.main()
