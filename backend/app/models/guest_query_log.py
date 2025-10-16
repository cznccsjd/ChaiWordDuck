"""
游客查询日志模型

记录游客（未登录用户）的查询历史，用于实现查询限流
"""
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class GuestQueryLog(Base):
    """
    游客查询日志表

    用于追踪游客（未认证用户）的单词查询历史，实现查询限流策略。

    Attributes:
        id: 主键ID
        identifier: 游客唯一标识符（MVP阶段使用IP地址）
        word_id: 查询的单词ID（外键关联words表）
        query_date: 查询日期（用于按天统计）
        created_at: 记录创建时间

    Indexes:
        idx_guest_identifier_date: 复合索引，优化按游客和日期查询
        uk_guest_word_date: 唯一索引，防止同一游客同一天查询同一单词重复记录
    """

    __tablename__ = "guest_query_logs"

    # 基本字段
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    identifier = Column(
        String(255),
        nullable=False,
        comment="游客标识符（IP地址，未来可升级为IP+UA hash）",
    )
    word_id = Column(
        Integer,
        ForeignKey("words.id", ondelete="CASCADE"),
        nullable=False,
        comment="查询的单词ID",
    )
    query_date = Column(
        Date,
        nullable=False,
        comment="查询日期（用于按天统计查询次数）",
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="记录创建时间",
    )

    # 关系
    word = relationship("Word", backref="guest_queries")

    # 索引（在__table_args__中定义）
    __table_args__ = (
        # 复合索引：优化按游客ID和日期查询的性能
        Index("idx_guest_identifier_date", "identifier", "query_date"),
        # 唯一索引：确保同一游客同一天查询同一单词只记录一次
        Index("uk_guest_word_date", "identifier", "word_id", "query_date", unique=True),
    )

    def __repr__(self):
        """字符串表示"""
        return (
            f"<GuestQueryLog("
            f"id={self.id}, "
            f"identifier={self.identifier}, "
            f"word_id={self.word_id}, "
            f"date={self.query_date}"
            f")>"
        )
