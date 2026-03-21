# MemoryBridge OpenClaw Skill 集成指南

**版本**: v0.1.0  
**最后更新**: 2026-03-21

---

## 📦 概述

MemoryBridge OpenClaw Skill 是一个为 OpenClaw Agent 提供的记忆管理工具集，通过 Skill 工具接口实现跨 Agent 记忆共享。

### 核心价值

- 🔄 **跨 Agent 共享**: OpenClaw、Claude Code 等 Agent 共享同一记忆库
- 💾 **持久化存储**: SQLite 本地存储，数据不丢失
- 🛠️ **9 个工具**: 完整的记忆增删查改功能
- 🚀 **即装即用**: 简单配置，无需额外依赖

---

## 🚀 快速开始

### 1. 安装 MemoryBridge Python 包

```bash
cd ~/.openclaw/workspace/projects/memorybridge
pip3 install -e . --break-system-packages
```

### 2. 配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "skills": {
    "entries": {
      "memorybridge": {
        "enabled": true,
        "db_path": "~/.memorybridge/memories.db"
      }
    }
  }
}
```

### 3. 重启 Gateway

```bash
openclaw gateway restart
```

### 4. 验证安装

在 OpenClaw 中询问：
```
帮我记住 Python 是一种编程语言
```

---

## 🛠️ 工具列表

### 工具总览

| 工具 | 功能 | 必填参数 | 可选参数 |
|------|------|---------|---------|
| `memory_add` | 添加记忆 | content | type, priority, tags, db_path |
| `memory_search` | 搜索记忆 | query | limit, type, db_path |
| `memory_list` | 列出记忆 | - | limit, type, db_path |
| `memory_get` | 获取详情 | memory_id | db_path |
| `memory_update` | 更新记忆 | memory_id | content, tags, db_path |
| `memory_delete` | 删除记忆 | memory_id | db_path |
| `memory_export` | 导出记忆 | - | output, db_path |
| `memory_import` | 导入记忆 | input | db_path |
| `memory_status` | 查看状态 | - | db_path |

---

## 📖 详细使用指南

### memory_add - 添加记忆

**功能**: 添加一条新记忆

**参数**:
- `content` (str, 必填): 记忆内容
- `type` (str, 可选): 记忆类型 `session` 或 `long_term`，默认 `long_term`
- `priority` (str, 可选): 优先级 `p0`/`p1`/`p2`/`p3`，默认 `p1`
- `tags` (str, 可选): 标签，逗号分隔
- `db_path` (str, 可选): 数据库路径

**示例**:

```python
# 简单用法
memory_add("Python 是一种编程语言")

# 完整参数
memory_add(
    content="Agent Memory 分为四层架构",
    type="long_term",
    priority="p1",
    tags="ai,memory,architecture"
)

# Session 记忆
memory_add(
    content="当前任务：开发 MemoryBridge",
    type="session",
    priority="p0",
    tags="task,development"
)
```

**返回**:
```json
{
  "success": true,
  "memory": {
    "id": "f7037272-147d-4530-bd96-c5976642c798",
    "content": "Python 是一种编程语言",
    "memory_type": "long_term",
    "priority": "p1",
    "metadata": {},
    "tags": ["python", "language"],
    "created_at": "2026-03-21T21:00:00",
    "updated_at": null,
    "embedding": null
  },
  "message": "记忆添加成功：f7037272"
}
```

---

### memory_search - 搜索记忆

**功能**: 关键词搜索记忆

**参数**:
- `query` (str, 必填): 搜索关键词
- `limit` (int, 可选): 返回数量，默认 10
- `type` (str, 可选): 类型过滤 `session` 或 `long_term`
- `db_path` (str, 可选): 数据库路径

**示例**:

```python
# 基本搜索
memory_search("Python")

# 限制结果数量
memory_search("编程", limit=5)

# 按类型过滤
memory_search("记忆", type="long_term")
```

**返回**:
```json
{
  "success": true,
  "count": 1,
  "memories": [
    {
      "id": "f7037272-...",
      "content": "Python 是一种编程语言",
      "memory_type": "long_term",
      "priority": "p1",
      "tags": ["python", "language"]
    }
  ]
}
```

---

### memory_list - 列出记忆

**功能**: 列出所有记忆

**参数**:
- `limit` (int, 可选): 返回数量，默认 20
- `type` (str, 可选): 类型过滤
- `db_path` (str, 可选): 数据库路径

**示例**:

```python
# 列出前 20 条
memory_list()

# 列出所有
memory_list(limit=100)

# 仅 Session 记忆
memory_list(type="session")
```

---

### memory_get - 获取记忆详情

**功能**: 获取单条记忆的完整信息

**参数**:
- `memory_id` (str, 必填): 记忆 ID

**示例**:

```python
memory_get("f7037272-147d-4530-bd96-c5976642c798")
```

**返回**:
```json
{
  "success": true,
  "memory": {
    "id": "f7037272-...",
    "content": "Python 是一种编程语言",
    "memory_type": "long_term",
    "priority": "p1",
    "metadata": {},
    "tags": ["python", "language"],
    "created_at": "2026-03-21T21:00:00",
    "updated_at": null
  }
}
```

---

### memory_update - 更新记忆

**功能**: 更新记忆内容或标签

**参数**:
- `memory_id` (str, 必填): 记忆 ID
- `content` (str, 可选): 新内容
- `tags` (str, 可选): 新标签，逗号分隔

**示例**:

```python
# 更新内容
memory_update("memory_id", content="新内容")

