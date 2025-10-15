"""
收藏模型

定义用户收藏相关的数据库模型
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Favorite(Base):
    """
    收藏表

    存储用户收藏的单词
    """

    __tablename__ = "favorites"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
    )

    # 表约束
    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="uq_user_word_favorite"),
        Index("idx_favorites_user", "user_id"),
        Index("idx_favorites_created", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<Favorite(id={self.id}, user_id={self.user_id}, word_id={self.word_id})>"
