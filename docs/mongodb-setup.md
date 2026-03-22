# MongoDB 存储后端配置指南

MemoryBridge 现在支持 MongoDB 作为存储后端，适合大规模部署和分布式场景。

## 安装依赖

```bash
# 安装 MongoDB 支持
pip install pymongo

# 或使用项目的可选依赖
cd /Users/shmily/workspace/MemoryBridge
pip install -e ".[mongodb]" --break-system-packages
```

## 安装 MongoDB

### macOS (Homebrew)

```bash
# 安装 MongoDB Community Edition
brew tap mongodb/brew
brew install mongodb-community

# 启动 MongoDB 服务
brew services start mongodb-community

# 验证安装
mongosh --eval "db.version()"
```

### Docker

```bash
docker run -d \
  -p 27017:27017 \
  --name mongodb \
  -v mongodb_data:/data/db \
  mongo:latest
```

### 使用 MongoDB Atlas (云端)

1. 访问 https://www.mongodb.com/cloud/atlas
2. 创建免费集群
3. 获取连接字符串
4. 配置白名单 IP

## 配置 MemoryBridge 使用 MongoDB

### 方法 1: 环境变量

```bash
export MEMORYBRIDGE_BACKEND=mongodb
export MEMORYBRIDGE_MONGO_URI="mongodb://localhost:27017"
export MEMORYBRIDGE_MONGO_DB="memorybridge"

# 使用 CLI
memorybridge add "Test memory" --type long_term
```

### 方法 2: Python 代码

```python
from memorybridge.storage import MongoDBStorage

# 本地 MongoDB
storage = MongoDBStorage(
    connection_string="mongodb://localhost:27017",
    database="memorybridge",
    collection="memories"
)

# 远程 MongoDB (Atlas)
storage = MongoDBStorage(
    connection_string="mongodb+srv://user:pass@cluster.mongodb.net",
    database="memorybridge"
)

# 使用记忆
await storage.add("Python 是一种编程语言", tags=["programming"])
results = await storage.search("Python")
```

### 方法 3: 工厂函数

```python
from memorybridge.storage.factory import create_storage

# 创建 MongoDB 存储
storage = create_storage(
    backend="mongodb",
    config={
        "connection_string": "mongodb://localhost:27017",
        "database": "memorybridge"
    }
)
```

## MongoDB vs SQLite 对比

| 特性 | SQLite | MongoDB |
|------|--------|---------|
| 适用场景 | 个人使用，本地开发 | 大规模，分布式 |
| 配置复杂度 | 零配置 | 需要安装 MongoDB |
| 性能 | 单用户优秀 | 多用户并发优秀 |
| 扩展性 | 垂直扩展 | 水平扩展 |
| 查询能力 | SQL | 灵活查询 + 聚合 |
| 数据量 | <10GB | 无限制 |
| 备份 | 文件拷贝 | mongodump |

## 高级功能

### 聚合查询

```python
# 按类型统计
pipeline = [
    {"$group": {
        "_id": "$memory_type",
        "count": {"$sum": 1}
    }}
]
results = await storage.aggregate(pipeline)

# 按标签统计
pipeline = [
    {"$unwind": "$tags"},
    {"$group": {
        "_id": "$tags",
        "count": {"$sum": 1}
    }},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]
top_tags = await storage.aggregate(pipeline)
```

### 全文搜索

```python
# MongoDB 全文搜索会自动使用 $text 索引
results = await storage.search(
    query="Python programming",
    limit=20,
    filters={"priority": "p0"}
)
```

### 数据备份

```bash
# 导出
mongodump --db memorybridge --out ./backup

# 导入
mongorestore --db memorybridge ./backup/memorybridge
```

## 性能优化

### 索引建议

MongoDB 存储会自动创建以下索引：

- `memory_type` - 类型过滤
- `priority` - 优先级过滤
- `created_at` - 时间排序
- `content` (TEXT) - 全文搜索
- `tags` - 标签查询
- 复合索引 - 常用查询组合

### 连接池配置

对于高并发场景，可以配置连接池：

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017",
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000
)
```

## 故障排查

### 连接失败

```bash
# 检查 MongoDB 是否运行
brew services list

# 查看 MongoDB 日志
tail -f /usr/local/var/log/mongodb/mongo.log

# 测试连接
mongosh mongodb://localhost:27017
```

### 权限问题

确保 MongoDB 用户有读写权限：

```javascript
use memorybridge
db.createUser({
  user: "memorybridge_user",
  pwd: "secure_password",
  roles: ["readWrite"]
})
```

## 下一步

- [ ] 添加 MongoDB 性能基准测试
- [ ] 支持 MongoDB 变更流（实时同步）
- [ ] 添加数据分片支持
- [ ] MongoDB Atlas 集成指南
