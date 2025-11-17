#!/bin/bash

# ============================================
# 拆词鸭项目Railway部署脚本
# 用于正确配置Redis和PostgreSQL服务
# ============================================

set -e

echo "🚀 开始拆词鸭项目Railway部署..."

# 1. 检查Railway CLI是否安装
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI未安装，请先安装：npm install -g @railway/cli"
    exit 1
fi

# 2. 检查是否已登录
if ! railway whoami &> /dev/null; then
    echo "❌ 请先登录Railway：railway login"
    exit 1
fi

# 3. 创建PostgreSQL数据库服务
echo "📊 创建PostgreSQL数据库服务..."
railway add postgresql --name chaiword-postgres

# 4. 创建Redis缓存服务
echo "🔴 创建Redis缓存服务..."
railway add redis --name chaiword-redis

# 5. 等待服务创建完成
echo "⏳ 等待服务创建完成..."
sleep 30

# 6. 验证服务配置
echo "🔍 验证服务配置..."

# 检查PostgreSQL服务
postgres_env=$(railway variables get --service chaiword-postgres)
if echo "$postgres_env" | grep -q "DATABASE_URL"; then
    echo "✅ PostgreSQL服务配置正确"
else
    echo "❌ PostgreSQL服务配置异常"
    echo "$postgres_env"
fi

# 检查Redis服务
redis_env=$(railway variables get --service chaiword-redis)
if echo "$redis_env" | grep -q "REDIS_URL"; then
    echo "✅ Redis服务配置正确"
else
    echo "❌ Redis服务配置异常"
    echo "$redis_env"
    echo ""
    echo "💡 如果Redis服务显示DATABASE_URL，说明被错误识别为PostgreSQL"
    echo "   请在Railway控制台中删除并重新创建Redis服务"
fi

# 7. 设置应用环境变量
echo "🔧 设置应用环境变量..."
railway variables set DATABASE_URL="${{chaiword-postgres.DATABASE_URL}}"
railway variables set REDIS_URL="${{chaiword-redis.REDIS_URL}}"
railway variables set PORT=8000
railway variables set APP_ENV=production

# 8. 部署应用
echo "🚢 部署应用..."
railway up

echo "✅ 部署完成！"
echo ""
echo "📝 重要提醒："
echo "1. 如果Redis服务被错误识别为PostgreSQL，请："
echo "   - 删除错误的Redis服务"
echo "   - 重新添加Redis服务"
echo "   - 确保服务名称包含'redis'关键词"
echo ""
echo "2. 验证方法："
echo "   - Redis服务应该生成REDIS_URL变量"
echo "   - PostgreSQL服务应该生成DATABASE_URL变量"
echo "   - 不应该出现DATABASE_PUBLIC_URL变量在Redis服务中"