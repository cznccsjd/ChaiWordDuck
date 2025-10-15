"""
依赖注入模块

提供FastAPI路由依赖项
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.common import ErrorCode

# HTTP Bearer认证
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前登录用户

    依赖注入函数，用于需要认证的路由

    Args:
        credentials: JWT令牌凭证
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 401 未授权
    """
    token = credentials.credentials

    # 解码JWT
    try:
        payload = decode_access_token(token)
    except ExpiredSignatureError:
        # Token过期
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.TOKEN_EXPIRED,
                "message": "认证令牌已过期，请重新登录",
            },
        )
    except JWTError:
        # Token无效
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.TOKEN_INVALID,
                "message": "无效的认证令牌",
            },
        )

    # 获取用户ID
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.TOKEN_INVALID,
                "message": "令牌中缺少用户ID",
            },
        )

    # 查询用户
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.USER_NOT_FOUND,
                "message": "用户不存在",
            },
        )

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
