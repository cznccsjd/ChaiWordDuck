"""
Pytest配置和全局fixtures

提供测试数据库、测试客户端等fixtures
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.models import User  # noqa: F401

# 测试数据库URL（使用内存SQLite或独立测试数据库）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # 内存数据库，每次测试运行后销毁

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    创建测试数据库session

    每个测试函数执行前创建所有表，执行后删除所有表
    """
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建session
    async with TestSessionLocal() as session:
        yield session

    # 删除所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建测试客户端

    覆盖依赖注入的数据库session为测试session
    """
    from app.main import app

    # 覆盖数据库依赖
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # 创建异步HTTP客户端
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # 清除依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user_data() -> dict:
    """测试用户数据"""
    return {
        "email": "test@example.com",
        "password": "TestPass123",
    }


@pytest_asyncio.fixture(scope="function")
async def created_user(test_db: AsyncSession, test_user_data: dict) -> User:
    """
    创建测试用户

    返回已保存到数据库的用户对象
    """
    from app.core.security import get_password_hash
    from app.models import User

    user = User(
        email=test_user_data["email"],
        password_hash=get_password_hash(test_user_data["password"]),
        membership_tier="free",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    return user


@pytest.fixture(scope="function")
def auth_headers(created_user: User) -> dict:
    """
    认证headers

    生成JWT token用于测试需要认证的API
    """
    from app.core.security import create_access_token

    access_token = create_access_token(data={"sub": str(created_user.id)})
    return {"Authorization": f"Bearer {access_token}"}
