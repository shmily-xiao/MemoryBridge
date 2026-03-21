# MemoryBridge

**跨 Agent 记忆共享平台** - Memory as a Service + CLI + Knowledge Graph

## 🎯 项目愿景

让用户在不同 AI Agent 之间自由切换，同时保持记忆的持久化和连续性。

> "记忆不应该被锁定在单个 Agent 中。用户应该像切换应用一样切换 Agent，而记忆始终跟随。"

## ✨ 核心特性

- **🔀 跨 Agent 共享**: 支持 OpenClaw、Claude Code 等主流 Agent 平台
- **💾 持久化存储**: SQLite 本地存储，数据不丢失
- **🧠 记忆分层**: Session 级 + 中长期记忆
- **🕸️ 知识图谱**: NetworkX 图结构，支持实体关系管理
- **🔍 语义搜索**: 支持关键词搜索和向量搜索
- **📦 灵活导出**: JSON 格式导出导入，支持备份和迁移
- **🎨 可视化**: 知识图谱交互式可视化
- **🛠️ Skill 集成**: OpenClaw Skill 支持，9 个工具即装即用

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
cd ~/.openclaw/workspace/projects/memorybridge

# 安装依赖
pip3 install -e . --break-system-packages
```

### CLI 基本使用

```bash
# 添加记忆
memorybridge add "Python 是一种编程语言" --type long_term --priority p1 --tags "python,language"

# 搜索记忆
memorybridge search "Python"

# 列出所有记忆
memorybridge list

# 查看记忆详情
memorybridge get <memory_id>

# 更新记忆
memorybridge update <memory_id> --content "新内容" --tags "new,updated"

# 删除记忆
memorybridge delete <memory_id>

# 导出记忆
memorybridge export -o backup.json

# 导入记忆
memorybridge import -i backup.json

# 查看状态
memorybridge status
```

### OpenClaw Skill 集成

**1. 配置 openclaw.json**:

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

**2. 重启 Gateway**:

```bash
openclaw gateway restart
```

**3. 在对话中使用**:

```
帮我记住 Python 是一种编程语言
搜索关于 Python 的记忆
查看所有记忆
```

**详细文档**: [Skill 集成指南](docs/skill-integration.md)

## 📚 文档

- [快速开始](docs/quickstart.md)
- [Skill 集成指南](docs/skill-integration.md) ⭐ **NEW**
- [API 文档](docs/api.md)
- [CLI 使用指南](docs/cli.md)
- [部署指南](docs/deployment.md)
- [示例代码](docs/examples/)

## 🛠️ 技术栈

- **语言**: Python 3.10+
- **CLI 框架**: Typer
- **存储**: SQLite (主存储), MongoDB (可选), OSS (备份)
- **图谱**: NetworkX + SQLite 持久化
- **可视化**: PyVis
- **测试**: pytest

## 📋 开发计划

- [x] Phase 1: 核心功能 (Memory Service + CLI)
- [ ] Phase 2: 知识图谱 + 持久化
- [ ] Phase 3: MongoDB + OSS 存储
- [ ] Phase 4: Agent 集成
- [ ] Phase 5: 高级功能 (向量搜索)
- [ ] Phase 6: 生产就绪

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

## 📄 许可证

MIT License

## 👥 作者

- shmily

---

**Status**: 🚧 Development in Progress (v0.1.0)
