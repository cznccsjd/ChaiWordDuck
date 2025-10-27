"""
重构后的多语言功能集成测试

使用新的测试架构，解决以下问题：
1. 硬编码测试数据 - 使用动态数据生成器
2. 测试隔离不足 - 完善的隔离机制
3. 并发安全问题 - 并发控制机制
4. 数据清理不完整 - 自动化清理流程
5. 测试生命周期管理 - 完整的生命周期控制
"""
import pytest
import asyncio
from typing import Dict, List, Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# 使用新的测试架构
from ..base.base_test_class import BaseIntegrationTestClass, MultiLanguageTestMixin
from ..utils.test_data_generator import TestDataFactory
from ..utils.concurrency_controller import (
    concurrent_test_execution, locked_resource_access, LockType, get_concurrency_controller
)
from ..utils.test_isolation import isolated_test_context


class RefactoredMultiLanguageIntegrationTest(BaseIntegrationTestClass, MultiLanguageTestMixin):
    """
    重构后的多语言集成测试类

    展示新测试架构的完整使用方式
    """

    @pytest.mark.asyncio
    async def test_dynamic_chinese_word_generation_flow(
        self,
        enhanced_client: AsyncClient,
        enhanced_test_db: AsyncSession,
        setup_test_environment,
        concurrency_controller
    ):
        """测试动态中文单词生成流程（解决硬编码问题）"""
        test_name = f"{self.test_name}.test_dynamic_chinese_word_generation_flow"

        async with concurrent_test_execution(test_name):
            async with isolated_test_context(test_name) as isolation_manager:
                # 设置测试环境
                await setup_test_environment.setup_test(enhanced_test_db, enhanced_client)

                # 生成唯一的测试数据（不再是硬编码的"test"）
                chinese_word = self.generate_test_word("zh_CN")
                self.logger.info(f"Generated unique Chinese word: {chinese_word.word}")

                # 使用资源锁确保数据库访问安全
                async with locked_resource_access(
                    LockType.DATABASE,
                    f"word_generation_{chinese_word.word}",
                    test_name
                ):
                    async with self.mock_ai_service({"zh_CN": chinese_word}), \
                               self.mock_rate_limiting(), \
                               self.mock_ai_generation_service():

                        # 执行API调用
                        response = await enhanced_client.post(
                            "/api/v1/words/query",
                            json={"word": chinese_word.word},
                            headers={"Accept-Language": "zh-CN,zh;q=0.9"}
                        )

                        # 验证响应
                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True
                        assert data["data"]["word"] == chinese_word.word

                        # 验证中文内容
                        assert "游戏内容" in data["data"]["coreGame"]
                        assert "正式场景" in data["data"]["scenarioFormal"]
                        assert "词源拆解" in data["data"]["etymologyBreakdown"]

                        # 使用数据验证方法确保一致性
                        self.assert_word_data_consistency(chinese_word, data["data"])

                        self.logger.info(f"Successfully validated Chinese word: {chinese_word.word}")

    @pytest.mark.asyncio
    async def test_dynamic_english_word_generation_flow(
        self,
        enhanced_client: AsyncClient,
        enhanced_test_db: AsyncSession,
        setup_test_environment
    ):
        """测试动态英文单词生成流程"""
        test_name = f"{self.test_name}.test_dynamic_english_word_generation_flow"

        async with concurrent_test_execution(test_name):
            async with isolated_test_context(test_name):
                await setup_test_environment.setup_test(enhanced_test_db, enhanced_client)

                # 生成唯一的英文测试数据
                english_word = self.generate_test_word("en_US")
                self.logger.info(f"Generated unique English word: {english_word.word}")

                async with self.mock_ai_service({"en_US": english_word}), \
                           self.mock_rate_limiting(), \
                           self.mock_ai_generation_service():

                    # 设置用户语言偏好
                    await enhanced_client.put(
                        "/api/v1/users/preferences",
                        json={"preferred_language": "en_US"},
                        headers=setup_test_environment.test_base_class.get_auth_headers()
                    )

                    # 执行API调用
                    response = await enhanced_client.post(
                        "/api/v1/words/query",
                        json={"word": english_word.word}
                    )

                    # 验证响应
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["data"]["word"] == english_word.word

                    # 验证英文内容
                    assert "game content" in data["data"]["coreGame"].lower()
                    assert "formal scenario" in data["data"]["scenarioFormal"].lower()

                    self.assert_word_data_consistency(english_word, data["data"])

    @pytest.mark.asyncio
    async def test_language_parameter_priority_with_unique_data(
        self,
        enhanced_client: AsyncClient,
        enhanced_test_db: AsyncSession,
        setup_test_environment
    ):
        """测试语言参数优先级（使用唯一数据）"""
        test_name = f"{self.test_name}.test_language_parameter_priority_with_unique_data"

        async with concurrent_test_execution(test_name):
            async with isolated_test_context(test_name):
                await setup_test_environment.setup_test(enhanced_test_db, enhanced_client)

                # 生成中英文单词对
                word_pair = self.generate_test_word_pair()
                chinese_word = word_pair["zh_CN"]
                english_word = word_pair["en_US"]

                self.logger.info(f"Generated word pair: CN={chinese_word.word}, EN={english_word.word}")

                # 测试显式语言参数覆盖用户偏好
                async with self.mock_ai_service({"en_US": english_word}), \
                           self.mock_rate_limiting(), \
                           self.mock_ai_generation_service():

                    # 设置用户偏好为中文
                    await enhanced_client.put(
                        "/api/v1/users/preferences",
                        json={"preferred_language": "zh_CN"},
                        headers=setup_test_environment.test_base_class.get_auth_headers()
                    )

                    # 但显式指定英文
                    response = await enhanced_client.post(
                        "/api/v1/words/query",
                        json={"word": english_word.word, "language": "en_US"},
                        headers=setup_test_environment.test_base_class.get_auth_headers()
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True

                    # 应该返回英文内容，显式参数优先
                    assert "game content" in data["data"]["coreGame"].lower()
                    self.assert_word_data_consistency(english_word, data["data"])

    @pytest.mark.asyncio
    async def test_concurrent_multilang_requests_with_isolation(
        self,
        enhanced_client: AsyncClient,
        enhanced_test_db: AsyncSession,
        setup_test_environment
    ):
        """测试并发多语言请求（完全隔离）"""
        test_name = f"{self.test_name}.test_concurrent_multilang_requests_with_isolation"

        async with concurrent_test_execution(test_name):
            async with isolated_test_context(test_name):
                await setup_test_environment.setup_test(enhanced_test_db, enhanced_client)

                # 为每个并发请求生成唯一的数据
                concurrent_word_pairs = [
                    self.generate_test_word_pair() for _ in range(4)
                ]

                # 并发测试函数
                async def make_word_request(
                    word_pair: Dict[str, Any],
                    language: str,
                    request_id: int
                ):
                    """执行单个单词请求"""
                    sub_test_name = f"{test_name}.request_{request_id}"
                    word_data = word_pair[language]

                    async with locked_resource_access(
                        LockType.WORD_DATA,
                        f"request_{word_data.word}",
                        sub_test_name
                    ):
                        async with self.mock_ai_service({language: word_data}), \
                                   self.mock_rate_limiting(), \
                                   self.mock_ai_generation_service():

                            response = await enhanced_client.post(
                                "/api/v1/words/query",
                                json={"word": word_data.word, "language": language}
                            )

                            assert response.status_code == 200
                            data = response.json()
                            assert data["success"] is True
                            assert data["data"]["word"] == word_data.word

                            self.assert_word_data_consistency(word_data, data["data"])
                            return response

                # 创建并发任务
                tasks = [
                    make_word_request(concurrent_word_pairs[0], "zh_CN", 1),
                    make_word_request(concurrent_word_pairs[1], "en_US", 2),
                    make_word_request(concurrent_word_pairs[2], "zh_CN", 3),
                    make_word_request(concurrent_word_pairs[3], "en_US", 4),
                ]

                # 执行并发请求
                responses = await self.run_concurrent_tests(tasks, max_concurrent=2)

                # 验证所有请求都成功
                for i, response in enumerate(responses):
                    assert not isinstance(response, Exception), f"Request {i} failed: {response}"
                    assert response.status_code == 200

                self.logger.info(f"Successfully completed {len(responses)} concurrent requests")

    @pytest.mark.asyncio
    async def test_guest_language_detection_with_dynamic_data(
        self,
        enhanced_client: AsyncClient,
        enhanced_test_db: AsyncSession,
        setup_test_environment
    ):
        """测试游客语言检测（使用动态数据）"""
        test_name = f"{self.test_name}.test_guest_language_detection_with_dynamic_data"

        async with concurrent_test_execution(test_name):
            async with isolated_test_context(test_name):
                await setup_test_environment.setup_test(enhanced_test_db, enhanced_client)

                # 生成测试数据
                english_word = self.generate_test_word("en_US")

                async with self.mock_ai_service({"en_US": english_word}), \
                           self.mock_rate_limiting(), \
                           self.mock_ai_generation_service():

                    # 测试通过Accept-Language头部检测语言
                    headers = {"Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"}
                    response = await enhanced_client.post(
                        "/api/v1/words/query",
                        json={"word": english_word.word},
                        headers=headers
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["data"]["word"] == english_word.word

                    # 验证英文内容
                    assert "game content" in data["data"]["coreGame"].lower()
                    self.assert_word_data_consistency(english_word, data["data"])

    @pytest.mark.asyncio
    async def test_error_handling_with_unique_invalid_data(
        self,
        enhanced_client: AsyncClient,
        enhanced_test_db: AsyncSession,
        setup_test_environment
    ):
        """测试错误处理（使用唯一的无效数据）"""
        test_name = f"{self.test_name}.test_error_handling_with_unique_invalid_data"

        async with concurrent_test_execution(test_name):
            async with isolated_test_context(test_name):
                await setup_test_environment.setup_test(enhanced_test_db, enhanced_client)

                # 生成测试数据和无效语言代码
                test_word = self.generate_test_word("en_US")
                invalid_language = f"invalid_{test_word.unique_id[:8]}"

                async with self.mock_ai_service({"zh_CN": test_word}), \
                           self.mock_rate_limiting(), \
                           self.mock_ai_generation_service():

                    # 使用无效语言代码查询
                    response = await enhanced_client.post(
                        "/api/v1/words/query",
                        json={"word": test_word.word, "language": invalid_language}
                    )

                    # 应该降级到默认语言
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True

                    # 应该包含中文内容（默认语言）
                    assert "游戏内容" in data["data"]["coreGame"]

    @pytest.mark.asyncio
    async def test_user_preference_persistence_with_unique_data(
        self,
        enhanced_client: AsyncClient,
        enhanced_test_db: AsyncSession,
        setup_test_environment
    ):
        """测试用户偏好持久化（使用唯一数据）"""
        test_name = f"{self.test_name}.test_user_preference_persistence_with_unique_data"

        async with concurrent_test_execution(test_name):
            async with isolated_test_context(test_name):
                await setup_test_environment.setup_test(enhanced_test_db, enhanced_client)

                # 生成多个测试单词
                test_words = self.generate_multiple_test_words(3, "zh_CN")

                async with self.mock_ai_service({"zh_CN": test_words[0]}), \
                           self.mock_rate_limiting(), \
                           self.mock_ai_generation_service():

                    # 设置用户语言偏好
                    await enhanced_client.put(
                        "/api/v1/users/preferences",
                        json={"preferred_language": "zh_CN"},
                        headers=setup_test_environment.test_base_class.get_auth_headers()
                    )

                    # 多次查询验证偏好持续生效
                    for i, word in enumerate(test_words):
                        # 更新mock返回数据
                        async with self.mock_ai_service({"zh_CN": word}), \
                                   self.mock_rate_limiting(), \
                                   self.mock_ai_generation_service():

                            response = await enhanced_client.post(
                                "/api/v1/words/query",
                                json={"word": word.word},
                                headers=setup_test_environment.test_base_class.get_auth_headers()
                            )

                            assert response.status_code == 200
                            data = response.json()
                            assert data["success"] is True
                            assert data["data"]["word"] == word.word

                            # 验证中文内容
                            assert "游戏内容" in data["data"]["coreGame"]

    def test_data_generator_integration(self):
        """测试数据生成器集成"""
        test_name = f"{self.test_name}.test_data_generator_integration"

        # 创建独立的数据生成器
        generator = TestDataFactory.get_generator(test_name)

        # 测试数据生成
        word1 = generator.generate_unique_word("zh_CN")
        word2 = generator.generate_unique_word("en_US")

        # 验证数据唯一性
        assert word1.word != word2.word
        assert word1.language != word2.language
        assert word1.unique_id != word2.unique_id

        # 测试摘要
        summary = generator.get_test_summary()
        assert summary["total_words_generated"] == 2
        assert summary["generated_languages"]["zh_CN"] == 1
        assert summary["generated_languages"]["en_US"] == 1

        # 清理
        TestDataFactory.cleanup_generator(test_name)

    async def test_concurrency_controller_integration(self):
        """测试并发控制器集成"""
        controller = get_concurrency_controller()

        # 测试资源锁
        async with locked_resource_access(
            LockType.GENERAL_RESOURCE,
            "test_resource",
            "integration_test"
        ):
            # 在锁保护的范围内执行操作
            await asyncio.sleep(0.1)

        # 获取并发报告
        report = controller.get_concurrency_report()
        assert "stats" in report
        assert "active_locks" in report