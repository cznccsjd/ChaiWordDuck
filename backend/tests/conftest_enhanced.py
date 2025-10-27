"""
增强的pytest配置和fixtures

提供改进的测试基础设施，包括：
1. 测试隔离机制
2. 并发安全控制
3. 数据生成和清理
4. 测试生命周期管理
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator, Dict, Any, Optional
from contextlib import asynccontextmanager
import logging
import threading
import time

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, text
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app.core.database import Base, get_db
from app.models import User
from app.core.security import get_password_hash, create_access_token

from .base.base_test_class import BaseIntegrationTestClass
from .utils.test_data_generator import TestDataFactory


# 配置测试日志
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger("pytest.enhanced")

# 并发控制
_global_test_semaphore = None
_test_execution_lock = threading.Lock()
_active_tests: Dict[str, float] = {}


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def global_test_semaphore():
    """全局测试信号量，控制并发测试数量"""
    global _global_test_semaphore
    if _global_test_semaphore is None:
        _global_test_semaphore = asyncio.Semaphore(3)  # 最多3个并发测试
    return _global_test_semaphore


@pytest_asyncio.fixture(scope="function")
async def enhanced_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    增强的测试数据库fixture

    提供更好的隔离和清理机制
    """
    # 为每个测试创建独立的数据库连接
    test_database_url = "sqlite+aiosqlite:///:memory:"

    test_engine = create_async_engine(
        test_database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )

    # 创建测试会话工厂
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建session
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            # 确保session正确关闭
            await session.close()
            # 删除所有表
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            # 关闭引擎
            await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def enhanced_client(enhanced_test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    增强的测试客户端fixture

    提供更好的依赖注入管理
    """
    from app.main import app

    # 覆盖数据库依赖
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield enhanced_test_db

    # 清除之前的依赖覆盖
    app.dependency_overrides.clear()
    # 设置新的依赖覆盖
    app.dependency_overrides[get_db] = override_get_db

    try:
        # 创建异步HTTP客户端
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    finally:
        # 清除依赖覆盖
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user_data_factory():
    """测试用户数据工厂"""
    def _create_user_data(user_id: Optional[int] = None, **overrides) -> Dict[str, Any]:
        base_data = {
            "email": f"testuser{user_id or time.time()}@example.com",
            "password": "TestPass123!",
            "membership_tier": "free",
            "preferred_language": "en_US"
        }
        base_data.update(overrides)
        return base_data

    return _create_user_data


@pytest_asyncio.fixture(scope="function")
async def enhanced_created_user(
    enhanced_test_db: AsyncSession, test_user_data_factory
) -> User:
    """
    增强的测试用户创建fixture

    确保用户数据唯一性和清理
    """
    user_data = test_user_data_factory()

    user = User(
        email=user_data["email"],
        password_hash=get_password_hash(user_data["password"]),
        membership_tier=user_data["membership_tier"],
        preferred_language=user_data.get("preferred_language", "en_US")
    )

    enhanced_test_db.add(user)
    await enhanced_test_db.commit()
    await enhanced_test_db.refresh(user)

    # 记录创建的用户以便后续清理
    user._test_marker = "created_by_fixture"

    return user


@pytest.fixture(scope="function")
def enhanced_auth_headers(enhanced_created_user: User) -> Dict[str, str]:
    """
    增强的认证headers fixture
    """
    access_token = create_access_token(data={"sub": str(enhanced_created_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def test_base_class(request):
    """
    测试基类fixture

    为每个测试提供BaseIntegrationTestClass实例
    """
    test_name = f"{request.cls.__name__}_{request.function.__name__}"
    base_class = BaseIntegrationTestClass()
    base_class.test_name = test_name

    yield base_class

    # 清理测试数据生成器
    TestDataFactory.cleanup_generator(test_name)


@pytest_asyncio.fixture(scope="function")
async def setup_test_environment(
    test_base_class: BaseIntegrationTestClass,
    enhanced_test_db: AsyncSession,
    enhanced_client: AsyncClient
):
    """
    测试环境设置fixture

    设置测试环境并确保清理
    """
    try:
        await test_base_class.setup_test(enhanced_test_db, enhanced_client)
        yield test_base_class
    finally:
        await test_base_class.teardown_test()


@pytest.fixture(scope="function")
def concurrency_controller(global_test_semaphore):
    """
    并发控制器fixture

    控制测试并发执行
    """
    @asynccontextmanager
    async def _acquire_concurrency_slot(test_name: str):
        async with global_test_semaphore:
            test_logger.info(f"Acquired concurrency slot for: {test_name}")
            start_time = time.time()
            try:
                yield
            finally:
                duration = time.time() - start_time
                test_logger.info(f"Released concurrency slot for: {test_name} (duration: {duration:.2f}s)")

    return _acquire_concurrency_slot


@pytest.fixture(scope="function")
def test_isolation_controller():
    """
    测试隔离控制器fixture

    提供测试间的隔离机制
    """
    cleanup_tasks = []

    def register_cleanup_task(task: callable):
        """注册清理任务"""
        cleanup_tasks.append(task)

    async def execute_cleanup():
        """执行所有清理任务"""
        for task in reversed(cleanup_tasks):
            try:
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    task()
            except Exception as e:
                test_logger.error(f"Error executing cleanup task: {e}")

    yield register_cleanup_task

    # 测试结束后执行清理
    asyncio.create_task(execute_cleanup())


@pytest.fixture(scope="function")
def performance_monitor():
    """
    性能监控fixture

    监控测试执行性能
    """
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.checkpoints = []

        def start(self):
            self.start_time = time.time()

        def checkpoint(self, name: str):
            if self.start_time:
                elapsed = time.time() - self.start_time
                self.checkpoints.append((name, elapsed))
                test_logger.info(f"Performance checkpoint '{name}': {elapsed:.3f}s")

        def get_report(self) -> Dict[str, Any]:
            if not self.start_time:
                return {"error": "Monitor not started"}

            total_time = time.time() - self.start_time
            return {
                "total_time": total_time,
                "checkpoints": self.checkpoints,
                "checkpoint_count": len(self.checkpoints)
            }

    monitor = PerformanceMonitor()
    monitor.start()

    yield monitor

    # 输出性能报告
    report = monitor.get_report()
    test_logger.info(f"Test performance report: {report}")


@pytest.fixture(scope="function")
def test_data_validator():
    """
    测试数据验证器fixture

    提供通用的数据验证功能
    """
    class TestDataValidator:
        @staticmethod
        def validate_word_data(response_data: Dict[str, Any], expected_language: str = "en_US"):
            """验证单词数据格式"""
            required_fields = ["word", "phonetic", "partOfSpeech", "coreGame",
                              "scenarioFormal", "scenarioCasual", "etymologyBreakdown",
                              "etymologyStory", "memoryTrick", "commonMistakes"]

            for field in required_fields:
                assert field in response_data, f"Missing required field: {field}"
                assert response_data[field], f"Empty field: {field}"

            # 验证语言特定内容
            if expected_language == "zh_CN":
                assert any("中文" in str(response_data[field]) or "游戏" in str(response_data[field])
                          for field in ["coreGame", "scenarioFormal"]), "Missing Chinese content"
            else:
                assert any("English" in str(response_data[field]) or "game" in str(response_data[field]).lower()
                          for field in ["coreGame", "scenarioFormal"]), "Missing English content"

        @staticmethod
        def validate_api_response(response, expected_status: int = 200):
            """验证API响应格式"""
            assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                assert "success" in data, "Missing 'success' field in response"
                assert "data" in data, "Missing 'data' field in response"
                assert isinstance(data["success"], bool), "success must be boolean"

    return TestDataValidator()


# 全局测试清理函数
@pytest.fixture(scope="session", autouse=True)
def global_test_cleanup():
    """
    全局测试清理fixture

    在所有测试结束后执行全局清理
    """
    yield

    # 清理测试数据生成器
    TestDataFactory.cleanup_all()
    test_logger.info("Global test cleanup completed")


# 测试执行时间限制
@pytest.fixture(scope="function")
def test_timeout():
    """
    测试超时控制器fixture

    防止测试无限运行
    """
    @asynccontextmanager
    async def _with_timeout(timeout_seconds: int = 30):
        try:
            yield
        except asyncio.TimeoutError:
            pytest.fail(f"Test exceeded timeout of {timeout_seconds} seconds")

    return _with_timeout


# 错误处理和重试机制
@pytest.fixture(scope="function")
def error_handler():
    """
    错误处理fixture

    提供统一的错误处理和重试机制
    """
    class ErrorHandler:
        def __init__(self, max_retries: int = 3):
            self.max_retries = max_retries

        async def retry_on_failure(self, func, *args, **kwargs):
            """重试机制"""
            last_exception = None

            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        test_logger.warning(f"Attempt {attempt + 1} failed, retrying... Error: {e}")
                        await asyncio.sleep(0.5 * (attempt + 1))  # 指数退避
                    else:
                        test_logger.error(f"All {self.max_retries + 1} attempts failed")
                        raise last_exception

    return ErrorHandler()