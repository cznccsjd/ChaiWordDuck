"""
测试隔离和清理工具

提供完整的测试隔离机制，包括：
1. 数据库隔离
2. 文件系统隔离
3. 内存状态隔离
4. 外部服务隔离
5. 完整的清理机制
"""
import asyncio
import uuid
import tempfile
import shutil
import os
import gc
import weakref
from typing import Dict, List, Set, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import json
import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import class_mapper

logger = logging.getLogger("test.isolation")


@dataclass
class TestResource:
    """测试资源定义"""
    resource_id: str
    resource_type: str
    resource_data: Any
    created_at: float
    cleanup_func: Optional[Callable] = None
    cleanup_args: tuple = field(default_factory=tuple)
    cleanup_kwargs: dict = field(default_factory=dict)


class TestIsolationManager:
    """测试隔离管理器

    管理测试的隔离和清理
    """

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.test_id = str(uuid.uuid4())
        self.start_time = time.time()

        # 资源管理
        self.resources: Dict[str, TestResource] = {}
        self.database_records: List[Any] = []
        self.temp_files: List[str] = []
        self.temp_dirs: List[str] = []

        # 清理状态
        self.cleanup_executed = False
        self.cleanup_errors: List[Exception] = []

        # 弱引用跟踪
        self.object_refs: List[weakref.ref] = []

        # 日志
        self.logger = logging.getLogger(f"test.isolation.{test_name}")

    def register_resource(
        self,
        resource_type: str,
        resource_data: Any,
        cleanup_func: Optional[Callable] = None,
        cleanup_args: tuple = (),
        cleanup_kwargs: dict = None
    ) -> str:
        """注册测试资源"""
        resource_id = str(uuid.uuid4())
        resource = TestResource(
            resource_id=resource_id,
            resource_type=resource_type,
            resource_data=resource_data,
            created_at=time.time(),
            cleanup_func=cleanup_func,
            cleanup_args=cleanup_args,
            cleanup_kwargs=cleanup_kwargs or {}
        )

        self.resources[resource_id] = resource
        self.logger.debug(f"Registered resource: {resource_type}:{resource_id}")
        return resource_id

    def register_database_record(self, record: Any):
        """注册数据库记录"""
        self.database_records.append(record)
        self.logger.debug(f"Registered database record: {type(record).__name__}")

    def register_temp_file(self, file_path: str):
        """注册临时文件"""
        self.temp_files.append(file_path)
        self.logger.debug(f"Registered temp file: {file_path}")

    def register_temp_dir(self, dir_path: str):
        """注册临时目录"""
        self.temp_dirs.append(dir_path)
        self.logger.debug(f"Registered temp dir: {dir_path}")

    def track_object(self, obj: Any):
        """跟踪对象（使用弱引用）"""
        self.object_refs.append(weakref.ref(obj))
        self.logger.debug(f"Tracking object: {type(obj).__name__}")

    async def create_isolated_temp_dir(self) -> str:
        """创建隔离的临时目录"""
        temp_dir = tempfile.mkdtemp(prefix=f"test_{self.test_name}_")
        self.register_temp_dir(temp_dir)
        self.logger.info(f"Created isolated temp dir: {temp_dir}")
        return temp_dir

    async def create_isolated_temp_file(self, suffix: str = "", content: bytes = b"") -> str:
        """创建隔离的临时文件"""
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix=f"test_{self.test_name}_",
            delete=False
        ) as tmp_file:
            tmp_file.write(content)
            temp_file = tmp_file.name

        self.register_temp_file(temp_file)
        self.logger.info(f"Created isolated temp file: {temp_file}")
        return temp_file

    @asynccontextmanager
    async def isolated_filesystem(self) -> AsyncGenerator[str, None]:
        """隔离的文件系统上下文管理器"""
        temp_dir = await self.create_isolated_temp_dir()
        original_cwd = os.getcwd()

        try:
            os.chdir(temp_dir)
            yield temp_dir
        finally:
            os.chdir(original_cwd)

    async def cleanup(self):
        """执行完整的清理"""
        if self.cleanup_executed:
            self.logger.warning("Cleanup already executed")
            return

        self.logger.info(f"Starting cleanup for test: {self.test_name}")
        start_time = time.time()

        try:
            # 按顺序清理不同类型的资源
            cleanup_tasks = [
                self._cleanup_database_records(),
                self._cleanup_temp_files(),
                self._cleanup_temp_dirs(),
                self._cleanup_registered_resources(),
                self._force_garbage_collection()
            ]

            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            # 收集清理错误
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.cleanup_errors.append(result)
                    self.logger.error(f"Cleanup task {i} failed: {result}")

            self.cleanup_executed = True
            cleanup_time = time.time() - start_time
            self.logger.info(f"Cleanup completed for test: {self.test_name} (duration: {cleanup_time:.3f}s)")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            self.cleanup_errors.append(e)

    async def _cleanup_database_records(self):
        """清理数据库记录"""
        if not self.database_records:
            return

        self.logger.debug(f"Cleaning up {len(self.database_records)} database records")

        for record in self.database_records:
            try:
                # 获取记录的主键
                mapper = class_mapper(type(record))
                primary_key = mapper.primary_key_from_instance(record)
                if not primary_key or primary_key[0] is None:
                    continue

                # 获取表名和主键字段名
                table_name = mapper.local_table.name
                pk_column = mapper.primary_key[0].name

                # 构建删除语句
                delete_sql = text(f"DELETE FROM {table_name} WHERE {pk_column} = :pk")
                await record.session.execute(delete_sql, {"pk": primary_key[0]})
                await record.session.commit()

                self.logger.debug(f"Deleted record from {table_name} with PK {primary_key[0]}")

            except Exception as e:
                self.logger.error(f"Error deleting database record: {e}")

        self.database_records.clear()

    async def _cleanup_temp_files(self):
        """清理临时文件"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    self.logger.debug(f"Deleted temp file: {file_path}")
            except Exception as e:
                self.logger.error(f"Error deleting temp file {file_path}: {e}")

        self.temp_files.clear()

    async def _cleanup_temp_dirs(self):
        """清理临时目录"""
        for dir_path in self.temp_dirs:
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                    self.logger.debug(f"Deleted temp dir: {dir_path}")
            except Exception as e:
                self.logger.error(f"Error deleting temp dir {dir_path}: {e}")

        self.temp_dirs.clear()

    async def _cleanup_registered_resources(self):
        """清理注册的资源"""
        for resource_id, resource in self.resources.items():
            try:
                if resource.cleanup_func:
                    if asyncio.iscoroutinefunction(resource.cleanup_func):
                        await resource.cleanup_func(
                            resource.resource_data,
                            *resource.cleanup_args,
                            **resource.cleanup_kwargs
                        )
                    else:
                        resource.cleanup_func(
                            resource.resource_data,
                            *resource.cleanup_args,
                            **resource.cleanup_kwargs
                        )
                    self.logger.debug(f"Cleaned up resource: {resource_id}")
            except Exception as e:
                self.logger.error(f"Error cleaning up resource {resource_id}: {e}")

        self.resources.clear()

    async def _force_garbage_collection(self):
        """强制垃圾回收"""
        try:
            # 清理弱引用
            dead_refs = [ref for ref in self.object_refs if ref() is None]
            self.object_refs = [ref for ref in self.object_refs if ref() is not None]

            # 执行垃圾回收
            collected = gc.collect()
            self.logger.debug(f"Garbage collection collected {collected} objects")
            self.logger.debug(f"Cleaned up {len(dead_refs)} dead weak references")

        except Exception as e:
            self.logger.error(f"Error during garbage collection: {e}")

    def get_cleanup_report(self) -> Dict[str, Any]:
        """获取清理报告"""
        return {
            "test_name": self.test_name,
            "test_id": self.test_id,
            "cleanup_executed": self.cleanup_executed,
            "cleanup_errors": len(self.cleanup_errors),
            "resources_registered": len(self.resources),
            "database_records": len(self.database_records),
            "temp_files": len(self.temp_files),
            "temp_dirs": len(self.temp_dirs),
            "object_refs": len(self.object_refs),
            "execution_time": time.time() - self.start_time
        }


class DatabaseIsolationHelper:
    """数据库隔离助手

    提供数据库级别的隔离功能
    """

    def __init__(self, isolation_manager: TestIsolationManager):
        self.isolation_manager = isolation_manager

    async def create_test_schema(self, test_db: AsyncSession, schema_name: str) -> str:
        """创建测试专用schema"""
        try:
            # 创建schema
            await test_db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            await test_db.commit()
            self.isolation_manager.register_resource(
                "database_schema",
                schema_name,
                self._drop_schema,
                (test_db, schema_name)
            )
            return schema_name
        except Exception as e:
            # 如果schema创建失败，使用表级隔离
            self.isolation_manager.logger.warning(f"Schema creation failed, using table-level isolation: {e}")
            return None

    async def _drop_schema(self, schema_name: str, test_db: AsyncSession):
        """删除schema"""
        try:
            await test_db.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            await test_db.commit()
        except Exception as e:
            self.isolation_manager.logger.error(f"Error dropping schema {schema_name}: {e}")

    async def create_isolated_user(
        self,
        test_db: AsyncSession,
        email: str,
        password: str,
        **user_attrs
    ):
        """创建隔离的测试用户"""
        from app.models.user import User
        from app.core.security import get_password_hash

        user = User(
            email=email,
            password_hash=get_password_hash(password),
            **user_attrs
        )

        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        self.isolation_manager.register_database_record(user)
        return user

    async def create_isolated_word_data(
        self,
        test_db: AsyncSession,
        word_data: Dict[str, Any]
    ):
        """创建隔离的单词数据"""
        from app.models.word import Word

        word = Word(**word_data)

        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        self.isolation_manager.register_database_record(word)
        return word


class GlobalIsolationRegistry:
    """全局隔离注册表

    管理所有测试的隔离管理器
    """

    def __init__(self):
        self.isolation_managers: Dict[str, TestIsolationManager] = {}
        self._lock = asyncio.Lock()

    async def register_test(self, test_name: str) -> TestIsolationManager:
        """注册测试隔离管理器"""
        async with self._lock:
            if test_name in self.isolation_managers:
                self.isolation_managers[test_name].cleanup()
                del self.isolation_managers[test_name]

            manager = TestIsolationManager(test_name)
            self.isolation_managers[test_name] = manager
            return manager

    async def unregister_test(self, test_name: str):
        """注销测试隔离管理器"""
        async with self._lock:
            if test_name in self.isolation_managers:
                manager = self.isolation_managers[test_name]
                await manager.cleanup()
                del self.isolation_managers[test_name]

    async def cleanup_all_tests(self):
        """清理所有测试"""
        async with self._lock:
            for manager in self.isolation_managers.values():
                await manager.cleanup()
            self.isolation_managers.clear()

    def get_isolation_report(self) -> Dict[str, Any]:
        """获取隔离报告"""
        return {
            "active_tests": len(self.isolation_managers),
            "test_details": {
                test_name: manager.get_cleanup_report()
                for test_name, manager in self.isolation_managers.items()
            }
        }


# 全局隔离注册表实例
_global_registry = GlobalIsolationRegistry()


def get_global_registry() -> GlobalIsolationRegistry:
    """获取全局隔离注册表"""
    return _global_registry


@asynccontextmanager
async def isolated_test_context(test_name: str):
    """隔离测试上下文管理器"""
    registry = get_global_registry()
    manager = await registry.register_test(test_name)

    try:
        yield manager
    finally:
        await registry.unregister_test(test_name)


# 便捷函数
async def create_isolated_test_user(
    test_db: AsyncSession,
    test_name: str,
    email: str,
    password: str,
    **user_attrs
):
    """创建隔离的测试用户"""
    registry = get_global_registry()
    manager = await registry.register_test(test_name)
    helper = DatabaseIsolationHelper(manager)
    return await helper.create_isolated_user(test_db, email, password, **user_attrs)


async def create_isolated_temp_file(test_name: str, suffix: str = "", content: bytes = b"") -> str:
    """创建隔离的临时文件"""
    registry = get_global_registry()
    manager = await registry.register_test(test_name)
    return await manager.create_isolated_temp_file(suffix, content)