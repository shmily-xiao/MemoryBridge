---
name: memorybridge
description: Memory as a Service - 跨 Agent 记忆共享平台。提供记忆的增删查改、搜索、导出导入等功能。
---

# MemoryBridge Skill

MemoryBridge 是一个统一的记忆管理平台，支持跨 Agent 记忆共享。

## 功能特性

- 🔄 **跨 Agent 共享**: OpenClaw、Claude Code 等 Agent 共享同一记忆库
- 💾 **持久化存储**: SQLite 本地存储，数据不丢失
- 🛠️ **9 个工具**: 完整的记忆增删查改功能
- 🚀 **即装即用**: 简单配置，无需额外依赖

## 工具列表

| 工具 | 功能 | 示例 |
|------|------|------|
| `memory_add` | 添加记忆 | `memory_add("内容", type="long_term")` |
| `memory_search` | 搜索记忆 | `memory_search("Python")` |
| `memory_list` | 列出记忆 | `memory_list(limit=20)` |
| `memory_get` | 获取详情 | `memory_get("memory_id")` |
| `memory_update` | 更新记忆 | `memory_update("id", content="新")` |
| `memory_delete` | 删除记忆 | `memory_delete("id")` |
| `memory_export` | 导出记忆 | `memory_export(output="backup.json")` |
| `memory_import` | 导入记忆 | `memory_import(input="backup.json")` |
| `memory_status` | 查看状态 | `memory_status()` |

## 使用示例

### 添加记忆

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

### 搜索记忆

```python
# 基本搜索
memory_search("Python")

# 限制结果数量
memory_search("编程", limit=5)

# 按类型过滤
memory_search("记忆", type="long_term")
```

### 列出记忆

```python
# 列出前 20 条
memory_list()

# 列出所有
memory_list(limit=100)

# 仅 Session 记忆
memory_list(type="session")
```

## 参数说明

### memory_add

- `content` (str, 必填): 记忆内容
- `type` (str, 可选): 记忆类型 `session` 或 `long_term`，默认 `long_term`
- `priority` (str, 可选): 优先级 `p0`/`p1`/`p2`/`p3`，默认 `p1`
- `tags` (str, 可选): 标签，逗号分隔

### memory_search

- `query` (str, 必填): 搜索关键词
- `limit` (int, 可选): 返回数量，默认 10
- `type` (str, 可选): 类型过滤 `session` 或 `long_term`

## 记忆类型

- `session`: Session 级短期记忆（会话内有效）
- `long_term`: 长期记忆（持久化存储）

## 优先级

- `p0`: 最高 - 用户偏好、安全相关
- `p1`: 高 - 知识点、任务历史
- `p2`: 中 - 对话摘要
- `p3`: 低 - 临时上下文

## 跨 Agent 共享

多个 Agent 配置相同的数据库路径即可共享记忆：

```json
{
  "skills": {
    "entries": {
      "memorybridge": {
        "db_path": "~/.memorybridge/memories.db"
      }
    }
  }
}
```

## 故障排查

### Skill 未加载

检查 OpenClaw 日志：
```bash
openclaw logs --tail 50 | grep memorybridge
```

### 工具不可用

验证 Skill 路径：
```bash
ls -la ~/.openclaw/workspace/skills/memorybridge/
```

应该包含：
- `SKILL.md`
- `tools.py`

## 更多文档

- [完整 API 文档](https://github.com/shmily/memorybridge/blob/main/docs/skill-integration.md)
- [快速安装指南](https://github.com/shmily/memorybridge/blob/main/docs/skill-setup.md)
- [项目 README](https://github.com/shmily/memorybridge)
