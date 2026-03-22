# MemoryBridge

**跨 Agent 记忆共享平台** - Memory as a Service

[![Version](https://img.shields.io/badge/version-0.7.0-blue.svg)](https://github.com/shmily-xiao/MemoryBridge/releases)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-134%20passed-brightgreen.svg)](tests/)

---

## 🎯 项目愿景

让用户在不同 AI Agent 之间自由切换，同时保持记忆的持久化和连续性。

> "记忆不应该被锁定在单个 Agent 中。用户应该像切换应用一样切换 Agent，而记忆始终跟随。"

---

## ✨ 核心特性

### 📦 完整的记忆生命周期管理

- **Context → Short-term → Long-term** 自动升级
- **重要性评分** 基于引用次数、用户指令、情感强度、时效性
- **时间维度追踪** 实体/关系的创建、更新、过期时间
- **知识图谱自动提取** 从对话中自动提取实体和关系

### 🔀 7 个 Agent 框架集成

| Agent 框架 | 集成类 | 状态 |
|-----------|--------|------|
| **OpenClaw** | skill_tools.py | ✅ |
| **LangChain** | MemoryBridgeMemory | ✅ |
| **CrewAI** | CrewAIMemory | ✅ |
| **Claude Code** | ClaudeCodeIntegration | ✅ |
| **AutoGen** | AutoGenMemory | ✅ |
| **LlamaIndex** | LlamaIndexMemory | ✅ |
| **Haystack** | HaystackDocumentStore | ✅ |

### 💾 5 种存储后端

| 存储后端 | 适用场景 | 状态 |
|---------|---------|------|
| **SQLite** | 本地存储，个人使用 | ✅ |
| **MongoDB** | 大规模数据，分布式 | ✅ |
| **Tiered Storage** | 自动分层（热/温/冷） | ✅ |
| **OSS Backup** | 阿里云云备份 | ✅ |
| **Vector Store** | 向量搜索 + BM25 混合检索 | ✅ |

### 🚀 生产就绪

- ✅ Docker 部署（MongoDB + MemoryBridge + Nginx）
- ✅ 性能监控（指标收集 + 健康检查）
- ✅ 缓存加速（LRU Cache + TTL）
- ✅ 性能基准测试（16,350 ops/sec 读取）
- ✅ 知识图谱可视化

---

## 📊 项目统计

| 指标 | 数量 |
|------|------|
| **测试用例** | 134+ 个 ✅ |
| **代码行数** | ~13,000 行 |
| **Python 文件** | 48+ 个 |
| **Agent 集成** | 7 个框架 |
| **存储后端** | 5 种方案 |
| **文档** | 完整 |

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/shmily-xiao/MemoryBridge.git
cd MemoryBridge

# 安装依赖
pip3 install -e . --break-system-packages

# 验证安装
memorybridge --version
```

### 2. 基础使用（CLI）

```bash
# 添加记忆
memorybridge add "Python 是一种编程语言" \
  --type long_term \
  --priority p1 \
  --tags "python,language"

# 搜索记忆
memorybridge search "Python"

# 列出所有记忆
memorybridge list

# 查看记忆详情
memorybridge get <memory_id>

# 更新记忆
memorybridge update <memory_id> --content "新内容"

# 删除记忆
memorybridge delete <memory_id>

# 导出记忆
memorybridge export -o backup.json

# 导入记忆
memorybridge import -i backup.json

# 查看状态
memorybridge status
```

### 3. 知识图谱

```bash
# 添加实体
memorybridge graph add-entity "Python" --type language

# 添加关系
memorybridge graph add-relation <entity_id1> uses <entity_id2>

# 查询关系
memorybridge graph query <entity_id>

# 查找路径（多跳推理）
memorybridge graph find-path <from_id> <to_id>

# 查看图谱统计
memorybridge graph stats

# 导出图谱
memorybridge graph export -o graph.graphml
```

### 4. OpenClaw Skill 集成

```bash
# 安装 Skill
cd MemoryBridge
bash install-skill.sh

# 重启 Gateway
openclaw gateway restart

# 在对话中使用
"帮我记住 Python 是一种编程语言"
"搜索关于 Python 的记忆"
"查看所有记忆"
```

### 5. Docker 部署

```bash
# 配置环境变量
cp .env.example .env
vi .env  # 修改密码等配置

# 启动服务
docker-compose up -d

# 验证部署
curl http://localhost:8000/health

# 查看日志
docker-compose logs -f
```

---

## 📚 文档目录

### 核心文档

- **[快速开始](docs/quickstart.md)** - 5 分钟上手指南
- **[CLI 使用指南](docs/cli.md)** - 完整 CLI 命令参考
- **[Skill 集成](docs/skill-integration.md)** - OpenClaw Skill 配置
- **[Docker 部署](docs/deployment-docker.md)** - 生产环境部署

### Agent 集成

- **[LangChain Memory](docs/integrations/langchain.md)** - LangChain 集成指南
- **[CrewAI Memory](docs/integrations/crewai.md)** - CrewAI 集成指南
- **[Claude Code](docs/integrations/claude-code.md)** - Claude Code 集成指南
- **[AutoGen Memory](docs/integrations/autogen.md)** - AutoGen 集成指南
- **[LlamaIndex Memory](docs/integrations/llamaindex.md)** - LlamaIndex 集成指南
- **[Haystack DocumentStore](docs/integrations/haystack.md)** - Haystack 集成指南

### 高级主题

- **[向量搜索](docs/advanced/vector-search.md)** - Ollama + BM25 混合检索
- **[知识图谱](docs/advanced/knowledge-graph.md)** - 实体关系管理
- **[记忆生命周期](docs/advanced/memory-lifecycle.md)** - Context → Long-term
- **[性能优化](docs/advanced/performance.md)** - 缓存 + 连接池
- **[监控系统](docs/advanced/monitoring.md)** - 指标收集 + 健康检查

---

## 🏗️ 项目架构

```
MemoryBridge/
├── src/memorybridge/          # Python 包
│   ├── core/                  # 核心模块
│   │   ├── memory.py          # Memory 数据模型
│   │   └── service.py         # MemoryService 接口
│   ├── storage/               # 存储后端 (5 种)
│   │   ├── sqlite.py          # SQLite 实现
│   │   ├── mongodb.py         # MongoDB 实现
│   │   ├── tiered_storage.py  # 分层存储
│   │   ├── oss_backup.py      # OSS 云备份
│   │   └── vector_store.py    # 向量存储
│   ├── cognitive/             # 认知模块 ⭐
│   │   ├── refiner.py         # 记忆提炼器
│   │   ├── graph_extractor.py # 图谱提取器
│   │   └── manager.py         # 记忆管理器
│   ├── graph/                 # 知识图谱
│   │   └── networkx_graph.py  # NetworkX 实现
│   ├── integrations/          # Agent 集成 (7 个)
│   │   ├── langchain_memory.py
│   │   ├── crewai_memory.py
│   │   ├── claude_code.py
│   │   ├── autogen_memory.py
│   │   ├── llamaindex_memory.py
│   │   └── haystack_docstore.py
│   ├── cli/                   # CLI 工具
│   │   ├── main.py            # 主 CLI
│   │   └── graph_cmds.py      # 图谱命令
│   ├── monitoring.py          # 监控系统 ⭐
│   ├── optimization.py        # 性能优化 ⭐
│   └── skill_tools.py         # OpenClaw Skill
├── tests/                     # 测试 (134+ 用例)
├── tests/benchmarks/          # 性能基准 ⭐
├── docs/                      # 文档
├── skills/memorybridge/       # OpenClaw Skill
├── Dockerfile                 # Docker 镜像
├── docker-compose.yml         # Docker 编排
├── pyproject.toml             # 项目配置
└── README.md                  # 本文件
```

---

## 🎯 使用场景

### 场景 1: 跨 Agent 记忆共享

```python
# 在 LangChain Agent 中使用
from memorybridge.integrations import MemoryBridgeMemory

memory = MemoryBridgeMemory(backend="mongodb")
chain = ConversationChain(llm=llm, memory=memory)

# 在 CrewAI 中使用
from memorybridge.integrations import CrewAIMemory

crew_memory = CrewAIMemory(crew_id="research_team")
# 多 Agent 共享记忆

# 在 AutoGen 中使用
from memorybridge.integrations import AutoGenMemory

autogen_memory = AutoGenMemory(conversation_id="conv_001")
# 对话持久化
```

### 场景 2: 知识图谱自动构建

```python
from memorybridge.cognitive import KnowledgeGraphExtractor

extractor = KnowledgeGraphExtractor()

# 从对话自动提取
await extractor.extract_from_memory("我用 Python 开发 MemoryBridge 项目")
# 自动提取实体：["我", "Python", "MemoryBridge"]
# 自动提取关系：[("我", "uses", "Python"), ("我", "develops", "MemoryBridge")]
```

### 场景 3: 记忆自动升级

```python
from memorybridge.cognitive import MemoryManager

manager = MemoryManager(short_storage, long_storage)

# 处理新记忆（自动评分 + 升级）
result = await manager.process_new_memory(
    content="重要知识点",
    user_instruction=True,  # 用户说"记住这个"
)
# 重要性评分 > 0.7 自动升级到长期记忆
```

### 场景 4: 向量搜索 + 语义检索

```python
from memorybridge.storage.vector_store import VectorStore

store = VectorStore(ollama_model="nomic-embed-text")
await store.initialize()

# 混合检索（向量 70% + BM25 30%）
results = await store.search("人工智能", limit=5, use_hybrid=True)
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行性能基准
python3 tests/benchmarks/run_benchmarks.py

# 生成覆盖率报告
pytest tests/ --cov=src/memorybridge --cov-report=html
```

**测试统计**:
- 134+ 测试用例
- 全部通过 ✅
- 覆盖率 80%+ (核心模块)

---

## 📈 性能基准

| 操作类型 | 性能 | 评级 |
|---------|------|------|
| 单次写入 | 2,911 ops/sec | ⭐⭐⭐⭐⭐ |
| 单次读取 | 16,350 ops/sec | ⭐⭐⭐⭐⭐ |
| 搜索性能 | 11,017 ops/sec | ⭐⭐⭐⭐⭐ |
| 向量检索 | ~500 ops/sec | ⭐⭐⭐⭐ |

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 👥 作者

- **shmily** - [GitHub](https://github.com/shmily-xiao)

---

## 🎉 致谢

感谢以下开源项目：

- [NetworkX](https://networkx.org/) - 知识图谱
- [Ollama](https://ollama.ai/) - 向量嵌入
- [Typer](https://typer.tiangolo.com/) - CLI 框架
- [Pytest](https://docs.pytest.org/) - 测试框架
- [LangChain](https://python.langchain.com/) - Agent 集成
- [LlamaIndex](https://www.llamaindex.ai/) - RAG 集成

---

## 📞 联系方式

- **项目地址**: https://github.com/shmily-xiao/MemoryBridge
- **问题反馈**: https://github.com/shmily-xiao/MemoryBridge/issues
- **讨论区**: https://github.com/shmily-xiao/MemoryBridge/discussions

---

**Made with ❤️ by shmily**

*最后更新：2026-03-22*
