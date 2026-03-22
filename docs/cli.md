# CLI 使用指南

MemoryBridge 提供完整的命令行界面，支持记忆管理、知识图谱操作等。

## 安装

```bash
pip3 install -e . --break-system-packages
```

## 基础命令

### 添加记忆

```bash
memorybridge add "Python 是一种编程语言" \
  --type long_term \
  --priority p1 \
  --tags "python,language"
```

**参数**:
- `content`: 记忆内容（必填）
- `--type, -t`: 记忆类型 (session/long_term)
- `--priority, -p`: 优先级 (p0/p1/p2/p3)
- `--tags`: 标签，逗号分隔
- `--backend, -b`: 存储后端 (sqlite/mongodb)

### 搜索记忆

```bash
memorybridge search "Python" --limit 10
```

**参数**:
- `query`: 搜索关键词（必填）
- `--limit, -l`: 返回数量
- `--type, -t`: 记忆类型过滤

### 列出记忆

```bash
memorybridge list --limit 20
```

### 查看记忆详情

```bash
memorybridge get <memory_id>
```

### 更新记忆

```bash
memorybridge update <memory_id> \
  --content "新内容" \
  --tags "new,updated"
```

### 删除记忆

```bash
memorybridge delete <memory_id>
```

### 导出/导入

```bash
# 导出
memorybridge export -o backup.json

# 导入
memorybridge import -i backup.json
```

### 查看状态

```bash
memorybridge status
```

## 知识图谱命令

### 添加实体

```bash
memorybridge graph add-entity "Python" \
  --type language \
  --props '{"version": "3.12"}'
```

### 添加关系

```bash
memorybridge graph add-relation \
  <from_entity_id> \
  uses \
  <to_entity_id>
```

**有效关系类型**: uses, knows, related_to, part_of

### 查询关系

```bash
memorybridge graph query <entity_id>
```

### 查找路径（多跳推理）

```bash
memorybridge graph find-path <from_id> <to_id> --depth 3
```

### 图谱统计

```bash
memorybridge graph stats
```

### 导出图谱

```bash
memorybridge graph export \
  -o graph.graphml \
  --format graphml
```

**支持格式**: graphml, gexf, json

## 配置命令

```bash
# 显示配置
memorybridge config --show

# 设置默认后端
memorybridge config --backend mongodb

# 配置 MongoDB
memorybridge config \
  --backend mongodb \
  --mongo-uri "mongodb://localhost:27017" \
  --mongo-db "memorybridge"
```

## 备份命令

```bash
# 创建备份
memorybridge backup backup

# 列出备份
memorybridge backup list

# 恢复备份
memorybridge backup restore --target backup_20260322.json
```

## 多后端支持

```bash
# 使用 SQLite（默认）
memorybridge add "记忆" --backend sqlite

# 使用 MongoDB
memorybridge add "记忆" --backend mongodb

# 使用分层存储
memorybridge add "记忆" --backend tiered
```

## 环境变量

```bash
# 设置默认后端
export MEMORYBRIDGE_BACKEND=sqlite

# MongoDB 配置
export MEMORYBRIDGE_MONGO_URI="mongodb://localhost:27017"
export MEMORYBRIDGE_MONGO_DB="memorybridge"

# OSS 备份配置
export OSS_ACCESS_KEY_ID="your_key"
export OSS_ACCESS_KEY_SECRET="your_secret"
export OSS_BUCKET_NAME="your_bucket"
```

## 示例脚本

```bash
#!/bin/bash
# 批量添加记忆

memories=(
  "Python 是一种编程语言"
  "机器学习是 AI 的核心"
  "MemoryBridge 是记忆管理平台"
)

for memory in "${memories[@]}"; do
  memorybridge add "$memory" --type long_term --priority p1
done

echo "✅ 添加了 ${#memories[@]} 条记忆"
```

## 故障排查

### 命令执行慢

```bash
# 检查数据库大小
memorybridge status

# 清理过期记忆
memorybridge cleanup --max-age 90
```

### 搜索结果为空

```bash
# 检查索引
memorybridge graph rebuild-index

# 尝试关键词搜索
memorybridge search "关键词" --limit 50
```

---

**相关文档**:
- [快速开始](quickstart.md)
- [Skill 集成](skill-integration.md)
- [向量搜索](advanced/vector-search.md)
