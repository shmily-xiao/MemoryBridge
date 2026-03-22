"""
存储后端工厂

根据配置创建不同的存储后端实例
"""

import os
from typing import Any, Dict, Optional

from ..core.service import MemoryService


def create_storage(
    backend: str = "sqlite",
    config: Optional[Dict[str, Any]] = None,
) -> MemoryService:
    """创建存储后端实例

    Args:
        backend: 存储后端类型
            - "sqlite": SQLite 存储 (默认)
            - "mongodb": MongoDB 存储
        config: 存储后端配置字典

    Returns:
        MemoryService 实例

    Examples:
        # SQLite
        storage = create_storage("sqlite", {"db_path": "~/.memorybridge/memories.db"})
        
        # MongoDB
        storage = create_storage("mongodb", {
            "connection_string": "mongodb://localhost:27017",
            "database": "memorybridge"
        })
    """
    config = config or {}

    if backend == "sqlite":
        from .sqlite import SQLiteStorage
        return SQLiteStorage(**config)

    elif backend == "mongodb":
        from .mongodb import MongoDBStorage
        return MongoDBStorage(**config)

    else:
        raise ValueError(
            f"Unknown backend: {backend}. "
            f"Supported backends: sqlite, mongodb"
        )


def create_storage_from_env() -> MemoryService:
    """从环境变量创建存储后端实例

    环境变量:
        MEMORYBRIDGE_BACKEND: 存储后端类型 (sqlite/mongodb)
        MEMORYBRIDGE_DB_PATH: SQLite 数据库路径
        MEMORYBRIDGE_MONGO_URI: MongoDB 连接字符串
        MEMORYBRIDGE_MONGO_DB: MongoDB 数据库名

    Returns:
        MemoryService 实例
    """
    backend = os.getenv("MEMORYBRIDGE_BACKEND", "sqlite").lower()

    if backend == "sqlite":
        config = {}
        if db_path := os.getenv("MEMORYBRIDGE_DB_PATH"):
            config["db_path"] = db_path
        return create_storage("sqlite", config)

    elif backend == "mongodb":
        config = {}
        if mongo_uri := os.getenv("MEMORYBRIDGE_MONGO_URI"):
            config["connection_string"] = mongo_uri
        if mongo_db := os.getenv("MEMORYBRIDGE_MONGO_DB"):
            config["database"] = mongo_db
        return create_storage("mongodb", config)

    else:
        raise ValueError(
            f"Unknown backend from env: {backend}. "
            f"Supported: sqlite, mongodb"
        )