# 更新标签
memory_update("memory_id", tags="new,updated")

# 同时更新
memory_update("memory_id", content="新内容", tags="new,updated")
```

---

### memory_delete - 删除记忆

**功能**: 删除指定记忆

**参数**:
- `memory_id` (str, 必填): 记忆 ID

**示例**:

```python
memory_delete("f7037272-147d-4530-bd96-c5976642c798")
```

**返回**:
```json
{
  "success": true,
  "message": "记忆已删除：f7037272"
}
```

---

### memory_export - 导出记忆

**功能**: 导出记忆到 JSON 文件

**参数**:
- `output` (str, 可选): 输出文件路径（不提供则返回 JSON 字符串）
- `db_path` (str, 可选): 数据库路径

**示例**:

```python
# 导出到文件
memory_export(output="backup.json")

# 返回 JSON 字符串
memory_export()
```

**返回**:
```json
{
  "success": true,
  "file": "backup.json",
  "message": "已导出到：backup.json"
}
```

---

### memory_import - 导入记忆

**功能**: 从 JSON 文件导入记忆

**参数**:
- `input` (str, 必填): 输入文件路径

**示例**:

```python
memory_import(input="backup.json")
```

**返回**:
```json
{
  "success": true,
  "count": 3,
  "message": "成功导入 3 条记忆"
}
```

---

### memory_status - 查看系统状态

**功能**: 查看记忆库统计信息

**参数**:
- `db_path` (str, 可选): 数据库路径

**示例**:

```python
memory_status()
```

**返回**:
```json
{
  "success": true,
  "total": 10,
  "session_count": 3,
  "long_term_count": 7,
  "db_path": "/Users/shmily/.memorybridge/memories.db"
}
```

---

## 💡 使用场景

### 场景 1: 学习知识管理

```python
# 添加知识点
memory_add("Agent Memory 分为四层：工作记忆、对话记忆、任务记忆、长期记忆", 
          type="long_term", 
          priority="p1", 
          tags="ai,memory,architecture")

# 搜索相关知识
memory_search("Memory")
```

### 场景 2: 任务管理

```python
# 添加任务
memory_add("完成 MemoryBridge Phase 1 开发", 
          type="session", 
          priority="p0", 
          tags="task,development")

# 更新任务状态
memory_update("task_id", content="✅ 完成 MemoryBridge Phase 1 开发")

# 搜索任务
memory_search("task", type="session")
```

### 场景 3: 备份和迁移

```python
# 定期备份
memory_export(output="backup-20260321.json")

# 迁移到新机器
memory_import(input="backup-20260321.json")
```

### 场景 4: 跨 Agent 共享

```python
# OpenClaw 中添加
memory_add("我喜欢用 Python 开发", tags="preference")

# Claude Code 中读取（共享同一数据库）
memory_search("Python")  # 能找到 OpenClaw 中添加的记忆 ✅
```

---

## ⚙️ 配置选项

### 自定义数据库路径

```json
{
  "skills": {
    "entries": {
      "memorybridge": {
        "enabled": true,
        "db_path": "/path/to/custom/memories.db"
      }
    }
  }
}
```

### 多 Agent 共享配置

多个 Agent 配置相同的 `db_path` 即可共享记忆：

```json
// Agent 1 (OpenClaw)
{
  "skills": {
    "entries": {
      "memorybridge": {
        "db_path": "/shared/memories.db"
      }
    }
  }
}

// Agent 2 (Claude Code)
{
  "skills": {
    "entries": {
      "memorybridge": {
        "db_path": "/shared/memories.db"
      }
    }
  }
}
```

---

## 🐛 故障排查

### Skill 未加载

**检查日志**:
```bash
openclaw logs --tail 50 | grep memorybridge
```

**验证 Skill 路径**:
```bash
ls -la ~/.openclaw/workspace/skills/memorybridge/
```

应该包含：
- `SKILL.md`
- `tools.py`

### 工具不可用

**测试工具导入**:
```bash
cd ~/.openclaw/workspace/projects/memorybridge
python3 -c "from src.memorybridge.skill_tools import memory_add; print('OK')"
```

### 数据库错误

**检查数据库文件**:
```bash
ls -la ~/.memorybridge/memories.db
```

**重建数据库**:
```bash
rm ~/.memorybridge/memories.db
openclaw gateway restart
```

---

## 📚 API 参考

### MemoryType 枚举

- `session`: Session 级短期记忆
- `long_term`: 长期记忆

### MemoryPriority 枚举

- `p0`: 最高 - 用户偏好、安全相关
- `p1`: 高 - 知识点、任务历史
- `p2`: 中 - 对话摘要
- `p3`: 低 - 临时上下文

### 记忆数据结构

```json
{
  "id": "uuid",
  "content": "记忆内容",
  "memory_type": "session|long_term",
  "priority": "p0|p1|p2|p3",
  "metadata": {},
  "tags": ["tag1", "tag2"],
  "created_at": "ISO8601",
  "updated_at": "ISO8601|null",
  "embedding": null
}
```

---

## 🔗 相关文档

- [项目 README](../README.md)
- [快速开始](quickstart.md)
- [CLI 使用指南](cli.md)
- [API 文档](api.md)

---

**Happy Memory Management!** 🧠✨
