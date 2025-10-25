"""
用户偏好设置API路由

实现用户偏好设置的获取和更新功能
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.logging import get_logger, log_with_context
from app.models import User
from app.schemas.common import ErrorCode, SuccessResponse
from app.schemas.user import (
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
)
from app.services.user_preferences import update_user_language_preference

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/preferences",
    response_model=SuccessResponse[UserPreferencesResponse],
    status_code=status.HTTP_200_OK,
    summary="获取用户偏好设置",
    description="获取当前用户的偏好设置，包括语言偏好等",
)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserPreferencesResponse]:
    """
    获取用户偏好设置

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 用户偏好设置

    Raises:
        HTTPException: 500 服务器内部错误
    """
    log_with_context(
        logger, "info", "Get user preferences requested", user_id=current_user.id
    )

    try:
        # 构造响应数据
        response_data = UserPreferencesResponse(
            id=current_user.id,
            email=current_user.email,
            membership_tier=current_user.membership_tier,
            membership_expires_at=current_user.membership_expires_at,
            email_verified=current_user.email_verified,
            preferred_language=current_user.preferred_language,
            created_at=current_user.created_at,
            last_login_at=current_user.last_login_at,
        )

        log_with_context(
            logger,
            "info",
            "User preferences retrieved successfully",
            user_id=current_user.id,
            preferred_language=current_user.preferred_language,
        )

        return SuccessResponse(data=response_data)

    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Failed to get user preferences",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": "获取用户偏好设置失败",
            },
        )


@router.put(
    "/preferences",
    response_model=SuccessResponse[UserPreferencesResponse],
    status_code=status.HTTP_200_OK,
    summary="更新用户偏好设置",
    description="更新当前用户的偏好设置，目前支持语言偏好",
)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserPreferencesResponse]:
    """
    更新用户偏好设置

    Args:
        preferences_data: 偏好设置数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 更新后的用户偏好设置

    Raises:
        HTTPException: 422 验证错误
        HTTPException: 500 服务器内部错误
    """
    log_with_context(
        logger,
        "info",
        "Update user preferences requested",
        user_id=current_user.id,
        new_language=preferences_data.preferred_language,
        old_language=current_user.preferred_language,
    )

    try:
        # 更新用户语言偏好
        update_user_language_preference(current_user, preferences_data.preferred_language)

        # 更新数据库
        current_user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(current_user)

        # 构造响应数据
        response_data = UserPreferencesResponse(
            id=current_user.id,
            email=current_user.email,
            membership_tier=current_user.membership_tier,
            membership_expires_at=current_user.membership_expires_at,
            email_verified=current_user.email_verified,
            preferred_language=current_user.preferred_language,
            created_at=current_user.created_at,
            last_login_at=current_user.last_login_at,
        )

        log_with_context(
            logger,
            "info",
            "User preferences updated successfully",
            user_id=current_user.id,
            preferred_language=current_user.preferred_language,
        )

        return SuccessResponse(data=response_data)

    except ValueError as e:
        # 验证错误
        log_with_context(
            logger,
            "warning",
            "Invalid preferences data",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": ErrorCode.VALIDATION_ERROR,
                "message": str(e),
            },
        )
    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Failed to update user preferences",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": "更新用户偏好设置失败",
            },
        )