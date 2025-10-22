"""
依赖注入模块

提供FastAPI路由依赖项
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis_client
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.common import ErrorCode

# 配置日志
logger = logging.getLogger(__name__)

# HTTP Bearer认证 - auto_error=False允许我们自定义错误处理
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前登录用户

    依赖注入函数，用于需要认证的路由

    Args:
        credentials: JWT令牌凭证（可选）
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 401 未授权
    """
    # 检查是否提供了认证凭证
    if credentials is None:
        logger.warning("认证失败：请求未包含Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.UNAUTHORIZED,
                "message": "缺少认证凭证，请提供有效的访问令牌",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # 解码JWT
    try:
        payload = decode_access_token(token)
    except ExpiredSignatureError:
        # Token过期
        logger.warning("认证失败：访问令牌已过期")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.TOKEN_EXPIRED,
                "message": "认证令牌已过期，请重新登录",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        # Token无效
        logger.warning(f"认证失败：无效的访问令牌 - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.TOKEN_INVALID,
                "message": "无效的认证令牌",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户ID
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        logger.warning("认证失败：访问令牌中缺少用户ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.TOKEN_INVALID,
                "message": "令牌中缺少用户ID",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"认证失败：用户ID {user_id} 不存在")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.USER_NOT_FOUND,
                "message": "用户不存在",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"用户认证成功：user_id={user_id}, email={user.email}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户

    可在此处添加额外的用户状态检查（如账户是否被禁用）

    Args:
        current_user: 当前用户

    Returns:
        User: 当前活跃用户

    Raises:
        HTTPException: 403 禁止访问
    """
    # 未来可添加账户状态检查
    # if current_user.is_banned:
    #     raise HTTPException(...)

    return current_user


async def get_current_premium_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    获取当前高级会员用户

    用于需要高级会员权限的路由

    Args:
        current_user: 当前用户

    Returns:
        User: 当前高级会员用户

    Raises:
        HTTPException: 403 禁止访问
    """
    from datetime import datetime, timezone

    if current_user.membership_tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.INSUFFICIENT_PERMISSIONS,
                "message": "此功能需要高级会员权限",
            },
        )

    # 检查会员是否过期
    if current_user.membership_expires_at and current_user.membership_expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.INSUFFICIENT_PERMISSIONS,
                "message": "高级会员已过期，请续费",
            },
        )

    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    可选认证：获取当前用户（如果已登录）

    支持游客模式的依赖注入函数。
    - 如果提供了有效token，返回User对象
    - 如果未提供token或token无效，返回None（游客模式）

    Args:
        credentials: JWT令牌凭证（可选）
        db: 数据库会话

    Returns:
        Optional[User]: User对象或None（游客模式）

    Examples:
        >>> # 在路由中使用
        >>> @router.get("/words/query/{word}")
        >>> async def query_word(
        ...     word: str,
        ...     current_user: Optional[User] = Depends(get_optional_user),
        ... ):
        ...     if current_user is None:
        ...         # 游客模式逻辑
        ...     else:
        ...         # 注册用户逻辑
    """
    if credentials is None:
        # 游客模式
        logger.debug("请求未包含认证信息，使用游客模式")
        return None

    try:
        # 尝试认证（复用现有逻辑）
        return await get_current_user(credentials, db)
    except HTTPException as e:
        # 认证失败，降级为游客模式
        logger.warning(f"认证失败，降级为游客模式：{e.detail}")
        return None


async def get_rate_limit_service(
    db: AsyncSession = Depends(get_db),
) -> "RateLimitService":
    """
    获取查询限制服务实例

    自动注入Redis客户端（如果可用），提供缓存优化的查询限制功能。

    Args:
        db: 数据库会话

    Returns:
        RateLimitService: 查询限制服务实例
    """
    from app.services.rate_limit import RateLimitService

    try:
        # 尝试获取Redis客户端
        redis_client = await get_redis_client()
        return RateLimitService(db, redis_client)
    except Exception as e:
        # Redis不可用时使用数据库模式
        logger.warning(f"Redis不可用，查询限制服务将使用数据库模式: {e}")
        return RateLimitService(db, None)

