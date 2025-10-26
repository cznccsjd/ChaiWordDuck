"""
测试基类

提供统一的测试基础设施，包括：
1. 测试数据生成和管理
2. 数据隔离和清理
3. Mock服务管理
4. 测试生命周期管理
5. 并发安全控制
"""
import asyncio
import pytest
from typing import AsyncGenerator, Dict, List, Optional, Any, Callable
from unittest.mock import Mock, AsyncMock, patch
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.user import User
from ..utils.test_data_generator import TestDataGenerator, TestDataFactory, TestWordData


class BaseIntegrationTestClass:
    """集成测试基类

    提供统一的测试基础设施和数据管理
    """

    # 测试配置
    MAX_CONCURRENT_TESTS = 5  # 最大并发测试数
    CLEANUP_TIMEOUT = 30  # 清理超时时间（秒）
    ENABLE_TEST_DATA_LOGGING = True  # 启用测试数据日志

    def __init__(self):
        """初始化测试基类"""
        self.test_name: str = self.__class__.__name__
        self.data_generator: TestDataGenerator = TestDataFactory.get_generator(self.test_name)
        self.created_resources: Dict[str, List[Any]] = {
            "users": [],
            "words": [],
            "mock_data": [],
            "database_records": []
        }
        self._cleanup_lock = asyncio.Lock()
        self._setup_complete = False
        self._teardown_started = False

        # 配置日志
        self.logger = logging.getLogger(f"test.{self.test_name}")
        if self.ENABLE_TEST_DATA_LOGGING:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    async def setup_test(self, test_db: AsyncSession, client: AsyncClient):
        """设置测试环境

        Args:
            test_db: 测试数据库session
            client: 测试客户端
        """
        if self._setup_complete:
            return

        async with self._cleanup_lock:
            if self._setup_complete:
                return

            self.logger.info(f"Setting up test: {self.test_name}")
            self.test_db = test_db
            self.client = client

            # 执行自定义设置
            await self.custom_setup()

            self._setup_complete = True
            self.logger.info(f"Test setup complete: {self.test_name}")

    async def custom_setup(self):
        """自定义设置逻辑，子类可以重写"""
        pass

    async def teardown_test(self):
        """清理测试环境"""
        if self._teardown_started:
            return

        async with self._cleanup_lock:
            if self._teardown_started:
                return

            self._teardown_started = True
            self.logger.info(f"Starting teardown for test: {self.test_name}")

            try:
                # 执行自定义清理
                await self.custom_teardown()

                # 清理创建的资源
                await self.cleanup_created_resources()

                # 清理数据生成器
                TestDataFactory.cleanup_generator(self.test_name)

                self.logger.info(f"Teardown complete for test: {self.test_name}")

            except Exception as e:
                self.logger.error(f"Error during teardown for {self.test_name}: {e}")
                raise

    async def custom_teardown(self):
        """自定义清理逻辑，子类可以重写"""
        pass

    async def cleanup_created_resources(self):
        """清理测试过程中创建的资源"""
        cleanup_tasks = []

        # 清理用户
        if self.created_resources["users"]:
            cleanup_tasks.append(self.cleanup_users(self.created_resources["users"]))

        # 清理数据库记录
        if self.created_resources["database_records"]:
            cleanup_tasks.append(self.cleanup_database_records(self.created_resources["database_records"]))

        # 执行清理任务
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        # 清空资源记录
        self.created_resources = {
            "users": [],
            "words": [],
            "mock_data": [],
            "database_records": []
        }

    async def cleanup_users(self, users: List[User]):
        """清理测试用户"""
        try:
            for user in users:
                # 删除用户相关的记录
                await self.test_db.execute(
                    "DELETE FROM users WHERE id = :user_id",
                    {"user_id": user.id}
                )
            await self.test_db.commit()
            self.logger.info(f"Cleaned up {len(users)} test users")
        except Exception as e:
            self.logger.error(f"Error cleaning up users: {e}")
            await self.test_db.rollback()

    async def cleanup_database_records(self, records: List[Any]):
        """清理数据库记录"""
        # 这里可以根据具体模型实现清理逻辑
        pass

    def track_created_user(self, user: User):
        """跟踪创建的测试用户"""
        self.created_resources["users"].append(user)

    def track_created_word(self, word_data: TestWordData):
        """跟踪创建的测试单词数据"""
        self.created_resources["words"].append(word_data)

    def track_created_mock_data(self, mock_data: Any):
        """跟踪创建的Mock数据"""
        self.created_resources["mock_data"].append(mock_data)

    def track_database_record(self, record: Any):
        """跟踪创建的数据库记录"""
        self.created_resources["database_records"].append(record)

    # Mock 服务管理方法
    @asynccontextmanager
    async def mock_ai_service(self, return_data: Optional[Dict[str, TestWordData]] = None):
        """AI服务Mock上下文管理器

        Args:
            return_data: 按语言返回的数据字典，如 {"zh_CN": chinese_data, "en_US": english_data}
        """
        mock_service = Mock()
        mock_calls = []

        def generate_word_manual(word: str, **kwargs):
            language = kwargs.get('language', 'en_US')
            mock_calls.append((word, language, kwargs))

            # 根据语言返回对应的数据
            if return_data and language in return_data:
                return return_data[language].mock_data
            else:
                # 如果没有指定返回数据，生成一个默认的
                test_data = self.data_generator.generate_unique_word(language)
                return test_data.mock_data

        mock_service.generate_word_manual = generate_word_manual
        mock_service.generate_word_manual.call_args_list = mock_calls

        self.track_created_mock_data(mock_service)

        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_get_service.return_value = mock_service
            yield mock_service

    @asynccontextmanager
    async def mock_rate_limiting(self, return_value: tuple = (True, 1, 10, "free")):
        """速率限制Mock上下文管理器"""
        with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
            mock_instance = Mock()
            mock_instance.check_and_record_query = AsyncMock(return_value=return_value)
            mock_rate_limiter.return_value = mock_instance
            yield mock_rate_limiter

    @asynccontextmanager
    async def mock_ai_generation_service(self):
        """AI生成服务Mock上下文管理器"""
        with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
            mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
            mock_ai_gen.log_generation = AsyncMock()
            yield mock_ai_gen

    # 测试数据生成辅助方法
    def generate_test_word(self, language: str = "en_US") -> TestWordData:
        """生成测试单词数据"""
        test_word = self.data_generator.generate_unique_word(language)
        self.track_created_word(test_word)
        return test_word

    def generate_test_word_pair(self) -> Dict[str, TestWordData]:
        """生成中英文单词对"""
        chinese_data, english_data = self.data_generator.generate_multilang_word_pair()
        self.track_created_word(chinese_data)
        self.track_created_word(english_data)
        return {"zh_CN": chinese_data, "en_US": english_data}

    def generate_multiple_test_words(self, count: int, language: str = "en_US") -> List[TestWordData]:
        """生成多个测试单词"""
        test_words = self.data_generator.generate_multiple_unique_words(count, language)
        for word in test_words:
            self.track_created_word(word)
        return test_words

    # 并发安全的测试执行方法
    async def run_concurrent_tests(self, test_functions: List[Callable], max_concurrent: Optional[int] = None):
        """并发执行测试函数

        Args:
            test_functions: 要并发执行的测试函数列表
            max_concurrent: 最大并发数，默认使用类配置
        """
        max_concurrent = max_concurrent or self.MAX_CONCURRENT_TESTS
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(test_func):
            async with semaphore:
                return await test_func()

        # 使用信号量控制并发数
        tasks = [run_with_semaphore(test_func) for test_func in test_functions]
        return await asyncio.gather(*tasks, return_exceptions=True)

    # 数据验证辅助方法
    def assert_word_data_consistency(self, word_data: TestWordData, response_data: Dict[str, Any]):
        """验证单词数据一致性"""
        assert word_data.word in response_data.get("word", ""), f"Word mismatch: {word_data.word} vs {response_data.get('word')}"
        assert word_data.phonetic in response_data.get("phonetic", ""), f"Phonetic mismatch"
        assert word_data.part_of_speech in response_data.get("partOfSpeech", ""), f"Part of speech mismatch"

        # 验证内容字段包含预期语言的内容
        if word_data.language == "zh_CN":
            assert "游戏内容" in response_data.get("coreGame", ""), "Chinese game content missing"
            assert "正式场景" in response_data.get("scenarioFormal", ""), "Chinese formal scenario missing"
        else:
            assert "game content" in response_data.get("coreGame", "").lower(), "English game content missing"
            assert "formal scenario" in response_data.get("scenarioFormal", "").lower(), "English formal scenario missing"

    # 测试统计和报告
    def get_test_statistics(self) -> Dict[str, Any]:
        """获取测试统计信息"""
        data_summary = self.data_generator.get_test_summary()
        return {
            "test_name": self.test_name,
            "setup_complete": self._setup_complete,
            "teardown_started": self._teardown_started,
            "created_resources_count": {
                resource_type: len(resources)
                for resource_type, resources in self.created_resources.items()
            },
            "data_generation_summary": data_summary,
            "cleanup_lock_locked": self._cleanup_lock.locked()
        }

    def log_test_summary(self):
        """记录测试摘要"""
        stats = self.get_test_statistics()
        self.logger.info(f"Test Summary for {self.test_name}:")
        self.logger.info(f"  - Setup Complete: {stats['setup_complete']}")
        self.logger.info(f"  - Created Resources: {stats['created_resources_count']}")
        self.logger.info(f"  - Data Generated: {stats['data_generation_summary']['total_words_generated']} words")


class MultiLanguageTestMixin:
    """多语言测试混入类

    为多语言测试提供额外的辅助方法
    """

    async def test_language_priority_flow(
        self,
        base_test_class: BaseIntegrationTestClass,
        expected_language: str,
        explicit_lang: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        user_preference: Optional[str] = None
    ):
        """测试语言优先级流程的通用方法"""
        test_word = base_test_class.generate_test_word(expected_language)

        # 设置用户偏好（如果指定）
        if user_preference:
            # 这里需要根据实际的API调用来设置用户偏好
            pass

        # 准备请求参数
        request_data = {"word": test_word.word}
        if explicit_lang:
            request_data["language"] = explicit_lang

        # 执行API调用并验证语言参数
        async with base_test_class.mock_ai_service({expected_language: test_word}), \
                base_test_class.mock_rate_limiting(), \
                base_test_class.mock_ai_generation_service():

            response = await base_test_class.client.post(
                "/api/v1/words/query",
                json=request_data,
                headers=headers or {},
                cookies=cookies or {}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            base_test_class.assert_word_data_consistency(test_word, data["data"])

            # 验证AI服务调用参数
            # 注意：这里需要根据实际Mock服务实现来调整
            return response