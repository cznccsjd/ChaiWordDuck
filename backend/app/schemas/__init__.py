"""
Pydantic Schemas包

导出所有API请求和响应模型
"""
from app.schemas.common import APIResponse, ErrorDetail, ErrorResponse, SuccessResponse, ErrorCode
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

__all__ = [
    # 通用
    "APIResponse",
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    "ErrorCode",
    # 用户
    "UserRegisterRequest",
    "UserRegisterResponse",
    "UserLoginRequest",
    "UserLoginResponse",
    "UserInfo",
    "PasswordResetRequest",
    "PasswordResetResponse",
    "PasswordResetConfirmRequest",
    "PasswordResetConfirmResponse",
    "UserProfileResponse",
]
