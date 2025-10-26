"""
并发安全控制机制

提供测试并发执行时的安全控制，包括：
1. 数据库访问控制
2. 测试资源锁定
3. 竞态条件预防
4. 并发监控和报告
"""
import asyncio
import threading
import time
import uuid
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from enum import Enum
import logging

logger = logging.getLogger("test.concurrency")


class LockType(Enum):
    """锁类型枚举"""
    DATABASE = "database"
    USER_DATA = "user_data"
    WORD_DATA = "word_data"
    MOCK_SERVICE = "mock_service"
    GENERAL_RESOURCE = "general_resource"


@dataclass
class LockInfo:
    """锁信息"""
    lock_id: str
    lock_type: LockType
    resource_key: str
    thread_id: int
    test_name: str
    acquired_at: float
    timeout: float = 30.0

    @property
    def is_expired(self) -> bool:
        """检查锁是否已过期"""
        return time.time() - self.acquired_at > self.timeout


@dataclass
class ConcurrencyStats:
    """并发统计信息"""
    total_locks_acquired: int = 0
    total_locks_released: int = 0
    concurrent_tests: int = 0
    max_concurrent_tests: int = 0
    total_execution_time: float = 0.0
    resource_conflicts: int = 0
    timeouts: int = 0

    def update_max_concurrent(self, current: int):
        """更新最大并发数"""
        if current > self.max_concurrent_tests:
            self.max_concurrent_tests = current


