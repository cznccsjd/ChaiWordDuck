# 2025-11-12 Code Review Report

## Backend Findings

- `AIServiceFactory` 支持 OpenAI 回退，但 `query_word_internal` 直接同步调用 `generate_word_manual`（backend/app/api/v1/words.py:288-302），而 OpenAI 实现是 `async def`（backend/app/services/ai/openai_service.py:38-88）。当切到备用提供商时会得到协程对象，随后的 `model_dump()` 抛错，整条查询链失效。需要统一同步/异步接口并在调用处正确 await。
- AI 生成（单词与图片）均在 FastAPI 协程内直接运行同步 SDK（backend/app/services/ai/gemini_service.py:146-205、backend/app/services/ai/image_generation_service.py:78-170），一次生成会阻塞整个事件循环，导致并发请求饥饿。应换用 SDK 的异步版本或通过 `anyio.to_thread.run_sync`/线程池封装。
- `AIGenerationService.check_generation_limit` 对所有登录用户一律使用免费配额（backend/app/services/ai_generation_service.py:32-41），忽略 `membership_tier` 和 `premium_user_ai_generation_limit`（含 -1 无上限）。结果 Premium 用户仍被限流。需按会员等级选择上限并处理无限场景。
- `backend/tests/integration/test_word_upsert_service.py` 多处使用未定义的 `async_session` 变量（例如 :204-259），pytest 将直接 `NameError`。应改用 fixture 传入的 `test_db` 或显式声明依赖，确保集成测试可运行。

## Frontend Findings

- `getQueryLimit` 直接将 `/words/query-limit` 响应视作 `QueryLimit`（frontend/lib/api/words.ts:60-64），但后端返回 `SuccessResponse` 包裹且字段为 `totalQueries/remainingQueries`。`useQueryLimit` 读取 `remaining/total` 时得到 `undefined`，需要先解包 `success/data` 并转换字段，或调整类型定义（frontend/types/index.ts:91-95）。
- `useQueryLimit` 提供的 `recordQuery` 从未被调用（frontend/lib/hooks/useQueryLimit.ts:138-175），首页仅调用 `refresh`（frontend/app/page.tsx:61-66）。游客查询次数不会被本地递增，导致 UI 永远显示“还有次数”。应在搜索成功后调用 `recordQuery` 或统一依赖后端统计。
- 收藏 API 期望裸 JSON（frontend/lib/api/favorites.ts:5-38），而后端返回 `SuccessResponse`。`response.data` 实际是 `{ success, data }`，访问 `response.data.is_favorited` 等字段会失败。需检查 `success` 并读取 `response.data.data`。
- 游客配额在前端被硬编码为 1（frontend/lib/hooks/useQueryLimit.ts:84-118），与后端 `settings.guest_daily_limit`（默认 10）不符。应该改为依赖配置或接口返回值，避免界面误导。
- `getWordById`/`WordManualApiResponse` 仍使用 `created_at`（frontend/lib/api/words.ts:95-108、frontend/types/index.ts:73-88），但后端按别名输出 `createdAt`。当前实现总是 fallback 到 `new Date()`，导致创建时间错误。需要与后端字段保持一致。
- `SearchBox` 只接受纯字母（frontend/components/features/SearchBox.tsx:37-47），但后端允许字母、连字符与空格（backend/app/api/v1/words.py:168-175）。诸如 “self-esteem” 的合法输入会被前端拒绝，应放宽校验以匹配后端规则。
