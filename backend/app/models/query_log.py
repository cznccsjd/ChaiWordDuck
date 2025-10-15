"""
查询日志模型

定义单词查询日志的数据库模型，用于限制查询次数
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class QueryLog(Base):
    """
    查询日志表

    记录用户和游客的单词查询历史，用于实现查询次数限制
    """

    __tablename__ = "query_logs"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 外键（用户或游客，二选一）
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    guest_session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("guest_sessions.guest_id", ondelete="CASCADE"), nullable=True, index=True
    )

    # 查询信息
    word_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
    )

    # 表约束
    __table_args__ = (
        # 确保要么是用户查询，要么是游客查询，不能都为空或都存在
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_session_id IS NULL) OR "
            "(user_id IS NULL AND guest_session_id IS NOT NULL)",
            name="check_query_log_owner",
        ),
        Index("idx_query_logs_user_date", "user_id", "query_date"),
        Index("idx_query_logs_guest_date", "guest_session_id", "query_date"),
        Index("idx_query_logs_word", "word_id"),
    )

    def __repr__(self) -> str:
        owner = f"user_id={self.user_id}" if self.user_id else f"guest={self.guest_session_id}"
        return f"<QueryLog(id={self.id}, {owner}, word_id={self.word_id}, date={self.query_date})>"
