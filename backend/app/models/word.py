"""
单词模型

定义单词相关的数据库模型，支持多语言Prompt系统和向后兼容
"""
from datetime import datetime
from typing import Optional, Dict, Any

import os
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# 统一使用SQLite兼容的JSON类型，避免环境切换问题
# 在生产环境中，PostgreSQL也支持JSON类型（虽然JSONB更高效，但JSON是兼容的）
from sqlalchemy import JSON

JSONField = JSON


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

    # 多语言支持字段
    translation: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, server_default='zh', index=True
    )
    prompt_version: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, server_default='v1.0'
    )
    is_legacy_format: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true", index=True
    )

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

    # 结构化数据字段（JSONB/JSON）
    # 添加default=None确保在非测试环境下正确的默认值处理
    core_game_new: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONField, nullable=True, default=None
    )
    game_boards: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONField, nullable=True, default=None
    )
    etymology_new: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONField, nullable=True, default=None
    )
    common_mistakes_new: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONField, nullable=True, default=None
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

    # 表约束
    table_constraints = [
        CheckConstraint("source IN ('ai', 'manual')", name="check_word_source"),
        CheckConstraint(
            "language_code IN ('en', 'zh', 'zh_TW', 'ja', 'ko', 'fr', 'de', 'es', 'it', 'ru')",
            name="check_words_language_code"
        ),
        Index("idx_words_word", "word", unique=True),
        Index("idx_words_is_golden", "is_golden"),
        Index("idx_words_language_code", "language_code"),
        Index("idx_words_prompt_version", "prompt_version"),
        Index("idx_words_is_legacy_format", "is_legacy_format"),
    ]

    # JSON/GIN indexes for efficient querying (PostgreSQL only)
    if not os.getenv("PYTEST_CURRENT_TEST"):
        table_constraints.extend([
            Index("idx_words_core_game_new_gin", "core_game_new", postgresql_using="gin"),
            Index("idx_words_game_boards_gin", "game_boards", postgresql_using="gin"),
            Index("idx_words_etymology_new_gin", "etymology_new", postgresql_using="gin"),
            Index("idx_words_common_mistakes_new_gin", "common_mistakes_new", postgresql_using="gin"),
        ])

    __table_args__ = tuple(table_constraints)

    def __repr__(self) -> str:
        return f"<Word(id={self.id}, word={self.word}, is_golden={self.is_golden})>"

    # 向后兼容方法
    def get_display_data(self, preferred_format: str = 'auto') -> Dict[str, Any]:
        """
        获取单词的显示格式数据，自动处理新旧格式

        Args:
            preferred_format: 首选格式 ('auto', 'legacy', 'new')

        Returns:
            标准化的显示数据字典
        """
        from app.models.word_converter import WordDataConverter

        return WordDataConverter.get_word_display_format(self, preferred_format)

    def is_new_format(self) -> bool:
        """检查是否为新格式数据"""
        return not getattr(self, 'is_legacy_format', True)

    def get_core_game_content(self) -> str:
        """获取核心游戏内容（兼容新旧格式）"""
        if self.is_new_format() and self.core_game_new:
            return self.core_game_new.get('content', '')
        return self.core_game

    def get_game_boards_data(self) -> Dict[str, Any]:
        """获取游戏棋盘数据（兼容新旧格式）"""
        if self.is_new_format() and self.game_boards:
            return self.game_boards

        # 返回旧格式的默认结构
        return {
            'board_a_speculative': {
                'type': '棋盘A (思辨场)',
                'name': '思辨场景',
                'example': self.scenario_formal
            },
            'board_b_life': {
                'type': '棋盘B (生活场)',
                'name': '生活场景',
                'example': self.scenario_casual
            }
        }

    def get_etymology_data(self) -> Dict[str, Any]:
        """获取词源数据（兼容新旧格式）"""
        if self.is_new_format() and self.etymology_new:
            return self.etymology_new

        # 返回旧格式的默认结构
        return {
            'breakdown': {
                'prefix': {'part': '', 'meaning': ''},
                'root': {'part': self.etymology_breakdown, 'meaning': '词根拆解'},
                'suffix': {'part': '', 'meaning': ''}
            },
            'story': self.etymology_story or ''
        }

    def get_common_mistakes_data(self) -> Dict[str, Any]:
        """获取常见错误数据（兼容新旧格式）"""
        if self.is_new_format() and self.common_mistakes_new:
            return self.common_mistakes_new

        # 返回旧格式的默认结构
        return {
            'warning': self.common_mistakes,
            'avoidance': self.memory_trick
        }

    def get_translation_or_hint(self) -> str:
        """获取翻译或翻译提示"""
        return getattr(self, 'translation', '') or '需要翻译'

    def get_language_display_name(self) -> str:
        """获取语言显示名称"""
        from app.models.word_converter import WordDataConverter

        language_code = getattr(self, 'language_code', 'en')
        return WordDataConverter.SUPPORTED_LANGUAGES.get(language_code, language_code)

    def is_multilingual(self) -> bool:
        """检查是否为多语言数据"""
        language_code = getattr(self, 'language_code', 'en')
        translation = getattr(self, 'translation', '')
        return language_code != 'en' or bool(translation)

    def to_api_dict(self, include_legacy_fields: bool = True) -> Dict[str, Any]:
        """
        转换为API响应字典

        Args:
            include_legacy_fields: 是否包含向后兼容的字段

        Returns:
            API响应格式的数据字典
        """
        display_data = self.get_display_data()

        if not include_legacy_fields:
            # 只返回新格式字段
            return {
                'id': display_data['id'],
                'word': display_data['word'],
                'phonetic': display_data['phonetic'],
                'translation': display_data['translation'],
                'part_of_speech': display_data['part_of_speech'],
                'language_code': display_data['language_code'],
                'core_game': display_data['core_game'],
                'game_boards': display_data['game_boards'],
                'etymology': display_data['etymology'],
                'common_mistakes': display_data['common_mistakes'],
                'memory_trick': display_data['memory_trick'],
                'is_golden': display_data['is_golden'],
                'source': display_data['source'],
                'prompt_version': display_data['prompt_version'],
                'created_at': display_data['created_at'],
                'updated_at': display_data['updated_at']
            }

        # 返回完整数据（包含向后兼容字段）
        return display_data
