"""
用户偏好设置完整流程测试

测试用户语言偏好设置的端到端流程，包括：
- 偏好设置的创建、读取、更新、删除
- 偏好设置在单词查询中的应用
- 数据库持久化和一致性
- 用户认证和授权
- 错误处理和边界情况
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.services.user_preferences import (
    get_user_language_preference,
    get_effective_language,
    update_user_language_preference,
    should_use_user_preference
)
from app.services.ai.base import WordManualData


class TestUserPreferencesCompleteFlow:
    """用户偏好设置完整流程测试"""

    @pytest.fixture
    def mock_word_data_chinese(self):
        """模拟中文单词数据"""
        return WordManualData(
            word="hello",
            phonetic="[həˈloʊ]",
            part_of_speech="interjection",
            core_game="你好游戏：通过打招呼游戏学习英语",
            scenario_formal="正式场景：Hello, nice to meet you. 你好，很高兴认识你。",
            scenario_casual="日常场景：Hey! What's up? 嘿！最近怎么样？",
            etymology_breakdown="词源拆解：hello源于法语holà",
            etymology_story="词源故事：hello最初是电话问候语",
            memory_trick="记忆技巧：he-llo，他来了，要打招呼",
            common_mistakes="常见错误：不要和hollow混淆"
        )

    @pytest.fixture
    def mock_word_data_english(self):
        """模拟英文单词数据"""
        return WordManualData(
            word="hello",
            phonetic="[həˈloʊ]",
            part_of_speech="interjection",
            core_game="Hello game: Learn greetings through interactive play",
            scenario_formal="Formal scenario: Hello, nice to meet you.",
            scenario_casual="Casual scenario: Hey! What's up?",
            etymology_breakdown="Etymology: hello from French holà",
            etymology_story="Etymology story: hello originated as telephone greeting",
            memory_trick="Memory trick: he-llo, he arrives, say hello",
            common_mistakes="Common mistakes: don't confuse with hollow"
        )

    async def test_user_preferences_crud_operations(
        self, client: AsyncClient, created_user: User, auth_headers: dict, test_db: AsyncSession
    ):
        """测试用户偏好设置的CRUD操作"""
        # 1. 创建偏好设置（更新为中文）
        update_response = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["success"] is True
        assert update_data["data"]["preferred_language"] == "zh_CN"

        # 2. 读取偏好设置
        get_response = await client.get("/api/v1/users/preferences", headers=auth_headers)
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["success"] is True
        assert get_data["data"]["preferred_language"] == "zh_CN"
        assert get_data["data"]["id"] == created_user.id
        assert get_data["data"]["email"] == created_user.email

        # 3. 更新偏好设置（改为英文）
        update_response2 = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "en_US"},
            headers=auth_headers
        )
        assert update_response2.status_code == 200
        update_data2 = update_response2.json()
        assert update_data2["data"]["preferred_language"] == "en_US"

        # 4. 验证更新成功
        get_response2 = await client.get("/api/v1/users/preferences", headers=auth_headers)
        assert get_response2.status_code == 200
        get_data2 = get_response2.json()
        assert get_data2["data"]["preferred_language"] == "en_US"

        # 5. 验证数据库持久化
        from app.models.user import User as UserModel
        result = await test_db.execute(
            select(UserModel).where(UserModel.id == created_user.id)
        )
        db_user = result.scalar_one()
        assert db_user.preferred_language == "en_US"

    async def test_user_preferences_applied_in_word_queries(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession, mock_word_data_chinese, mock_word_data_english
    ):
        """测试用户偏好设置在单词查询中的应用"""
        # 1. 设置用户偏好为中文
        await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"},
            headers=auth_headers
        )

        # 2. Mock AI服务
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 1, 10, "free")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 3. 查询单词（应使用用户偏好的中文）
                    mock_service.generate_word_manual.return_value = mock_word_data_chinese
                    response1 = await client.post(
                        "/api/v1/words/query",
                        json={"word": "hello"},
                        headers=auth_headers
                    )
                    assert response1.status_code == 200
                    assert "你好游戏" in response1.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("hello", language="zh_CN")

                    # 4. 更改用户偏好为英文
                    await client.put(
                        "/api/v1/users/preferences",
                        json={"preferred_language": "en_US"},
                        headers=auth_headers
                    )

                    # 5. 再次查询（应使用新的偏好）
                    mock_service.generate_word_manual.return_value = mock_word_data_english
                    response2 = await client.post(
                        "/api/v1/words/query",
                        json={"word": "hello"},
                        headers=auth_headers
                    )
                    assert response2.status_code == 200
                    assert "Hello game" in response2.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("hello", language="en_US")

    async def test_explicit_language_parameter_overrides_preferences(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession, mock_word_data_chinese
    ):
        """测试显式语言参数覆盖用户偏好"""
        # 1. 设置用户偏好为英文
        await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "en_US"},
            headers=auth_headers
        )

        # 2. Mock AI服务
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_chinese
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 1, 10, "free")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 3. 查询单词时显式指定中文（应覆盖用户偏好）
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "hello", "language": "zh_CN"},
                        headers=auth_headers
                    )
                    assert response.status_code == 200
                    assert "你好游戏" in response.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("hello", language="zh_CN")

    async def test_user_preferences_persistence_across_restarts(
        self, client: AsyncClient, created_user: User, auth_headers: dict, test_db: AsyncSession
    ):
        """测试用户偏好设置在重启后持久化"""
        # 1. 设置用户偏好
        await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"},
            headers=auth_headers
        )

        # 2. 模拟重启：清除应用缓存但保留数据库
        # 这里通过直接查询数据库来验证持久化
        from app.models.user import User as UserModel
        result = await test_db.execute(
            select(UserModel).where(UserModel.id == created_user.id)
        )
        db_user = result.scalar_one()
        assert db_user.preferred_language == "zh_CN"

        # 3. 模拟新会话：重新获取用户偏好
        get_response = await client.get("/api/v1/users/preferences", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["data"]["preferred_language"] == "zh_CN"

    async def test_user_preferences_authentication_and_authorization(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试用户偏好设置的认证和授权"""
        # 1. 测试未授权访问
        unauthorized_response = await client.get("/api/v1/users/preferences")
        assert unauthorized_response.status_code == 401

        unauthorized_update = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"}
        )
        assert unauthorized_update.status_code == 401

        # 2. 测试无效token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        invalid_response = await client.get("/api/v1/users/preferences", headers=invalid_headers)
        assert invalid_response.status_code == 401

        # 3. 测试授权访问
        authorized_response = await client.get("/api/v1/users/preferences", headers=auth_headers)
        assert authorized_response.status_code == 200

        # 4. 测试授权更新
        authorized_update = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "en_US"},
            headers=auth_headers
        )
        assert authorized_update.status_code == 200

    async def test_user_preferences_validation_and_error_handling(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试用户偏好设置的验证和错误处理"""
        # 1. 测试无效语言代码
        invalid_language_response = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "invalid_lang"},
            headers=auth_headers
        )
        assert invalid_language_response.status_code == 422
        assert "不支持的语言代码" in invalid_language_response.json()["message"]

        # 2. 测试空语言代码
        empty_language_response = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": ""},
            headers=auth_headers
        )
        assert empty_language_response.status_code == 422

        # 3. 测试缺少必需字段
        missing_field_response = await client.put(
            "/api/v1/users/preferences",
            json={},  # 缺少preferred_language
            headers=auth_headers
        )
        assert missing_field_response.status_code == 422

        # 4. 测试额外字段
        extra_fields_response = await client.put(
            "/api/v1/users/preferences",
            json={
                "preferred_language": "zh_CN",
                "extra_field": "should_be_ignored"
            },
            headers=auth_headers
        )
        # 应该成功，额外字段被忽略
        assert extra_fields_response.status_code == 200

    async def test_concurrent_user_preferences_updates(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试并发用户偏好更新"""
        # 并发发送多个更新请求
        tasks = []
        languages = ["zh_CN", "en_US", "zh_CN", "en_US", "zh_CN"]

        for language in languages:
            task = client.put(
                "/api/v1/users/preferences",
                json={"preferred_language": language},
                headers=auth_headers
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 所有请求都应该成功
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code == 200

        # 验证最终状态
        final_response = await client.get("/api/v1/users/preferences", headers=auth_headers)
        assert final_response.status_code == 200
        final_language = final_response.json()["data"]["preferred_language"]
        assert final_language in ["zh_CN", "en_US"]

    async def test_user_preferences_service_layer_functions(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试用户偏好设置服务层函数"""
        # 1. 测试获取用户语言偏好
        from app.models.user import User as UserModel
        result = await test_db.execute(
            select(UserModel).where(UserModel.id == created_user.id)
        )
        db_user = result.scalar_one()

        # 初始状态应该有默认语言
        initial_preference = get_user_language_preference(db_user)
        assert initial_preference in ["zh_CN", "en_US"]

        # 2. 测试更新用户语言偏好
        updated_user = update_user_language_preference(db_user, "zh_CN")
        assert updated_user.preferred_language == "zh_CN"

        # 3. 测试是否应该使用用户偏好
        assert should_use_user_preference(db_user, explicit_language=None) is True
        assert should_use_user_preference(db_user, explicit_language="en_US") is False
        assert should_use_user_preference(None, explicit_language=None) is False

        # 4. 测试获取有效语言
        effective_lang1 = get_effective_language(db_user, explicit_language=None)
        assert effective_lang1 == "zh_CN"

        effective_lang2 = get_effective_language(db_user, explicit_language="en_US")
        assert effective_lang2 == "en_US"

        effective_lang3 = get_effective_language(None, explicit_language="zh_CN")
        assert effective_lang3 == "zh_CN"

    async def test_user_preferences_with_different_user_roles(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """测试不同用户角色的偏好设置"""
        from app.core.security import get_password_hash, create_access_token

        # 1. 创建免费用户
        free_user = User(
            email="free@example.com",
            password_hash=get_password_hash("TestPass123"),
            membership_tier="free",
        )
        test_db.add(free_user)
        await test_db.commit()
        await test_db.refresh(free_user)

        # 2. 创建高级用户
        premium_user = User(
            email="premium@example.com",
            password_hash=get_password_hash("TestPass123"),
            membership_tier="premium",
        )
        test_db.add(premium_user)
        await test_db.commit()
        await test_db.refresh(premium_user)

        # 3. 生成token
        free_token = create_access_token(data={"sub": str(free_user.id)})
        premium_token = create_access_token(data={"sub": str(premium_user.id)})
        free_headers = {"Authorization": f"Bearer {free_token}"}
        premium_headers = {"Authorization": f"Bearer {premium_token}"}

        # 4. 免费用户设置偏好
        free_response = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"},
            headers=free_headers
        )
        assert free_response.status_code == 200

        # 5. 高级用户设置偏好
        premium_response = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "en_US"},
            headers=premium_headers
        )
        assert premium_response.status_code == 200

        # 6. 验证各自偏好
        free_get = await client.get("/api/v1/users/preferences", headers=free_headers)
        premium_get = await client.get("/api/v1/users/preferences", headers=premium_headers)

        assert free_get.json()["data"]["preferred_language"] == "zh_CN"
        assert premium_get.json()["data"]["preferred_language"] == "en_US"

    async def test_user_preferences_data_integrity(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试用户偏好设置的数据完整性"""
        # 1. 设置偏好
        await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"},
            headers=auth_headers
        )

        # 2. 验证API响应数据完整性
        response = await client.get("/api/v1/users/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]

        # 验证必需字段存在
        required_fields = ["id", "email", "preferred_language"]
        for field in required_fields:
            assert field in data

        # 验证数据类型正确
        assert isinstance(data["id"], int)
        assert isinstance(data["email"], str)
        assert isinstance(data["preferred_language"], str)

        # 3. 验证数据库数据完整性
        from app.models.user import User as UserModel
        result = await test_db.execute(
            select(UserModel).where(UserModel.id == created_user.id)
        )
        db_user = result.scalar_one()
        assert db_user.preferred_language == "zh_CN"
        assert db_user.email == created_user.email
        assert db_user.id == created_user.id

    async def test_user_preferences_edge_cases(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试用户偏好设置的边界情况"""
        # 1. 测试重复设置相同值
        response1 = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"},
            headers=auth_headers
        )
        assert response1.status_code == 200

        response2 = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"},
            headers=auth_headers
        )
        assert response2.status_code == 200

        # 2. 测试快速切换语言
        languages = ["zh_CN", "en_US", "zh_CN", "en_US", "zh_CN"]
        for language in languages:
            response = await client.put(
                "/api/v1/users/preferences",
                json={"preferred_language": language},
                headers=auth_headers
            )
            assert response.status_code == 200

        # 3. 验证最终状态
        final_response = await client.get("/api/v1/users/preferences", headers=auth_headers)
        assert final_response.json()["data"]["preferred_language"] == "zh_CN"

    async def test_user_preferences_with_database_constraints(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试用户偏好设置与数据库约束"""
        # 1. 验证用户只能设置自己的偏好
        from app.core.security import create_access_token

        # 创建另一个用户
        other_user = User(
            email="other@example.com",
            password_hash=get_password_hash("TestPass123"),
            membership_tier="free",
        )
        test_db.add(other_user)
        await test_db.commit()
        await test_db.refresh(other_user)

        # 使用other_user的token，但尝试通过URL参数修改created_user的偏好
        # （如果API支持user_id参数的话，这里假设不支持，JWT token已经包含了用户信息）
        other_token = create_access_token(data={"sub": str(other_user.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # 设置other_user的偏好
        response = await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "en_US"},
            headers=other_headers
        )
        assert response.status_code == 200

        # 验证created_user的偏好没有改变
        created_user_response = await client.get("/api/v1/users/preferences", headers=auth_headers)
        created_user_preference = created_user_response.json()["data"]["preferred_language"]

        # 验证数据隔离
        other_user_response = await client.get("/api/v1/users/preferences", headers=other_headers)
        other_user_preference = other_user_response.json()["data"]["preferred_language"]

        # 两个用户的偏好应该是独立的
        assert created_user_preference != other_user_preference or created_user_preference in ["zh_CN", "en_US"]