# MemoryBridge Skill 安装和使用指南

**最后更新**: 2026-03-21  
**版本**: v0.1.0

---

## 🎯 快速开始（3 分钟安装）

### 步骤 1: 安装 Python 包

```bash
cd ~/.openclaw/workspace/projects/memorybridge
pip3 install -e . --break-system-packages
```

### 步骤 2: 配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`，添加：

```json
{
  "skills": {
    "entries": {
      "memorybridge": {
        "enabled": true
      }
    }
  }
}
```

### 步骤 3: 重启 Gateway

```bash
openclaw gateway restart
```

### 步骤 4: 验证安装

在 OpenClaw 中询问：
```
帮我记住 Python 是一种编程语言
```

---

## 🛠️ 可用工具（9 个）

### 记忆管理

| 工具 | 功能 | 示例 |
|------|------|------|
| `memory_add` | 添加记忆 | `memory_add("内容", type="long_term")` |
| `memory_search` | 搜索记忆 | `memory_search("Python")` |
| `memory_list` | 列出记忆 | `memory_list(limit=20)` |
| `memory_get` | 获取详情 | `memory_get("memory_id")` |
| `memory_update` | 更新记忆 | `memory_update("id", content="新")` |
| `memory_delete` | 删除记忆 | `memory_delete("id")` |

### 备份迁移

| 工具 | 功能 | 示例 |
|------|------|------|
| `memory_export` | 导出记忆 | `memory_export(output="backup.json")` |
| `memory_import` | 导入记忆 | `memory_import(input="backup.json")` |
| `memory_status` | 查看状态 | `memory_status()` |

---

## 💡 使用示例

### 添加记忆

```
用户：帮我记住 Python 是一种编程语言
AI: ✅ 记忆添加成功！ID: f7037272
```

### 搜索记忆

```
用户：搜索关于 Python 的记忆
AI: 📊 找到 1 条记忆:
    [1] Python 是一种编程语言
        类型：long_term | 优先级：p1
        标签：python, language
```

### 查看所有记忆

```
用户：查看所有记忆
AI: 📊 共 3 条记忆:
    [1] 当前任务：开发 MemoryBridge
    [2] Agent Memory 分为四层架构
    [3] Python 是一种编程语言
```

### 更新记忆

```
用户：把第一条记忆改成"已完成 MemoryBridge Phase 1"
AI: ✅ 记忆更新成功！
```

### 备份记忆

```
用户：备份所有记忆
AI: ✅ 已导出到：backup.json
```

---

## 📖 参数说明

### memory_add

- `content` (必填): 记忆内容
- `type` (可选): `session` 或 `long_term`，默认 `long_term`
- `priority` (可选): `p0`/`p1`/`p2`/`p3`，默认 `p1`
- `tags` (可选): 标签，逗号分隔

### memory_search

- `query` (必填): 搜索关键词
- `limit` (可选): 返回数量，默认 10
- `type` (可选): 类型过滤

### 其他工具

所有工具的详细参数请参考：[Skill 集成完整文档](skill-integration.md)

---

## 🔄 跨 Agent 共享

### 配置共享数据库

多个 Agent 配置相同的数据库路径：

```json
// OpenClaw
{
  "skills": {
    "entries": {
      "memorybridge": {
        "db_path": "~/.memorybridge/memories.db"
      }
    }
  }
}

// Claude Code (未来支持)
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

### 使用场景

```
1. OpenClaw: "记住我喜欢用 Python"
   → 保存到 ~/.memorybridge/memories.db

2. Claude Code: "我知道你喜欢用 Python"
   ← 从同一数据库读取 ✅
```

---

## 🐛 故障排查

### Skill 未加载

```bash
# 检查日志
openclaw logs --tail 50 | grep memorybridge

# 验证 Skill 文件
ls -la ~/.openclaw/workspace/skills/memorybridge/
```

### 工具不可用

```bash
# 测试工具导入
cd ~/.openclaw/workspace/projects/memorybridge
python3 -c "from src.memorybridge.skill_tools import memory_add; print('OK')"
```

### 数据库问题

```bash
# 查看数据库文件
ls -la ~/.memorybridge/memories.db

# 重建数据库（会删除所有记忆！）
rm ~/.memorybridge/memories.db
openclaw gateway restart
```

---

## 📚 更多文档

- [Skill 集成完整文档](skill-integration.md) - 详细 API 和使用指南
- [快速开始](quickstart.md) - CLI 使用指南
- [项目 README](../README.md) - 项目概述

---

## 🎯 下一步

1. ✅ 安装 Skill
2. ✅ 测试基本功能
3. ✅ 开始使用记忆管理
4. ⏳ 配置跨 Agent 共享（等待其他 Agent 支持）

---

**有任何问题随时询问！** 🚀