class ConcurrencyController:
    """并发控制器

    管理测试的并发执行和资源访问
    """

    def __init__(self, max_concurrent_tests: int = 3, default_timeout: float = 30.0):
        self.max_concurrent_tests = max_concurrent_tests
        self.default_timeout = default_timeout

        # 锁管理
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock_info: Dict[str, LockInfo] = {}
        self._lock_semaphore = asyncio.Lock()

        # 并发控制
        self._test_semaphore = asyncio.Semaphore(max_concurrent_tests)
        self._active_tests: Set[str] = set()
        self._test_start_times: Dict[str, float] = {}

        # 统计信息
        self.stats = ConcurrencyStats()

        # 后台任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        # 线程安全锁（用于同步操作）
        self._thread_lock = threading.Lock()

    async def start(self):
        """启动并发控制器"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_locks())
        logger.info("Concurrency controller started")

    async def stop(self):
        """停止并发控制器"""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 等待所有锁被释放
        await self._wait_for_all_locks_release()
        logger.info("Concurrency controller stopped")

    async def _cleanup_expired_locks(self):
        """后台任务：清理过期锁"""
        while self._running:
            try:
                await asyncio.sleep(5)  # 每5秒检查一次
                await self._release_expired_locks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in lock cleanup task: {e}")

    async def _release_expired_locks(self):
        """释放过期的锁"""
        async with self._lock_semaphore:
            expired_locks = [
                lock_id for lock_id, info in self._lock_info.items()
                if info.is_expired
            ]

            for lock_id in expired_locks:
                info = self._lock_info[lock_id]
                logger.warning(f"Releasing expired lock: {lock_id} (test: {info.test_name})")
                await self._release_lock_internal(lock_id)
                self.stats.timeouts += 1

    @asynccontextmanager
    async def acquire_test_slot(self, test_name: str):
        """获取测试执行槽位"""
        test_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # 获取信号量
            await self._test_semaphore.acquire()

            async with self._thread_lock:
                self._active_tests.add(test_id)
                self._test_start_times[test_id] = start_time
                current_concurrent = len(self._active_tests)
                self.stats.concurrent_tests = current_concurrent
                self.stats.update_max_concurrent(current_concurrent)

            logger.info(f"Test slot acquired: {test_name} (ID: {test_id})")
            yield test_id

        finally:
            # 释放信号量
            self._test_semaphore.release()

            async with self._thread_lock:
                self._active_tests.discard(test_id)
                self._test_start_times.pop(test_id, None)
                self.stats.total_execution_time += time.time() - start_time

            logger.info(f"Test slot released: {test_name} (ID: {test_id})")

    @asynccontextmanager
    async def acquire_resource_lock(
        self,
        lock_type: LockType,
        resource_key: str,
        test_name: str,
        timeout: Optional[float] = None
    ):
        """获取资源锁"""
        lock_id = f"{lock_type.value}:{resource_key}"
        timeout = timeout or self.default_timeout

        try:
            # 等待获取锁
            lock = await self._get_lock(lock_id)
            await asyncio.wait_for(lock.acquire(), timeout=timeout)

            # 记录锁信息
            lock_info = LockInfo(
                lock_id=lock_id,
                lock_type=lock_type,
                resource_key=resource_key,
                thread_id=threading.get_ident(),
                test_name=test_name,
                acquired_at=time.time(),
                timeout=timeout
            )

            async with self._lock_semaphore:
                self._lock_info[lock_id] = lock_info
                self.stats.total_locks_acquired += 1

            logger.debug(f"Lock acquired: {lock_id} by {test_name}")
            yield lock_id

        except asyncio.TimeoutError:
            self.stats.timeouts += 1
            self.stats.resource_conflicts += 1
            logger.error(f"Timeout acquiring lock: {lock_id} for {test_name}")
            raise

        except Exception as e:
            self.stats.resource_conflicts += 1
            logger.error(f"Error acquiring lock {lock_id} for {test_name}: {e}")
            raise

        finally:
            await self._release_lock(lock_id)

    async def _get_lock(self, lock_id: str) -> asyncio.Lock:
        """获取或创建锁对象"""
        if lock_id not in self._locks:
            self._locks[lock_id] = asyncio.Lock()
        return self._locks[lock_id]

    async def _release_lock(self, lock_id: str):
        """释放锁"""
        await self._release_lock_internal(lock_id)
        self.stats.total_locks_released += 1
        logger.debug(f"Lock released: {lock_id}")

    async def _release_lock_internal(self, lock_id: str):
        """内部锁释放逻辑"""
        if lock_id in self._locks:
            self._locks[lock_id].release()
            # 如果没有其他等待者，可以删除锁对象
            if not self._locks[lock_id].locked():
                del self._locks[lock_id]

        async with self._lock_semaphore:
            self._lock_info.pop(lock_id, None)

    async def _wait_for_all_locks_release(self, timeout: float = 10.0):
        """等待所有锁被释放"""
        start_time = time.time()
        while self._lock_info and time.time() - start_time < timeout:
            await asyncio.sleep(0.1)

        if self._lock_info:
            logger.warning(f"Still have active locks after timeout: {list(self._lock_info.keys())}")

    def get_active_locks(self) -> Dict[str, LockInfo]:
        """获取活跃锁信息"""
        return self._lock_info.copy()

    def get_active_tests(self) -> Set[str]:
        """获取活跃测试"""
        return self._active_tests.copy()

    def get_concurrency_report(self) -> Dict[str, Any]:
        """获取并发报告"""
        return {
            "stats": {
                "total_locks_acquired": self.stats.total_locks_acquired,
                "total_locks_released": self.stats.total_locks_released,
                "current_concurrent_tests": len(self._active_tests),
                "max_concurrent_tests": self.stats.max_concurrent_tests,
                "total_execution_time": self.stats.total_execution_time,
                "resource_conflicts": self.stats.resource_conflicts,
                "timeouts": self.stats.timeouts,
            },
            "active_locks": len(self._lock_info),
            "active_tests": len(self._active_tests),
            "lock_details": {
                lock_id: {
                    "type": info.lock_type.value,
                    "test_name": info.test_name,
                    "acquired_at": info.acquired_at,
                    "duration": time.time() - info.acquired_at
                }
                for lock_id, info in self._lock_info.items()
            }
        }


class DatabaseIsolationManager:
    """数据库隔离管理器

    提供测试间的数据库访问隔离
    """

    def __init__(self, concurrency_controller: ConcurrencyController):
        self.concurrency_controller = concurrency_controller
        self._test_schemas: Dict[str, str] = {}
        self._schema_locks: Dict[str, asyncio.Lock] = {}

    @asynccontextmanager
    async def isolated_database_session(self, test_name: str, session_factory):
        """创建隔离的数据库会话"""
        schema_name = f"test_schema_{test_name}_{uuid.uuid4().hex[:8]}"

        try:
            # 获取数据库锁
            async with self.concurrency_controller.acquire_resource_lock(
                LockType.DATABASE, schema_name, test_name
            ):
                # 创建测试专用schema（这里简化处理）
                # 在实际实现中可能需要创建真实的数据库schema
                logger.info(f"Creating isolated database schema: {schema_name}")

                self._test_schemas[test_name] = schema_name

                # 创建会话
                async with session_factory() as session:
                    yield session, schema_name

        finally:
            # 清理schema
            await self._cleanup_schema(schema_name, test_name)
            self._test_schemas.pop(test_name, None)

    async def _cleanup_schema(self, schema_name: str, test_name: str):
        """清理测试schema"""
        # 在实际实现中，这里需要删除schema及其中的所有数据
        logger.info(f"Cleaning up schema: {schema_name} for test: {test_name}")


# 全局并发控制器实例
_global_concurrency_controller: Optional[ConcurrencyController] = None


def get_concurrency_controller() -> ConcurrencyController:
    """获取全局并发控制器"""
    global _global_concurrency_controller
    if _global_concurrency_controller is None:
        _global_concurrency_controller = ConcurrencyController()
    return _global_concurrency_controller


async def start_global_concurrency_controller():
    """启动全局并发控制器"""
    controller = get_concurrency_controller()
    await controller.start()


async def stop_global_concurrency_controller():
    """停止全局并发控制器"""
    controller = get_concurrency_controller()
    await controller.stop()


# 便捷装饰器和上下文管理器
@asynccontextmanager
async def concurrent_test_execution(test_name: str):
    """并发测试执行上下文管理器"""
    controller = get_concurrency_controller()
    async with controller.acquire_test_slot(test_name):
        yield


@asynccontextmanager
async def locked_resource_access(
    lock_type: LockType,
    resource_key: str,
    test_name: str,
    timeout: Optional[float] = None
):
    """资源访问锁上下文管理器"""
    controller = get_concurrency_controller()
    async with controller.acquire_resource_lock(lock_type, resource_key, test_name, timeout):
        yield


# 并发测试执行函数
async def run_concurrent_tests(test_functions: List[Callable], max_concurrent: Optional[int] = None):
    """并发执行测试函数"""
    controller = get_concurrency_controller()
    if max_concurrent:
        original_max = controller.max_concurrent_tests
        controller.max_concurrent_tests = max_concurrent

    try:
        semaphore = asyncio.Semaphore(controller.max_concurrent_tests)

        async def run_with_semaphore(test_func):
            async with semaphore:
                return await test_func()

        tasks = [run_with_semaphore(test_func) for test_func in test_functions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    finally:
        if max_concurrent:
            controller.max_concurrent_tests = original_max