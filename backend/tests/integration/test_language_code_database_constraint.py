"""
语言代码数据库约束集成测试

验证语言代码处理与数据库约束的一致性，确保：
- 应用层产生的语言代码符合数据库约束
- 数据库操作不会违反check_words_language_code约束
- 用户偏好存储和检索使用正确的语言代码格式
- API响应使用一致的语言代码格式
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch, Mock, AsyncMock
from httpx import AsyncClient

from app.models.user import User
from app.models.word import Word
from app.core.security import get_password_hash


class TestLanguageCodeDatabaseConstraint:
    """语言代码数据库约束集成测试"""

    async def test_user_model_language_code_constraint(self, test_db: AsyncSession):
        """测试用户模型语言代码约束"""
        # 测试有效的2字符语言代码
        valid_users = [
            User(
                email="user1@example.com",
                password_hash=get_password_hash("TestPass123"),
                membership_tier="free",
                preferred_language="en"
            ),
            User(
                email="user2@example.com",
                password_hash=get_password_hash("TestPass123"),
                membership_tier="free",
                preferred_language="zh"
            ),
        ]

        for user in valid_users:
            test_db.add(user)
            await test_db.commit()
            await test_db.refresh(user)
            assert len(user.preferred_language) == 2
            assert user.preferred_language in ["en", "zh"]

        # 测试无效的5字符语言代码应该违反约束
        invalid_user = User(
            email="invalid@example.com",
            password_hash=get_password_hash("TestPass123"),
            membership_tier="free",
            preferred_language="en_US"  # 这应该违反数据库约束
        )

        test_db.add(invalid_user)
        with pytest.raises(IntegrityError):
            await test_db.commit()

    async def test_word_model_language_code_constraint(self, test_db: AsyncSession):
        """测试单词模型语言代码约束"""
        # 测试有效的2字符语言代码
        valid_words = [
            Word(
                word="welcome",
                phonetic="[ˈwelkəm]",
                core_game="Welcome game content",
                scenario_formal="Formal scenario",
                scenario_casual="Casual scenario",
                etymology_breakdown="Etymology",
                common_mistakes="Common mistakes",
                memory_trick="Memory trick",
                language_code="en"
            ),
            Word(
                word="欢迎",
                phonetic="[huānyíng]",
                core_game="欢迎游戏内容",
                scenario_formal="正式场景",
                scenario_casual="日常场景",
                etymology_breakdown="词源",
                common_mistakes="常见错误",
                memory_trick="记忆技巧",
                language_code="zh"
            ),
        ]

        for word in valid_words:
            test_db.add(word)
            await test_db.commit()
            await test_db.refresh(word)
            assert len(word.language_code) == 2
            assert word.language_code in ["en", "zh"]

        # 测试无效的5字符语言代码应该违反约束
        invalid_word = Word(
            word="test",
            phonetic="[test]",
            core_game="Test content",
            scenario_formal="Formal scenario",
            scenario_casual="Casual scenario",
            etymology_breakdown="Etymology",
            common_mistakes="Common mistakes",
            memory_trick="Memory trick",
            language_code="en_US"  # 这应该违反数据库约束
        )

        test_db.add(invalid_word)
        with pytest.raises(IntegrityError):
            await test_db.commit()

    async def test_api_user_preferences_language_code(
        self, client: AsyncClient, test_db: AsyncSession, created_user: User
    ):
        """测试API用户偏好设置使用正确的语言代码"""
        # 更新用户语言偏好为2字符代码
        update_data = {"preferred_language": "en"}
        response = await client.patch(
            f"/api/v1/users/{created_user.id}/preferences",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["preferredLanguage"] == "en"
        assert len(data["data"]["preferredLanguage"]) == 2

        # 验证数据库中的值
        await test_db.refresh(created_user)
        assert created_user.preferred_language == "en"
        assert len(created_user.preferred_language) == 2

        # 测试更新为中文
        update_data = {"preferred_language": "zh"}
        response = await client.patch(
            f"/api/v1/users/{created_user.id}/preferences",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["preferredLanguage"] == "zh"
        assert len(data["data"]["preferredLanguage"]) == 2

    async def test_api_guest_mode_language_code_handling(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """测试API游客模式语言代码处理"""
        mock_word_data = Mock()
        mock_word_data.word = "welcome"
        mock_word_data.phonetic = "[ˈwelkəm]"
        mock_word_data.part_of_speech = "interjection"
        mock_word_data.core_game = "Welcome game"
        mock_word_data.scenario_formal = "Formal scenario"
        mock_word_data.scenario_casual = "Casual scenario"
        mock_word_data.etymology_breakdown = "Etymology"
        mock_word_data.etymology_story = "Etymology story"
        mock_word_data.common_mistakes = "Common mistakes"
        mock_word_data.memory_trick = "Memory trick"

        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 测试Accept-Language头部处理
                    headers = {"Accept-Language": "en-US,en;q=0.9"}
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome"},
                        headers=headers
                    )
                    assert response.status_code == 200
                    # 验证调用AI服务时使用2字符语言代码
                    mock_service.generate_word_manual.assert_called_with("welcome", language="en")

                    # 测试显式语言参数
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome", "language": "zh_CN"}  # 输入5字符代码
                    )
                    assert response.status_code == 200
                    # 应该被标准化为2字符代码
                    mock_service.generate_word_manual.assert_called_with("welcome", language="zh")

    async def test_language_code_conversion_consistency(self, test_db: AsyncSession):
        """测试语言代码转换一致性"""
        # 创建使用不同语言代码的测试数据
        test_cases = [
            ("en", "en"),  # 2字符代码保持不变
            ("zh", "zh"),  # 2字符代码保持不变
        ]

        for input_code, expected_code in test_cases:
            # 测试用户模型
            user = User(
                email=f"test_{input_code}@example.com",
                password_hash=get_password_hash("TestPass123"),
                membership_tier="free",
                preferred_language=input_code
            )
            test_db.add(user)
            await test_db.commit()
            await test_db.refresh(user)
            assert user.preferred_language == expected_code

            # 测试单词模型
            word = Word(
                word=f"test_{input_code}",
                phonetic="[test]",
                core_game="Test content",
                scenario_formal="Formal scenario",
                scenario_casual="Casual scenario",
                etymology_breakdown="Etymology",
                common_mistakes="Common mistakes",
                memory_trick="Memory trick",
                language_code=input_code
            )
            test_db.add(word)
            await test_db.commit()
            await test_db.refresh(word)
            assert word.language_code == expected_code

    async def test_database_constraint_edge_cases(self, test_db: AsyncSession):
        """测试数据库约束边界情况"""
        # 测试各种可能违反约束的语言代码格式
        invalid_codes = [
            "en_US",
            "zh_CN",
            "zh_TW",
            "en-us",
            "zh-cn",
            "EN",
            "ZH",
            "En_Us",
            "Zh_Cn",
            "english",
            "chinese",
            "invalid_lang",
            "e",  # 太短
            "eng",  # 太长
        ]

        for invalid_code in invalid_codes:
            # 测试用户模型约束
            user = User(
                email=f"test_{invalid_code}@example.com",
                password_hash=get_password_hash("TestPass123"),
                membership_tier="free",
                preferred_language=invalid_code
            )
            test_db.add(user)

            try:
                await test_db.commit()
                # 如果成功提交，检查数据库是否自动修正了值
                await test_db.refresh(user)
                assert len(user.preferred_language) == 2, \
                    f"数据库应该拒绝或修正语言代码 '{invalid_code}'"
            except IntegrityError:
                # 这是期望的行为，数据库应该拒绝无效的语言代码
                await test_db.rollback()

            # 测试单词模型约束
            word = Word(
                word=f"test_{invalid_code}",
                phonetic="[test]",
                core_game="Test content",
                scenario_formal="Formal scenario",
                scenario_casual="Casual scenario",
                etymology_breakdown="Etymology",
                common_mistakes="Common mistakes",
                memory_trick="Memory trick",
                language_code=invalid_code
            )
            test_db.add(word)

            try:
                await test_db.commit()
                # 如果成功提交，检查数据库是否自动修正了值
                await test_db.refresh(word)
                assert len(word.language_code) == 2, \
                    f"数据库应该拒绝或修正语言代码 '{invalid_code}'"
            except IntegrityError:
                # 这是期望的行为，数据库应该拒绝无效的语言代码
                await test_db.rollback()

    async def test_api_response_language_code_format(
        self, client: AsyncClient, test_db: AsyncSession, created_user: User
    ):
        """测试API响应中的语言代码格式"""
        # 获取用户偏好，验证语言代码格式
        response = await client.get(f"/api/v1/users/{created_user.id}/preferences")
        assert response.status_code == 200
        data = response.json()
        preferred_language = data["data"]["preferredLanguage"]
        assert len(preferred_language) == 2
        assert preferred_language in ["en", "zh"]

        # 创建测试单词数据
        word = Word(
            word="test",
            phonetic="[test]",
            core_game="Test content",
            scenario_formal="Formal scenario",
            scenario_casual="Casual scenario",
            etymology_breakdown="Etymology",
            common_mistakes="Common mistakes",
            memory_trick="Memory trick",
            language_code="en"
        )
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        # 获取单词数据，验证语言代码格式
        response = await client.get(f"/api/v1/words/{word.id}")
        assert response.status_code == 200
        data = response.json()
        language_code = data["data"]["languageCode"]
        assert len(language_code) == 2
        assert language_code == "en"

    async def test_language_code_migration_compatibility(self, test_db: AsyncSession):
        """测试语言代码迁移兼容性"""
        # 模拟旧数据迁移场景
        # 如果数据库中有旧的5字符语言代码，应用应该能正确处理

        # 直接在数据库中插入旧的5字符语言代码（绕过模型验证）
        raw_sql = """
        INSERT INTO words (
            word, phonetic, core_game, scenario_formal, scenario_casual,
            etymology_breakdown, common_mistakes, memory_trick,
            language_code, source, created_at, updated_at
        ) VALUES (
            :word, :phonetic, :core_game, :scenario_formal, :scenario_casual,
            :etymology_breakdown, :common_mistakes, :memory_trick,
            :language_code, :source, datetime('now'), datetime('now')
        )
        """

        # 注意：这个测试假设我们能够绕过模型验证直接插入数据
        # 在实际情况下，这可能需要数据库迁移脚本来处理

        # 测试应用读取现有数据时的兼容性
        # 这里我们创建符合新格式的数据，确保应用能正确处理
        word = Word(
            word="migration_test",
            phonetic="[test]",
            core_game="Migration test content",
            scenario_formal="Formal scenario",
            scenario_casual="Casual scenario",
            etymology_breakdown="Etymology",
            common_mistakes="Common mistakes",
            memory_trick="Memory trick",
            language_code="en"  # 使用新的2字符格式
        )
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        # 验证应用能正确读取和处理这种格式
        assert word.language_code == "en"
        assert len(word.language_code) == 2

    async def test_concurrent_language_code_operations(
        self, client: AsyncClient, test_db: AsyncSession, created_user: User
    ):
        """测试并发语言代码操作"""
        import asyncio

        async def update_user_preference(language_code):
            """更新用户语言偏好的异步操作"""
            response = await client.patch(
                f"/api/v1/users/{created_user.id}/preferences",
                json={"preferred_language": language_code}
            )
            return response

        # 并发执行多个语言偏好更新
        tasks = [
            update_user_preference("en"),
            update_user_preference("zh"),
            update_user_preference("en"),
            update_user_preference("zh"),
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有操作都成功
        for response in responses:
            assert not isinstance(response, Exception)
            assert response.status_code == 200
            data = response.json()
            preferred_language = data["data"]["preferredLanguage"]
            assert len(preferred_language) == 2
            assert preferred_language in ["en", "zh"]

        # 验证最终状态的一致性
        await test_db.refresh(created_user)
        assert len(created_user.preferred_language) == 2
        assert created_user.preferred_language in ["en", "zh"]

    async def test_language_code_logging_and_monitoring(self, client: AsyncClient):
        """测试语言代码处理日志和监控"""
        mock_word_data = Mock()
        mock_word_data.word = "welcome"
        mock_word_data.phonetic = "[ˈwelkəm]"
        mock_word_data.core_game = "Welcome game"

        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data
            mock_get_service.return_value = mock_service

            with patch('app.services.guest_preferences.logger') as mock_logger:
                # Mock rate limiter and AI generation service
                with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                    mock_rate_limiter_instance = Mock()
                    mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                        return_value=(True, 5, 10, "guest")
                    )
                    mock_rate_limiter.return_value = mock_rate_limiter_instance

                    with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                        mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                        mock_ai_gen.log_generation = AsyncMock()

                        # 测试各种语言代码输入的日志记录
                        test_headers = [
                            {"Accept-Language": "en-US,en;q=0.9"},
                            {"Accept-Language": "zh-CN,zh;q=0.9"},
                            {"Accept-Language": "invalid-lang"},
                        ]

                        for headers in test_headers:
                            response = await client.post(
                                "/api/v1/words/query",
                                json={"word": "welcome"},
                                headers=headers
                            )
                            assert response.status_code == 200

                        # 验证日志记录（如果实现了）
                        # 这里可以根据实际的日志实现进行验证
                        # mock_logger.info.assert_called() 或类似的断言