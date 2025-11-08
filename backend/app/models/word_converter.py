"""
单词数据转换器

提供新旧格式数据转换功能，支持渐进式迁移和向后兼容
"""
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.word import Word
from app.core.config import settings


class WordDataConverter:
    """单词数据转换器，处理新旧格式转换"""

    # 支持的语言代码 - 使用2字符ISO 639-1标准语言代码
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'zh': '简体中文',
        'zh_TW': '繁體中文',  # 保留用于兼容性，但实际使用zh
        'ja': '日本語',
        'ko': '한국어',
        'fr': 'Français',
        'de': 'Deutsch',
        'es': 'Español',
        'it': 'Italiano',
        'ru': 'Русский'
    }

    @classmethod
    def normalize_language_code(cls, language_code: str) -> str:
        """
        标准化语言代码为2字符格式

        Args:
            language_code: 原始语言代码

        Returns:
            标准化后的2字符语言代码
        """
        if not language_code:
            return 'en'  # 默认语言

        language_code = language_code.strip()

        # 如果已经是2字符代码，直接返回
        if len(language_code) == 2 and language_code.islower():
            return language_code

        # 特殊处理：zh_TW 作为繁体中文代码，保持不变
        if language_code == 'zh_TW':
            return 'zh_TW'

        # 映射常见的5字符代码到标准格式
        language_mapping = {
            'zh_cn': 'zh',
            'zh-cn': 'zh_TW',  # 处理 zh-cn (繁体中文)
            'en_us': 'en',
            'en-gb': 'en',
        }

        # 处理不同格式
        normalized = language_mapping.get(language_code.lower())
        if normalized:
            return normalized

        # 处理特殊情况
        if language_code.startswith('zh'):
            return 'zh'
        return 'en'

    @classmethod
    def legacy_to_new_format(cls, word: Word) -> Dict[str, Any]:
        """
        将旧格式的Word对象转换为新格式的字典

        Args:
            word: 旧格式的Word对象

        Returns:
            新格式的数据字典
        """
        return {
            'id': word.id,
            'word': word.word,
            'phonetic': word.phonetic or '',
            'translation': getattr(word, 'translation', cls._generate_translation_hint(word)),
            'part_of_speech': word.part_of_speech or '',
            'language_code': cls.normalize_language_code(getattr(word, 'language_code', 'en')),
            'core_game': {
                'content': word.core_game
            },
            'game_boards': {
                'board_a_speculative': {
                    'type': '棋盘A (思辨场)',
                    'name': '思辨场景',
                    'example': word.scenario_formal
                },
                'board_b_life': {
                    'type': '棋盘B (生活场)',
                    'name': '生活场景',
                    'example': word.scenario_casual
                }
            },
            'etymology': {
                'breakdown': {
                    'prefix': {'part': '', 'meaning': ''},
                    'root': {'part': word.etymology_breakdown, 'meaning': '词根拆解'},
                    'suffix': {'part': '', 'meaning': ''}
                },
                'story': word.etymology_story or ''
            },
            'common_mistakes': {
                'warning': word.common_mistakes,
                'avoidance': word.memory_trick
            },
            'memory_trick': word.memory_trick,
            'is_golden': word.is_golden,
            'source': word.source,
            'prompt_version': getattr(word, 'prompt_version', 'v1.0'),
            'created_at': word.created_at.isoformat() if word.created_at else None,
            'updated_at': word.updated_at.isoformat() if word.updated_at else None,
            'is_legacy_format': True,
            # 兼容性字段
            'common_mistakes_str': word.common_mistakes
        }

    @classmethod
    def new_to_legacy_format(cls, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将新格式转换为旧格式

        Args:
            new_data: 新格式的数据字典

        Returns:
            旧格式的数据字典
        """
        # 提取结构化数据到扁平字段
        core_game_data = new_data.get('core_game', {})
        game_boards_data = new_data.get('game_boards', {})
        etymology_data = new_data.get('etymology', {})
        common_mistakes_data = new_data.get('common_mistakes', {})

        return {
            'word': new_data.get('word'),
            'phonetic': new_data.get('phonetic'),
            'part_of_speech': new_data.get('part_of_speech'),
            'core_game': core_game_data.get('content', ''),
            'scenario_formal': game_boards_data.get('board_a_speculative', {}).get('example', ''),
            'scenario_casual': game_boards_data.get('board_b_life', {}).get('example', ''),
            'etymology_breakdown': etymology_data.get('breakdown', {}).get('root', {}).get('part', ''),
            'etymology_story': etymology_data.get('story', ''),
            'common_mistakes': common_mistakes_data.get('warning', ''),
            'memory_trick': new_data.get('memory_trick', ''),
            'is_golden': new_data.get('is_golden', False),
            'source': new_data.get('source', 'ai'),
            # 新增字段
            'translation': new_data.get('translation'),
            'language_code': new_data.get('language_code', 'en'),
            'prompt_version': new_data.get('prompt_version', 'v1.0'),
            'is_legacy_format': False,
            'core_game_new': core_game_data,
            'game_boards': game_boards_data,
            'etymology_new': etymology_data,
            'common_mistakes_new': common_mistakes_data
        }

    @classmethod
    def convert_ai_response_to_word(cls, ai_response: Dict[str, Any],
                                  language_code: str = 'en',
                                  source: str = 'ai') -> Dict[str, Any]:
        """
        将AI响应转换为Word模型数据

        Args:
            ai_response: AI服务返回的结构化响应
            language_code: 语言代码
            source: 数据来源

        Returns:
            Word模型数据字典
        """
        # 确保必要字段存在
        if not ai_response.get('word'):
            raise ValueError("AI response missing required field: word")

        # 安全提取嵌套字段，避免KeyError
        def safe_get_nested(data: Dict[str, Any], keys: list, default: Any = None) -> Any:
            """安全获取嵌套字典值"""
            result = data
            for key in keys:
                if isinstance(result, dict) and key in result:
                    result = result[key]
                else:
                    return default
            return result

        # 提取各部分数据，确保安全性
        core_game_data = ai_response.get('core_game', {})
        game_boards_data = ai_response.get('game_boards', {})
        etymology_data = ai_response.get('etymology', {})
        common_mistakes_data = ai_response.get('common_mistakes', {})

        return {
            # 基本字段
            'word': ai_response['word'],
            'phonetic': ai_response.get('phonetic', ''),
            'part_of_speech': ai_response.get('part_of_speech', ''),
            'translation': ai_response.get('translation', ''),
            'language_code': language_code,

            # 传统字段（向后兼容）
            'core_game': safe_get_nested(core_game_data, ['content'], ''),
            'scenario_formal': safe_get_nested(game_boards_data, ['board_a_speculative', 'example'], ''),
            'scenario_casual': safe_get_nested(game_boards_data, ['board_b_life', 'example'], ''),
            'etymology_breakdown': safe_get_nested(etymology_data, ['breakdown', 'root', 'part'], ''),
            'etymology_story': safe_get_nested(etymology_data, ['story'], ''),
            'common_mistakes': safe_get_nested(common_mistakes_data, ['warning'], ''),
            'memory_trick': ai_response.get('memory_trick', ''),

            # 元数据
            'is_golden': False,
            'source': source,
            'prompt_version': settings.prompt_version,
            'is_legacy_format': False,

            # JSONB字段 - 确保字段不为空字典，避免插入问题
            'core_game_new': core_game_data if core_game_data else None,
            'game_boards': game_boards_data if game_boards_data else None,
            'etymology_new': etymology_data if etymology_data else None,
            'common_mistakes_new': common_mistakes_data if common_mistakes_data else None,
        }

    @classmethod
    def migrate_legacy_word(cls, db: Session, word_id: int) -> Optional[Word]:
        """
        迁移单个旧格式单词到新格式

        Args:
            db: 数据库会话
            word_id: 要迁移的单词ID

        Returns:
            更新后的Word对象或None
        """
        stmt = select(Word).where(Word.id == word_id)
        word = db.execute(stmt).scalar_one_or_none()

        if not word:
            return None

        if not getattr(word, 'is_legacy_format', True):
            return word  # 已经是新格式

        # 转换数据
        new_data = cls.legacy_to_new_format(word)

        # 更新字段
        word.translation = new_data.get('translation')
        word.language_code = new_data.get('language_code', 'en')
        word.prompt_version = new_data.get('prompt_version', 'v1.0')
        word.is_legacy_format = False

        # 设置JSONB字段
        word.core_game_new = new_data.get('core_game')
        word.game_boards = new_data.get('game_boards')
        word.etymology_new = new_data.get('etymology')
        word.common_mistakes_new = new_data.get('common_mistakes')

        word.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(word)

        return word

    @classmethod
    def batch_migrate_legacy_words(cls, db: Session, batch_size: int = 100) -> int:
        """
        批量迁移旧格式单词

        Args:
            db: 数据库会话
            batch_size: 批次大小

        Returns:
            迁移的单词数量
        """
        stmt = select(Word).where(Word.is_legacy_format == True).limit(batch_size)
        words = db.execute(stmt).scalars().all()

        migrated_count = 0
        for word in words:
            try:
                cls.migrate_legacy_word(db, word.id)
                migrated_count += 1
            except Exception as e:
                db.rollback()
                print(f"Failed to migrate word {word.word}: {e}")

        return migrated_count

    @classmethod
    def validate_language_code(cls, language_code: str) -> bool:
        """
        验证语言代码是否有效

        Args:
            language_code: 语言代码

        Returns:
            是否有效
        """
        return language_code in cls.SUPPORTED_LANGUAGES

    @classmethod
    def get_supported_languages(cls) -> Dict[str, str]:
        """
        获取支持的语言列表

        Returns:
            语言代码到语言名称的映射
        """
        return cls.SUPPORTED_LANGUAGES.copy()

    @classmethod
    def _generate_translation_hint(cls, word: Word) -> str:
        """
        为旧数据生成翻译提示

        Args:
            word: Word对象

        Returns:
            翻译提示
        """
        # 基于现有字段推断可能的翻译
        if word.word.lower() in ['accommodation', 'embarrassment', 'procrastination']:
            return '需要翻译'

        # 根据内容中是否包含中文判断
        content = f"{word.core_game} {word.scenario_formal} {word.scenario_casual}"
        if any('\u4e00' <= char <= '\u9fff' for char in content):
            return '中文翻译'

        return '需要翻译'

    @classmethod
    def get_word_display_format(cls, word: Word, preferred_format: str = 'auto') -> Dict[str, Any]:
        """
        获取单词的显示格式数据

        Args:
            word: Word对象
            preferred_format: 首选格式 ('auto', 'legacy', 'new')

        Returns:
            显示用的数据字典
        """
        is_legacy = getattr(word, 'is_legacy_format', True)

        if preferred_format == 'legacy' or (preferred_format == 'auto' and is_legacy):
            return cls.legacy_to_new_format(word)
        else:
            # 新格式，直接返回结构化数据
            display_dict = {
                'id': word.id,
                'word': word.word,
                'phonetic': word.phonetic or '',
                'translation': getattr(word, 'translation', ''),
                'part_of_speech': word.part_of_speech or '',
                'language_code': cls.normalize_language_code(getattr(word, 'language_code', 'en')),
                'core_game': getattr(word, 'core_game_new', {}),
                'game_boards': getattr(word, 'game_boards', {}),
                'etymology': getattr(word, 'etymology_new', {}),
                'common_mistakes': getattr(word, 'common_mistakes_new', {}),
                'memory_trick': word.memory_trick,
                'is_golden': word.is_golden,
                'source': word.source,
                'prompt_version': getattr(word, 'prompt_version', 'v1.0'),
                'created_at': word.created_at.isoformat() if word.created_at else None,
                'updated_at': word.updated_at.isoformat() if word.updated_at else None,
                'is_legacy_format': is_legacy,
                # 兼容性字段 - 增强处理，确保字段始终存在
                'core_game_content': getattr(word, 'core_game', '') or '',
                'scenario_formal': getattr(word, 'scenario_formal', '') or '',
                'scenario_casual': getattr(word, 'scenario_casual', '') or '',
                'etymology_breakdown': getattr(word, 'etymology_breakdown', '') or '',
                'etymology_story': getattr(word, 'etymology_story', '') or '',
            }

            # 处理 common_mistakes 字段的向后兼容性
            # 优先使用新格式的结构化数据，如果没有则使用旧格式的字符串
            common_mistakes_new = getattr(word, 'common_mistakes_new', {})
            if common_mistakes_new:
                display_dict['common_mistakes'] = common_mistakes_new
                # 添加向后兼容的字符串字段
                display_dict['common_mistakes_str'] = common_mistakes_new.get('warning', getattr(word, 'common_mistakes', '') or '')
            else:
                # 如果新格式数据不存在，使用旧格式字符串并构造一个默认结构
                legacy_mistakes = getattr(word, 'common_mistakes', '') or ''
                display_dict['common_mistakes'] = {'warning': legacy_mistakes, 'avoidance': ''}
                display_dict['common_mistakes_str'] = legacy_mistakes

            return display_dict