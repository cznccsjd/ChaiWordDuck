"""
用户认证API路由

实现用户注册、登录、密码找回等功能
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.logging import get_logger, log_with_context
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, PasswordResetToken
from app.schemas.common import ErrorCode, ErrorDetail, ErrorResponse, SuccessResponse
from app.schemas.user import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserInfo,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    UserProfileResponse,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/register",
    response_model=SuccessResponse[UserRegisterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账号",
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserRegisterResponse]:
    """
    用户注册

    Args:
        data: 注册数据（邮箱、密码）
        db: 数据库会话

    Returns:
        SuccessResponse: 包含用户信息和JWT token

    Raises:
        HTTPException: 422 邮箱已存在
    """
    log_with_context(logger, "info", "User registration attempt", email=data.email)

    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        log_with_context(logger, "warning", "Registration failed: email already exists", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": ErrorCode.EMAIL_ALREADY_EXISTS,
                "message": "该邮箱已注册，请直接登录",
            },
        )

    # 创建用户
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        membership_tier="free",
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)

        log_with_context(logger, "info", "User registered successfully", user_id=user.id, email=user.email)

        # 生成JWT token
        access_token = create_access_token(data={"sub": str(user.id)})

        # 构造响应
        response_data = UserRegisterResponse(
            id=user.id,
            email=user.email,
            membership_tier=user.membership_tier,
            created_at=user.created_at,
            access_token=access_token,
            token_type="bearer",
        )

        return SuccessResponse(data=response_data)

    except IntegrityError as e:
        # 数据库唯一约束冲突（并发注册相同邮箱）
        await db.rollback()
        log_with_context(logger, "warning", "Registration failed: database integrity error", error=str(e), email=data.email)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": ErrorCode.EMAIL_ALREADY_EXISTS,
                "message": "该邮箱已注册，请直接登录",
            },
        )
    except Exception as e:
        await db.rollback()
        log_with_context(logger, "error", "User registration failed", error=str(e), email=data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.DATABASE_ERROR,
                "message": "注册失败，请稍后重试",
            },
        )


@router.post(
    "/login",
    response_model=SuccessResponse[UserLoginResponse],
    status_code=status.HTTP_200_OK,
    summary="用户登录",
    description="使用邮箱和密码登录",
)
async def login(
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserLoginResponse]:
    """
    用户登录

    Args:
        data: 登录数据（邮箱、密码）
        db: 数据库会话

    Returns:
        SuccessResponse: 包含JWT token和用户信息

    Raises:
        HTTPException: 401 邮箱或密码错误
    """
    log_with_context(logger, "info", "User login attempt", email=data.email)

    # 查询用户
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # 验证用户存在且密码正确
    if not user or not verify_password(data.password, user.password_hash):
        log_with_context(logger, "warning", "Login failed: invalid credentials", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": ErrorCode.INVALID_CREDENTIALS,
                "message": "邮箱或密码错误",
            },
        )

    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    log_with_context(logger, "info", "User logged in successfully", user_id=user.id, email=user.email)

    # 生成JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    # 构造响应
    user_info = UserInfo.model_validate(user)
    response_data = UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_info,
    )

    return SuccessResponse(data=response_data)


@router.get(
    "/me",
    response_model=SuccessResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="获取当前用户信息",
    description="需要Bearer Token认证",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse[UserProfileResponse]:
    """
    获取当前登录用户信息

    Args:
        current_user: 当前用户（通过JWT验证）

    Returns:
        SuccessResponse: 用户信息
    """
    log_with_context(logger, "info", "User profile accessed", user_id=current_user.id)

    # 构造响应
    profile_data = UserProfileResponse.model_validate(current_user)

    return SuccessResponse(data=profile_data)


@router.post(
    "/password-reset",
    response_model=SuccessResponse[PasswordResetResponse],
    status_code=status.HTTP_200_OK,
    summary="请求密码重置",
    description="发送密码重置邮件",
)
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[PasswordResetResponse]:
    """
    请求密码重置

    Args:
        data: 重置请求数据（邮箱）
        db: 数据库会话

    Returns:
        SuccessResponse: 提示邮件已发送

    Note:
        出于安全考虑，无论用户是否存在都返回成功
    """
    log_with_context(logger, "info", "Password reset requested", email=data.email)

    # 查询用户
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user:
        # 生成重置token
        import secrets

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # 保存到数据库
        reset_token = PasswordResetToken(
            user_id=user.id,
            email=user.email,
            token=token,
            expires_at=expires_at,
        )
        db.add(reset_token)
        await db.commit()

        log_with_context(
            logger,
            "info",
            "Password reset token created",
            user_id=user.id,
            email=user.email,
            expires_at=expires_at.isoformat(),
        )

        # 发送邮件（实际项目中需要实现邮件服务）
        # await send_password_reset_email(user.email, token)

    # 无论用户是否存在都返回相同响应（安全考虑）
    return SuccessResponse(
        data=PasswordResetResponse(message="密码重置邮件已发送，请查收")
    )


@router.post(
    "/password-reset/confirm",
    response_model=SuccessResponse[PasswordResetConfirmResponse],
    status_code=status.HTTP_200_OK,
    summary="确认密码重置",
    description="使用重置token设置新密码",
)
async def confirm_password_reset(
    data: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[PasswordResetConfirmResponse]:
    """
    确认密码重置

    Args:
        data: 重置确认数据（token、新密码）
        db: 数据库会话

    Returns:
        SuccessResponse: 提示密码重置成功

    Raises:
        HTTPException: 400 token无效或已过期
    """
    log_with_context(logger, "info", "Password reset confirmation attempt")

    # 使用SELECT FOR UPDATE行级锁查询reset token,防止并发使用
    result = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token == data.token)
        .where(PasswordResetToken.is_used.is_(False))
        .with_for_update()
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        log_with_context(logger, "warning", "Invalid password reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.PASSWORD_RESET_TOKEN_INVALID,
                "message": "无效的重置令牌",
            },
        )

    # 检查是否过期
    if reset_token.expires_at < datetime.now(timezone.utc):
        log_with_context(logger, "warning", "Expired password reset token", email=reset_token.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.PASSWORD_RESET_TOKEN_EXPIRED,
                "message": "重置令牌已过期，请重新申请",
            },
        )

    # 查询用户
    user_result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        log_with_context(logger, "error", "User not found for password reset", user_id=reset_token.user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.USER_NOT_FOUND,
                "message": "用户不存在",
            },
        )

    # 更新密码
    user.password_hash = get_password_hash(data.new_password)

    # 标记token为已使用
    reset_token.is_used = True
    reset_token.used_at = datetime.now(timezone.utc)

    await db.commit()

    log_with_context(logger, "info", "Password reset successful", user_id=user.id, email=user.email)

    return SuccessResponse(
        data=PasswordResetConfirmResponse(message="密码重置成功，请使用新密码登录")
    )
