# MemoryBridge 快速开始指南

## 📦 安装

### 1. 克隆项目

```bash
cd ~/.openclaw/workspace/projects
# 项目已创建在此目录
```

### 2. 安装依赖

```bash
cd memorybridge
pip install -e ".[dev]"
```

### 3. 验证安装

```bash
memorybridge --help
```

应该看到 CLI 帮助信息。

---

## 🚀 基本使用

### 添加记忆

```bash
# 添加长期记忆
memorybridge add "Python 是一种编程语言" \
  --type long_term \
  --priority p1 \
  --tags "python,language"

# 添加 Session 记忆
memorybridge add "当前正在开发 MemoryBridge 项目" \
  --type session \
  --priority p2
```

### 搜索记忆

```bash
# 关键词搜索
memorybridge search "Python"

# 限制结果数量
memorybridge search "编程" --limit 5

# 按类型过滤
memorybridge search "记忆" --type long_term
```

### 列出记忆

```bash
# 列出所有
memorybridge list

# 列出前 10 条
memorybridge list --limit 10

# 按类型列出
memorybridge list --type session
```

### 查看详情

```bash
memorybridge get <memory_id>
```

### 更新记忆

```bash
# 更新内容
memorybridge update <memory_id> --content "新内容"

# 更新标签
memorybridge update <memory_id> --tags "new,updated"
```

### 删除记忆

```bash
memorybridge delete <memory_id>
```

### 导出导入

```bash
# 导出到文件
memorybridge export -o backup.json

# 从文件导入
memorybridge import -i backup.json
```

### 查看状态

```bash
memorybridge status
```

---

## 💡 使用示例

### 示例 1: 学习知识管理

```bash
# 添加知识点
memorybridge add "Agent Memory 分为四层：工作记忆、对话记忆、任务记忆、长期记忆" \
  --type long_term \
  --priority p1 \
  --tags "ai,memory,architecture"

memorybridge add "NetworkX 是 Python 图论库，支持内存图操作" \
  --type long_term \
  --priority p1 \
  --tags "python,graph,networkx"

# 搜索相关知识
memorybridge search "Memory"
```

### 示例 2: 任务管理

```bash
# 添加任务
memorybridge add "完成 MemoryBridge Phase 1 开发" \
  --type session \
  --priority p0 \
  --tags "task,development"

# 更新任务状态
memorybridge update <task_id> --content "✅ 完成 MemoryBridge Phase 1 开发"

# 搜索任务
memorybridge search "task" --type session
```

### 示例 3: 备份和迁移

```bash
# 定期备份
memorybridge export -o backup-$(date +%Y%m%d).json

# 迁移到新机器
memorybridge import -i backup.json
```

---

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=src/memorybridge

# 运行特定测试
pytest tests/test_memory.py -v
```

---

## 🔧 配置

### 自定义数据库路径

编辑 `~/.memorybridge/config.yaml`:

```yaml
storage:
  sqlite:
    db_path: /path/to/custom/db.db
```

### 环境变量

```bash
export MEMORYBRIDGE_DB_PATH=/path/to/db.db
```

---

## ❓ 常见问题

### Q: 数据存在哪里？

A: 默认在 `~/.memorybridge/memories.db`

### Q: 如何备份数据？

A: 使用 `memorybridge export` 或直接复制 `.db` 文件

### Q: 支持中文吗？

A: 完全支持！所有内容都使用 UTF-8 编码

### Q: 如何清空所有数据？

A: 删除 `~/.memorybridge/memories.db` 文件

---

## 📚 下一步

- 查看 [API 文档](api.md) 了解编程接口
- 查看 [CLI 指南](cli.md) 了解所有命令
- 查看 [部署指南](deployment.md) 了解生产环境配置

---

**Happy Memory Management!** 🧠✨
