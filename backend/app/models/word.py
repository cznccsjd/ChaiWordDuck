"""
单词模型

定义单词相关的数据库模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Word(Base):
    """
    单词表

    存储单词的详细信息和拆解数据
    """

    __tablename__ = "words"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 基本信息
    word: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    phonetic: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    part_of_speech: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 核心内容（拆词鸭特色）
    core_game: Mapped[str] = mapped_column(Text, nullable=False)  # 核心游戏
    scenario_formal: Mapped[str] = mapped_column(Text, nullable=False)  # 思辨场景
    scenario_casual: Mapped[str] = mapped_column(Text, nullable=False)  # 生活场景
    etymology_breakdown: Mapped[str] = mapped_column(Text, nullable=False)  # 词根拆解
    etymology_story: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 词源故事
    common_mistakes: Mapped[str] = mapped_column(Text, nullable=False)  # 犯规警告
    memory_trick: Mapped[str] = mapped_column(Text, nullable=False)  # 通关秘籍

    # 元数据
    is_golden: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )  # 是否黄金手册
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ai", server_default="ai"
    )  # 来源: ai or manual

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
        CheckConstraint("source IN ('ai', 'manual')", name="check_word_source"),
        Index("idx_words_word", "word", unique=True),
        Index("idx_words_is_golden", "is_golden"),
    )

    def __repr__(self) -> str:
        return f"<Word(id={self.id}, word={self.word}, is_golden={self.is_golden})>"
