#!/bin/bash

# 运行测试
pytest tests/ -v --cov=src/memorybridge --cov-report=term-missing
