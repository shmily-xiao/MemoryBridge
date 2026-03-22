# MemoryBridge Dockerfile
# 多阶段构建，生产就绪

# Stage 1: 构建环境
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml .
COPY src/ ./src/

# 安装依赖
RUN pip install --no-cache-dir --user -e ".[all]"

# Stage 2: 生产环境
FROM python:3.11-slim as production

WORKDIR /app

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash memorybridge

# 从构建阶段复制
COPY --from=builder /root/.local /home/memorybridge/.local
COPY --from=builder /app/src ./src
COPY --from=builder /app/pyproject.toml .

# 设置环境变量
ENV PATH=/home/memorybridge/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# 切换到非 root 用户
USER memorybridge

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "memorybridge.cli.main", "status"]
