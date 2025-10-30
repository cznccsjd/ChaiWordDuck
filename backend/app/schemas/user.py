"""
用户相关的Pydantic Schemas

定义API请求和响应的数据模型
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ========== 用户注册 ==========


class UserRegisterRequest(BaseModel):
    """用户注册请求"""

    email: EmailStr = Field(..., description="邮箱地址", examples=["user@example.com"])
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="密码（至少8位，包含字母和数字）",
        examples=["SecurePass123"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


class UserRegisterResponse(BaseModel):
    """用户注册响应"""

    id: int
    email: str
    membership_tier: str
    created_at: datetime
    access_token: str
    token_type: str = "bearer"

    model_config = {"from_attributes": True}


# ========== 用户登录 ==========


class UserLoginRequest(BaseModel):
    """用户登录请求"""

    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class UserInfo(BaseModel):
    """用户信息"""

    id: int
    email: str
    membership_tier: str
    membership_expires_at: Optional[datetime] = None
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserLoginResponse(BaseModel):
    """用户登录响应"""

    access_token: str
    token_type: str = "bearer"
    user: UserInfo


# ========== 密码找回 ==========


class PasswordResetRequest(BaseModel):
    """密码找回请求"""

    email: EmailStr = Field(..., description="注册时使用的邮箱地址")


class PasswordResetResponse(BaseModel):
    """密码找回响应"""

    message: str = "密码重置邮件已发送，请查收"


class PasswordResetConfirmRequest(BaseModel):
    """密码重置确认请求"""

    token: str = Field(..., description="密码重置令牌")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="新密码（至少8位，包含字母和数字）",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


class PasswordResetConfirmResponse(BaseModel):
    """密码重置确认响应"""

    message: str = "密码重置成功，请使用新密码登录"


# ========== 用户信息 ==========


class UserProfileResponse(BaseModel):
    """用户个人信息响应"""

    id: int
    email: str
    membership_tier: str
    membership_expires_at: Optional[datetime] = None
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    # 统计信息（后续实现）
    total_queries: int = 0
    total_favorites: int = 0
    continuous_days: int = 0

    model_config = {"from_attributes": True}


# ========== 用户偏好设置 ==========


class UserPreferencesResponse(BaseModel):
    """用户偏好设置响应"""

    id: int
    email: str
    membership_tier: str
    membership_expires_at: Optional[datetime] = None
    email_verified: bool
    preferred_language: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserPreferencesUpdateRequest(BaseModel):
    """用户偏好更新请求"""

    preferred_language: str = Field(..., description="首选语言", examples=["zh", "en"])

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """验证语言代码"""
        if not v or not v.strip():
            raise ValueError("preferred_language不能为空")

        v = v.strip()
        supported_languages = ["zh", "en"]
        if v not in supported_languages:
            raise ValueError("不支持的语言代码，仅支持: zh, en")
        return v
