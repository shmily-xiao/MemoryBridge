# MemoryBridge Skill 快速安装

**3 分钟完成安装，立即开始使用！**

---

## 🚀 一键安装（推荐）

```bash
cd ~/.openclaw/workspace/projects/memorybridge
bash install-skill.sh
```

安装脚本会自动：
1. ✅ 安装 Python 包
2. ✅ 创建 Skill 目录
3. ✅ 复制 Skill 文件
4. ✅ 提示配置 openclaw.json

---

## 📋 手动安装

### 步骤 1: 安装 Python 包

```bash
cd ~/.openclaw/workspace/projects/memorybridge
pip3 install -e . --break-system-packages
```

### 步骤 2: 复制 Skill 文件

```bash
mkdir -p ~/.openclaw/workspace/skills/memorybridge
cp -r skills/memorybridge/* ~/.openclaw/workspace/skills/memorybridge/
```

### 步骤 3: 配置 openclaw.json

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

### 步骤 4: 重启 Gateway

```bash
openclaw gateway restart
```

---

## ✅ 验证安装

在 OpenClaw 中询问：

```
帮我记住 Python 是一种编程语言
```

或：

```
搜索关于 Python 的记忆
```

---

## 🛠️ 可用工具（9 个）

| 工具 | 功能 | 示例 |
|------|------|------|
| `memory_add` | 添加记忆 | `memory_add("内容")` |
| `memory_search` | 搜索记忆 | `memory_search("Python")` |
| `memory_list` | 列出记忆 | `memory_list()` |
| `memory_get` | 获取详情 | `memory_get("id")` |
| `memory_update` | 更新记忆 | `memory_update("id", content="新")` |
| `memory_delete` | 删除记忆 | `memory_delete("id")` |
| `memory_export` | 导出记忆 | `memory_export(output="backup.json")` |
| `memory_import` | 导入记忆 | `memory_import(input="backup.json")` |
| `memory_status` | 查看状态 | `memory_status()` |

---

## 💡 使用示例

### 添加记忆

```
帮我记住 Python 是一种编程语言
```

### 搜索记忆

```
搜索关于 Python 的记忆
```

### 查看所有记忆

```
查看所有记忆
```

### 备份记忆

```
备份所有记忆
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

应该包含：
- `SKILL.md`
- `tools.py`

### 工具不可用

```bash
# 测试工具导入
cd ~/.openclaw/workspace/projects/memorybridge
python3 -c "from skills.memorybridge.tools import memory_add; print('OK')"
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

- [完整 Skill 文档](skill-integration.md)
- [API 参考](../docs/skill-integration.md)
- [快速开始](../docs/quickstart.md)
- [项目 README](../README.md)

---

## 🎯 跨 Agent 共享

配置相同的数据库路径，多个 Agent 即可共享记忆：

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

---

**安装完成，开始使用吧！** 🚀
