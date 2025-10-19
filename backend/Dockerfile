# ----------------------------------------------------
# 修正后的 Backend Dockerfile (解决所有构建和启动问题)
# ----------------------------------------------------
# 使用基于 Debian 的镜像
FROM python:3.11-slim-bullseye

# 1. 安装构建工具和系统依赖
# build-essential 用于编译 pydantic-core 等 C 扩展
# libpq-dev 包含了编译 asyncpg 所需的头文件
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 2. 设置工作目录
WORKDIR /app

# 3. 复制并安装Python依赖
# 假设您已将所有依赖导出到 requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制应用代码
COPY . .

# 5. 定义启动命令 (修复了 $PORT 解析问题，并确保变量解析)
# 使用 /bin/sh -c 确保 $PORT 和 $DATABASE_URL 等环境变量能被正确解析
CMD ["/bin/sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port $PORT"]