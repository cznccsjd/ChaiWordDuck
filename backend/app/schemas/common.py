"""
通用API响应模型
"""
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    统一API响应格式

    success: 请求是否成功
    data: 响应数据
    error: 错误信息
    timestamp: 响应时间戳
    """

    success: bool = Field(..., description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    error: Optional["ErrorDetail"] = Field(None, description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")


class ErrorDetail(BaseModel):
    """错误详情"""

    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[dict[str, Any]] = Field(None, description="详细错误信息")


class SuccessResponse(APIResponse[T], Generic[T]):
    """成功响应"""

    success: bool = True
    error: None = None


class ErrorResponse(APIResponse[None]):
    """错误响应"""

    success: bool = False
    data: None = None


# 常用错误代码
class ErrorCode:
    """错误代码常量"""

    # 认证相关 (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # 权限相关 (403)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # 资源相关 (404)
    NOT_FOUND = "NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    WORD_NOT_FOUND = "WORD_NOT_FOUND"

    # 验证相关 (422)
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    WEAK_PASSWORD = "WEAK_PASSWORD"

    # 业务逻辑 (400)
    BAD_REQUEST = "BAD_REQUEST"
    QUERY_LIMIT_EXCEEDED = "QUERY_LIMIT_EXCEEDED"
    FAVORITE_LIMIT_EXCEEDED = "FAVORITE_LIMIT_EXCEEDED"
    ALREADY_FAVORITED = "ALREADY_FAVORITED"
    PASSWORD_RESET_TOKEN_INVALID = "PASSWORD_RESET_TOKEN_INVALID"
    PASSWORD_RESET_TOKEN_EXPIRED = "PASSWORD_RESET_TOKEN_EXPIRED"

    # 限流相关 (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # 服务器错误 (500)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    AI_GENERATION_FAILED = "AI_GENERATION_FAILED"
