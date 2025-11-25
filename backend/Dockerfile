# ----------------------------------------------------
# 修正后的 Backend Dockerfile (解决所有构建和启动问题)
# ----------------------------------------------------
# 使用基于 Debian 的镜像
FROM python:3.12.8-slim-bullseye

# 安装编译依赖，解决pydantic-core编译问题
RUN apt-get update && apt-get install -y gcc rustc cargo && apt-get clean && rm -rf /var/lib/apt/lists/*

# 设置pip超时时间，解决Railway网络问题
ENV PIP_TIMEOUT=1000
ENV PIP_EXTRA_INDEX_URL=https://pypi.org/simple/

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

# 优化pip安装，分步安装避免一次性大包安装超时
RUN pip install --no-cache-dir wheel setuptools
RUN pip install --no-cache-dir pydantic==2.8.2 fastapi
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