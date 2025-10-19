# ----------------------------------------------------
# 最终版 Backend Dockerfile (解决系统依赖和端口问题)
# ----------------------------------------------------
# 使用基于 Debian 的镜像 (推荐使用 -slim-bullseye 或 bookworm)
FROM python:3.11-slim-bullseye

# 4. 解决 asyncpg 编译问题：安装构建工具和 libpq-dev
# libpq-dev 包含了编译 asyncpg 所需的头文件和开发库
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 5. 设置工作目录
WORKDIR /app

# 6. 复制并安装Python依赖
# 假设您已将所有依赖导出到 requirements.txt
# 注意：这里我们假设您只使用 requirements.txt，如果您的依赖拆分成 core，请相应调整
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. 复制应用代码
# 我们跳过非root用户创建和切换，以简化部署。Railway 容器默认使用 root 或 entrypoint user。
COPY . .

# 8. 修复启动命令（关键修复！）
# 必须使用 $PORT 环境变量，并且通过 /bin/sh -c 确保变量被正确解析。
CMD ["/bin/sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port $PORT"]

# 9. EXPOSE 是可选的，但如果需要，应该使用 $PORT 
# 保持 EXPOSE 8000 也没问题，但 Railway 主要依赖 $PORT 启动