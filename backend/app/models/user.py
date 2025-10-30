"""
用户模型

定义用户相关的数据库模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """
    用户表

    存储用户基本信息和会员状态
    """

    __tablename__ = "users"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 基本信息
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # 会员信息
    membership_tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="free",
        server_default="free",
    )
    membership_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 邮箱验证
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # 用户偏好设置
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="zh",
        server_default="zh",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 表约束
    __table_args__ = (
        CheckConstraint(
            "membership_tier IN ('free', 'premium')",
            name="check_membership_tier",
        ),
        CheckConstraint(
            "preferred_language IN ('zh', 'en')",
            name="check_preferred_language",
        ),
        Index("idx_users_membership", "membership_tier", "membership_expires_at"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, membership_tier={self.membership_tier})>"


class GuestSession(Base):
    """
    游客会话表

    存储游客的会话信息，用于限制查询次数
    """

    __tablename__ = "guest_sessions"

    # 主键
    guest_id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID

    # 游客标识
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # 支持IPv6
    user_agent_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # 查询信息
    last_query_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    query_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
    )

    # 表约束
    __table_args__ = (
        Index("idx_guest_last_query", "last_query_date"),
        Index("idx_guest_ip", "ip_address", "user_agent_hash"),
        Index("idx_guest_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<GuestSession(guest_id={self.guest_id}, query_count={self.query_count})>"


class PasswordResetToken(Base):
    """
    密码重置令牌表

    存储密码重置令牌
    """

    __tablename__ = "password_reset_tokens"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 用户关联
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    # 令牌信息
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 表约束
    __table_args__ = (Index("idx_token_expires", "expires_at", "is_used"),)

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, email={self.email}, is_used={self.is_used})>"
