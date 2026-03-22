# LangChain Memory 集成

MemoryBridge 提供 LangChain `BaseMemory` 接口实现，支持对话历史持久化和 RAG 上下文检索。

## 安装

```bash
pip install memorybridge langchain langchain-core
```

## 快速开始

### 基础使用

```python
from memorybridge.integrations import MemoryBridgeMemory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI

# 创建记忆实例
memory = MemoryBridgeMemory(
    backend="sqlite",  # 或 "mongodb"
    return_messages=True,
    max_memory_limit=100,
)

# 创建对话链
llm = OpenAI(temperature=0.7)
chain = ConversationChain(llm=llm, memory=memory)

# 开始对话
response = chain.run("你好，帮我写个 Python 脚本")
print(response)
```

### 配置 MongoDB 后端

```python
memory = MemoryBridgeMemory(
    backend="mongodb",
    mongo_uri="mongodb://localhost:27017",
    mongo_db="memorybridge",
    return_messages=True,
)
```

## 高级功能

### 知识图谱检索

```python
from memorybridge.integrations import MemoryBridgeMemory

memory = MemoryBridgeMemory(backend="mongodb")

# 获取带图谱上下文的对话历史
context = await memory.get_context_with_graph(
    query="Python",
    top_k=5,
    include_graph_entities=True,
)

print(context["messages"])
print(context["graph_entities"])
```

### RAG 上下文增强

```python
from langchain.chains import RetrievalQA
from memorybridge.integrations import MemoryBridgeMemory

# 创建记忆实例
memory = MemoryBridgeMemory(backend="mongodb")

# 获取检索器
retriever = memory.as_retriever(
    search_type="hybrid",  # 向量 + BM25
    search_kwargs={"k": 5},
)

# 创建 QA 链
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
)

result = qa_chain({"query": "什么是机器学习？"})
print(result["result"])
print(result["source_documents"])
```

### 对话历史管理

```python
# 获取对话历史
history = await memory.get_chat_history(limit=20)

# 清空历史
await memory.clear()

# 导出对话
json_data = await memory.export_session(format="json")
md_data = await memory.export_session(format="markdown")
```

## 配置选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `backend` | str | "sqlite" | 存储后端 |
| `db_path` | str | None | SQLite 数据库路径 |
| `mongo_uri` | str | None | MongoDB 连接字符串 |
| `mongo_db` | str | "memorybridge" | MongoDB 数据库名 |
| `return_messages` | bool | False | 返回 Message 对象 |
| `max_memory_limit` | int | 100 | 最大记忆数量 |
| `input_key` | str | None | 输入键名 |
| `output_key` | str | None | 输出键名 |

## 使用场景

### 场景 1: 长期对话记忆

```python
from langchain.agents import initialize_agent, Tool
from memorybridge.integrations import MemoryBridgeMemory

# 创建带记忆的 Agent
memory = MemoryBridgeMemory(
    backend="mongodb",
    max_memory_limit=1000,  # 保留更多历史
)

tools = [
    Tool(
        name="Search",
        func=search_function,
        description="搜索信息",
    ),
]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,  # 启用长期记忆
)

# 多轮对话会记住之前的内容
agent.run("我叫小明，记住我的名字")
agent.run("我叫什么名字？")  # 会回答"小明"
```

### 场景 2: 多会话管理

```python
# 为不同用户创建独立会话
user1_memory = MemoryBridgeMemory(
    session_id="user_001",
    backend="mongodb",
)

user2_memory = MemoryBridgeMemory(
    session_id="user_002",
    backend="mongodb",
)

# 每个用户有独立的对话历史
```

### 场景 3: 对话分析

```python
# 导出对话进行分析
import json

history = await memory.get_chat_history()

# 分析对话模式
user_messages = [m for m in history if m["role"] == "user"]
assistant_messages = [m for m in history if m["role"] == "assistant"]

print(f"用户消息数：{len(user_messages)}")
print(f"助手消息数：{len(assistant_messages)}")
```

## 故障排查

### 问题 1: 记忆未保存

```python
# 检查 backend 配置
print(memory.backend)

# 验证连接
await memory.storage.count()
```

### 问题 2: 检索结果不准确

```python
# 使用混合检索
retriever = memory.as_retriever(
    search_type="hybrid",
    search_kwargs={
        "k": 10,
        "alpha": 0.7,  # 向量权重 70%
    },
)
```

## 性能优化

```python
# 启用缓存
memory = MemoryBridgeMemory(
    backend="mongodb",
    enable_cache=True,
    cache_ttl=300,  # 5 分钟缓存
)

# 批量操作
await memory.batch_add([
    {"role": "user", "content": "消息 1"},
    {"role": "user", "content": "消息 2"},
])
```

---

**相关文档**:
- [CrewAI 集成](crewai.md)
- [LlamaIndex 集成](llamaindex.md)
- [向量搜索](../advanced/vector-search.md)
