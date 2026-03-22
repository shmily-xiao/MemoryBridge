#!/usr/bin/env python3
"""
基准测试运行器

一键运行所有性能基准测试并生成报告
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_benchmarks(test_type: str = "all", output_format: str = "json"):
    """运行基准测试"""
    print(f"🚀 运行基准测试 (类型：{test_type})")
    print("=" * 60)
    
    # 构建 pytest 命令
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/benchmarks/",
        "-v",
        "--tb=short",
        f"--cov=src/memorybridge",
    ]
    
    if test_type != "all":
        cmd.append(f"test_{test_type}_benchmark.py")
    
    # 运行测试
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 输出结果
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # 生成报告
    if output_format in ("json", "all"):
        generate_report(result.stdout, format="json")
    if output_format in ("md", "all"):
        generate_report(result.stdout, format="markdown")
    
    return result.returncode


def generate_report(output: str, format: str = "json"):
    """生成基准测试报告"""
    results_dir = Path("benchmark_results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        "timestamp": timestamp,
        "test_output": output,
        "summary": {
            "passed": output.count("PASSED"),
            "failed": output.count("FAILED"),
        }
    }
    
    if format == "json":
        report_path = results_dir / f"benchmark_report_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n📊 JSON 报告已生成：{report_path}")
    
    elif format == "markdown":
        report_path = results_dir / f"benchmark_report_{timestamp}.md"
        with open(report_path, "w") as f:
            f.write(f"# MemoryBridge 性能基准测试报告\n\n")
            f.write(f"**运行时间**: {timestamp}\n\n")
            f.write(f"## 测试结果\n\n```\n{output}\n```\n")
        print(f"\n📊 Markdown 报告已生成：{report_path}")


def main():
    parser = argparse.ArgumentParser(description="运行性能基准测试")
    parser.add_argument(
        "--test",
        type=str,
        default="all",
        choices=["all", "storage", "readwrite", "concurrent"],
        help="测试类型"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="json",
        choices=["json", "md", "all"],
        help="报告格式"
    )
    
    args = parser.parse_args()
    sys.exit(run_benchmarks(args.test, args.format))


if __name__ == "__main__":
    main()
