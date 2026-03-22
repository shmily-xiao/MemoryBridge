# MemoryBridge 性能基准测试

## 快速开始

```bash
# 运行所有基准测试
python3 tests/benchmarks/run_benchmarks.py

# 运行特定测试
python3 tests/benchmarks/run_benchmarks.py --test storage
python3 tests/benchmarks/run_benchmarks.py --test readwrite
python3 tests/benchmarks/run_benchmarks.py --test concurrent

# 生成报告
python3 tests/benchmarks/run_benchmarks.py --format all
```

## 测试类型

### 1. 存储性能基准 (`test_storage_benchmark.py`)
- 单次写入性能
- 单次读取性能
- 搜索性能
- 列表查询性能
- 更新/删除性能

### 2. 读写性能基准 (`test_read_write_benchmark.py`)
- 批量写入
- 批量读取
- 混合负载

### 3. 并发负载基准 (`test_concurrent_benchmark.py`)
- 并发写入
- 并发读取
- 并发搜索

## 性能标准

| 操作类型 | 优秀 | 良好 | 及格 |
|---------|------|------|------|
| 单次写入 | >500 ops/sec | >200 ops/sec | >100 ops/sec |
| 单次读取 | >1000 ops/sec | >500 ops/sec | >200 ops/sec |
| 搜索 | >200 ops/sec | >100 ops/sec | >50 ops/sec |

## 输出报告

报告生成在 `./benchmark_results/` 目录：
- `benchmark_report_YYYYMMDD_HHMMSS.json` - JSON 格式
- `benchmark_report_YYYYMMDD_HHMMSS.md` - Markdown 格式
