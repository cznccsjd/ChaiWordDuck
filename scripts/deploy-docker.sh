#!/bin/bash

# 拆词鸭项目Docker部署脚本
# 使用方法: ./deploy-docker.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
PROJECT_NAME="chaiwordduck"

echo "🚀 开始部署拆词鸭项目 (环境: $ENVIRONMENT)"

# 检查Docker和Docker Compose是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 清理旧的容器和网络
echo "🧹 清理旧的容器和网络..."
docker-compose -p $PROJECT_NAME down --remove-orphans || true

# 根据环境选择配置文件
case $ENVIRONMENT in
    "prod")
        echo "🏭 生产环境部署..."
        COMPOSE_FILE="docker-compose.fixed.yml"
        ENV_FILE="backend/.env.docker"

        # 检查必需的环境变量
        if [ ! -f "$ENV_FILE" ]; then
            echo "❌ 环境变量文件不存在: $ENV_FILE"
            echo "请先创建环境变量文件并设置必要的API密钥"
            exit 1
        fi

        # 构建并启动所有服务
        docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE --env-file $ENV_FILE up --build -d
        ;;

    "dev")
        echo "🔧 开发环境部署..."
        COMPOSE_FILE="docker-compose.dev.yml"

        # 仅启动数据库和Redis
        docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d

        echo "✅ 开发环境启动完成！"
        echo "📝 请在本地启动API服务："
        echo "   cd backend && pdm run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
        echo "📝 请在本地启动前端服务："
        echo "   cd frontend && npm run dev"
        exit 0
        ;;

    *)
        echo "❌ 未知环境: $ENVIRONMENT"
        echo "支持的环境: dev, prod"
        exit 1
        ;;
esac

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE ps

# 健康检查
echo "🏥 执行健康检查..."

# 检查数据库连接
echo "   检查数据库连接..."
for i in {1..30}; do
    if docker exec chaiword_db pg_isready -U postgres > /dev/null 2>&1; then
        echo "   ✅ 数据库连接正常"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ❌ 数据库连接失败"
        exit 1
    fi
    sleep 2
done

# 检查Redis连接
echo "   检查Redis连接..."
for i in {1..30}; do
    if docker exec chaiword_redis redis-cli ping > /dev/null 2>&1; then
        echo "   ✅ Redis连接正常"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ❌ Redis连接失败"
        exit 1
    fi
    sleep 2
done

# 检查API服务（生产环境）
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "   检查API服务..."
    for i in {1..60}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "   ✅ API服务正常"
            break
        fi
        if [ $i -eq 60 ]; then
            echo "   ❌ API服务启动失败"
            echo "📋 查看API服务日志:"
            docker logs chaiword_api
            exit 1
        fi
        sleep 2
    done
fi

echo ""
echo "🎉 部署完成！"
echo ""

if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🌐 服务访问地址:"
    echo "   - API服务: http://localhost:8000"
    echo "   - API文档: http://localhost:8000/docs"
    echo "   - 前端服务: http://localhost:3000"
    echo ""
    echo "📊 管理命令:"
    echo "   - 查看日志: docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE logs -f [service_name]"
    echo "   - 停止服务: docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE down"
    echo "   - 重启服务: docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE restart [service_name]"
fi

echo ""
echo "🔧 故障排除:"
echo "   - 查看容器状态: docker ps -a"
echo "   - 查看网络信息: docker network ls"
echo "   - 检查容器日志: docker logs [container_name]"
echo "   - 进入容器调试: docker exec -it [container_name] /bin/bash"