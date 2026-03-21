"""
Storage module - 存储后端实现
"""

from .sqlite import SQLiteStorage

__all__ = [
    "SQLiteStorage",
]
