@echo off
REM 拆词鸭项目Docker部署脚本 (Windows版本)
REM 使用方法: deploy-docker.bat [dev|prod]

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev
set PROJECT_NAME=chaiwordduck

echo 🚀 开始部署拆词鸭项目 (环境: %ENVIRONMENT%)

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 清理旧的容器和网络
echo 🧹 清理旧的容器和网络...
docker-compose -p %PROJECT_NAME% down --remove-orphans >nul 2>&1

REM 根据环境选择配置文件
if "%ENVIRONMENT%"=="prod" (
    echo 🏭 生产环境部署...
    set COMPOSE_FILE=docker-compose.fixed.yml
    set ENV_FILE=backend\.env.docker

    REM 检查必需的环境变量文件
    if not exist "%ENV_FILE%" (
        echo ❌ 环境变量文件不存在: %ENV_FILE%
        echo 请先创建环境变量文件并设置必要的API密钥
        pause
        exit /b 1
    )

    REM 构建并启动所有服务
    docker-compose -p %PROJECT_NAME% -f %COMPOSE_FILE% --env-file %ENV_FILE% up --build -d
) else if "%ENVIRONMENT%"=="dev" (
    echo 🔧 开发环境部署...
    set COMPOSE_FILE=docker-compose.dev.yml

    REM 仅启动数据库和Redis
    docker-compose -p %PROJECT_NAME% -f %COMPOSE_FILE% up -d

    echo ✅ 开发环境启动完成！
    echo 📝 请在本地启动API服务：
    echo    cd backend ^&^& pdm run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    echo 📝 请在本地启动前端服务：
    echo    cd frontend ^&^& npm run dev
    pause
    exit /b 0
) else (
    echo ❌ 未知环境: %ENVIRONMENT%
    echo 支持的环境: dev, prod
    pause
    exit /b 1
)

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker-compose -p %PROJECT_NAME% -f %COMPOSE_FILE% ps

REM 健康检查
echo 🏥 执行健康检查...

REM 检查数据库连接
echo    检查数据库连接...
set /a count=0
:check_db
docker exec chaiword_db pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    set /a count+=1
    if !count! geq 30 (
        echo    ❌ 数据库连接失败
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto check_db
)
echo    ✅ 数据库连接正常

REM 检查Redis连接
echo    检查Redis连接...
set /a count=0
:check_redis
docker exec chaiword_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    set /a count+=1
    if !count! geq 30 (
        echo    ❌ Redis连接失败
        pause
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto check_redis
)
echo    ✅ Redis连接正常

REM 检查API服务（生产环境）
if "%ENVIRONMENT%"=="prod" (
    echo    检查API服务...
    set /a count=0
:check_api
    curl -f http://localhost:8000/health >nul 2>&1
    if errorlevel 1 (
        set /a count+=1
        if !count! geq 60 (
            echo    ❌ API服务启动失败
            echo 📋 查看API服务日志:
            docker logs chaiword_api
            pause
            exit /b 1
        )
        timeout /t 2 /nobreak >nul
        goto check_api
    )
    echo    ✅ API服务正常
)

echo.
echo 🎉 部署完成！
echo.

if "%ENVIRONMENT%"=="prod" (
    echo 🌐 服务访问地址:
    echo    - API服务: http://localhost:8000
    echo    - API文档: http://localhost:8000/docs
    echo    - 前端服务: http://localhost:3000
    echo.
    echo 📊 管理命令:
    echo    - 查看日志: docker-compose -p %PROJECT_NAME% -f %COMPOSE_FILE% logs -f [service_name]
    echo    - 停止服务: docker-compose -p %PROJECT_NAME% -f %COMPOSE_FILE% down
    echo    - 重启服务: docker-compose -p %PROJECT_NAME% -f %COMPOSE_FILE% restart [service_name]
)

echo.
echo 🔧 故障排除:
echo    - 查看容器状态: docker ps -a
echo    - 查看网络信息: docker network ls
echo    - 检查容器日志: docker logs [container_name]
echo    - 进入容器调试: docker exec -it [container_name] /bin/bash

pause