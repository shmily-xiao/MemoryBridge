#!/usr/bin/env python3
"""
存储后端使用示例

演示如何使用 SQLite 和 MongoDB 存储后端
"""

import asyncio
import os


async def demo_sqlite():
    """SQLite 存储示例"""
    print("=" * 60)
    print("SQLite 存储示例")
    print("=" * 60)
    
    from memorybridge.storage import SQLiteStorage
    from memorybridge.core.memory import MemoryType, MemoryPriority
    
    # 创建存储实例
    storage = SQLiteStorage(db_path="/tmp/demo_memorybridge.db")
    
    # 添加记忆
    print("\n1. 添加记忆...")
    memory = await storage.add(
        content="Python 是一种高级编程语言",
        memory_type=MemoryType.LONG_TERM,
        priority=MemoryPriority.P1,
        tags=["programming", "python"]
    )
    print(f"   ✓ 添加记忆：{memory.id}")
    
    # 搜索记忆
    print("\n2. 搜索记忆...")
    results = await storage.search("Python", limit=5)
    print(f"   ✓ 找到 {len(results)} 条记忆")
    for mem in results:
        print(f"      - {mem.content[:50]}...")
    
    # 统计
    print("\n3. 统计记忆...")
    count = await storage.count()
    print(f"   ✓ 总记忆数：{count}")
    
    # 导出
    print("\n4. 导出记忆...")
    exported = await storage.export(format="json")
    print(f"   ✓ 导出 {len(exported)} 字节 JSON")
    
    print("\n✅ SQLite 示例完成\n")


async def demo_mongodb():
    """MongoDB 存储示例"""
    print("=" * 60)
    print("MongoDB 存储示例")
    print("=" * 60)
    
    try:
        from memorybridge.storage import MongoDBStorage
        from memorybridge.core.memory import MemoryType, MemoryPriority
    except ImportError:
        print("   ⚠️  跳过：pymongo 未安装")
        print("   安装：pip install pymongo\n")
        return
    
    try:
        # 创建存储实例
        storage = MongoDBStorage(
            connection_string="mongodb://localhost:27017",
            database="memorybridge_demo",
            collection="memories"
        )
    except Exception as e:
        print(f"   ⚠️  跳过：MongoDB 不可用 ({e})")
        print("   确保 MongoDB 正在运行：brew services start mongodb-community\n")
        return
    
    # 添加记忆
    print("\n1. 添加记忆...")
    memory = await storage.add(
        content="MongoDB 是一个 NoSQL 数据库",
        memory_type=MemoryType.LONG_TERM,
        priority=MemoryPriority.P1,
        tags=["database", "nosql"]
    )
    print(f"   ✓ 添加记忆：{memory.id}")
    
    # 搜索记忆
    print("\n2. 搜索记忆...")
    results = await storage.search("MongoDB", limit=5)
    print(f"   ✓ 找到 {len(results)} 条记忆")
    for mem in results:
        print(f"      - {mem.content[:50]}...")
    
    # 聚合查询
    print("\n3. 聚合查询（按标签统计）...")
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    tag_stats = await storage.aggregate(pipeline)
    for stat in tag_stats:
        print(f"      - {stat['_id']}: {stat['count']}")
    
    # 统计
    print("\n4. 统计记忆...")
    count = await storage.count()
    print(f"   ✓ 总记忆数：{count}")
    
    # 清理
    print("\n5. 清理测试数据...")
    await storage.drop_database()
    print(f"   ✓ 已删除测试数据库")
    
    print("\n✅ MongoDB 示例完成\n")


async def demo_factory():
    """存储工厂示例"""
    print("=" * 60)
    print("存储工厂示例")
    print("=" * 60)
    
    from memorybridge.storage.factory import create_storage, create_storage_from_env
    from memorybridge.core.memory import MemoryType
    
    # 使用工厂创建 SQLite
    print("\n1. 使用工厂创建 SQLite 存储...")
    storage = create_storage(
        backend="sqlite",
        config={"db_path": "/tmp/factory_demo.db"}
    )
    print(f"   ✓ 创建存储：{storage}")
    
    # 添加记忆
    await storage.add("Factory test", memory_type=MemoryType.LONG_TERM)
    count = await storage.count()
    print(f"   ✓ 记忆数：{count}")
    
    # 从环境变量创建
    print("\n2. 从环境变量创建存储...")
    os.environ["MEMORYBRIDGE_BACKEND"] = "sqlite"
    storage_from_env = create_storage_from_env()
    print(f"   ✓ 创建存储：{storage_from_env}")
    
    print("\n✅ 工厂示例完成\n")


async def main():
    """运行所有示例"""
    print("\n🚀 MemoryBridge 存储后端示例\n")
    
    # SQLite 示例
    await demo_sqlite()
    
    # MongoDB 示例（如果可用）
    await demo_mongodb()
    
    # 工厂示例
    await demo_factory()
    
    print("🎉 所有示例完成！")


if __name__ == "__main__":
    asyncio.run(main())
