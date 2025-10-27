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
# 使用Railway专用的requirements文件（仅生产依赖）
COPY requirements-railway.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制应用代码
COPY . .

# 5. 创建启动脚本以运行数据库迁移
RUN echo '#!/bin/sh\n\
set -e\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting FastAPI server..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# 6. 定义启动命令
CMD ["/bin/sh", "-c", "exec /app/start.sh"]