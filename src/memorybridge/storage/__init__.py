"""
Storage backends for MemoryBridge

Available backends:
- SQLiteStorage: Local SQLite database
- MongoDBStorage: MongoDB database (requires pymongo)
- TieredStorage: Multi-tier storage with auto-tiering
- OSSBackup: Alibaba Cloud OSS backup (requires oss2)
"""

from .sqlite import SQLiteStorage
from .factory import create_storage, create_storage_from_env

__all__ = [
    "SQLiteStorage",
    "create_storage",
    "create_storage_from_env",
]

# Optional imports (may not be available)
try:
    from .mongodb import MongoDBStorage
    __all__.append("MongoDBStorage")
except ImportError:
    pass

try:
    from .tiered_storage import TieredStorage
    __all__.append("TieredStorage")
except ImportError:
    pass

try:
    from .oss_backup import OSSBackup
    __all__.append("OSSBackup")
except ImportError:
    pass
