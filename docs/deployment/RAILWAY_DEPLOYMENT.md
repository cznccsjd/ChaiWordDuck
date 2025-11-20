# 拆词鸭 (ChaiWord Duck) Railway 部署指南 🚀

这份指南旨在帮助开发者以最"丝滑"的方式，将拆词鸭后端 API 部署到 Railway 平台。我们采用 **Docker** 方案，确保环境的一致性和部署的稳定性。

## 📋 核心架构

*   **构建方式**: Dockerfile (基于 `python:3.11-slim-bullseye`)
*   **数据库**: PostgreSQL (Railway 自动提供)
*   **缓存**: Redis (Railway 自动提供)
*   **依赖管理**: `requirements-railway.txt` (仅包含生产环境依赖)

---

## 🛠️ 部署前检查清单

在开始之前，请确保你的代码库已经准备就绪：

1.  **代码同步**: 确保本地代码已推送到 GitHub 的 `develop` 或 `main` 分支。
2.  **关键文件确认**:
    *   ✅ `railway.json`: 定义了服务结构和构建源。
    *   ✅ `railway.toml`: 配置了构建器为 `DOCKERFILE`。
    *   ✅ `backend/Dockerfile`: 包含了构建和启动逻辑。
    *   ✅ `backend/requirements-railway.txt`: 锁定了生产环境依赖。

---

## 🚢 极速部署步骤 (3分钟搞定)

### 第一步：连接 GitHub

1.  登录 [Railway 控制台](https://railway.app/)。
2.  点击 **"New Project"** -> **"Deploy from GitHub repo"**。
3.  选择 **`ChaiWordDuck`** 仓库。
4.  点击 **"Deploy Now"**。

### 第二步：添加数据库和缓存

Railway 会自动解析 `railway.json`，但为了确保万无一失，请检查服务视图：

1.  你应该能看到 **`postgres`** 和 **`redis`** 服务自动被创建（如果没有，请手动添加 Database -> PostgreSQL 和 Database -> Redis）。
2.  **关键**: 确保 API 服务连接到了这两个数据库。Railway 的变量注入通常是自动的，但我们需要手动确认环境变量。

### 第三步：配置环境变量 (关键!)

进入 API 服务的 **"Variables"** 选项卡，添加以下必须的变量：

| 变量名 | 示例值/说明 |
| :--- | :--- |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `JWT_SECRET_KEY` | 生成一个长随机字符串 (至少32位) |
| `AI_PRIMARY_PROVIDER` | `gemini` 或 `openai` |
| `GEMINI_API_KEY` | 你的 Google Gemini API Key |
| `OPENAI_API_KEY` | 你的 OpenAI API Key (如果用作备用) |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` (前端域名) |

> **注意**: `DATABASE_URL`, `REDIS_URL`, `PORT` 这些变量 Railway 会自动注入，**不需要**手动添加。

### 第四步：坐等变绿 🟢

1.  配置完变量后，Railway 会自动触发重新部署。
2.  点击 API 服务的 **"Deployments"** 标签，观察构建日志。
3.  看到 `Starting FastAPI server...` 字样，说明部署成功！

---

## 🔍 验证部署

部署成功后，Railway 会提供一个公网域名（例如 `chaiword-duck-production.up.railway.app`）。

1.  **健康检查**:
    访问 `https://<你的域名>/api/v1/health/database`
    *   预期返回: `{"status":"healthy", ...}`

2.  **API 文档**:
    访问 `https://<你的域名>/docs`
    *   预期看到 Swagger UI 界面。

---

## 🚨 常见问题急救箱

**Q: 部署失败，日志显示 `alembic: command not found`?**
A: 检查 `backend/Dockerfile` 是否正确复制了依赖，并且 `requirements-railway.txt` 中包含 `alembic`。我们的 Dockerfile 已经内置了启动脚本 `start.sh` 来处理这个问题。

**Q: 数据库连接报错 `scheme not supported: postgres`?**
A: 我们的代码 (`backend/app/core/config.py`) 已经自动处理了这个问题，会将 `postgres://` 自动替换为 `postgresql+asyncpg://`。如果仍报错，请检查 `DATABASE_URL` 变量是否被正确注入。

**Q: 构建速度很慢？**
A: Docker 构建第一次会比较慢（下载基础镜像和编译依赖），后续部署会利用缓存，速度会快很多。

---

## 🤝 维护指南

*   **更新代码**: 只要推送到 GitHub，Railway 就会自动重新部署。
*   **查看日志**: 在 Railway 控制台点击服务，选择 "Logs" 即可查看实时日志。
*   **数据库管理**: Railway 提供了网页版的数据库管理工具，也可以通过 "Connect" 标签获取连接串用本地工具连接。

祝你部署愉快！🦆