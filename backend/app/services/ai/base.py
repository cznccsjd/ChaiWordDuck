"""AI服务抽象基类和数据模型"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import re
from pydantic import BaseModel, field_validator


class GameBoard(BaseModel):
    """游戏棋盘数据模型"""
    type: str
    name: str
    example: str

    @field_validator('type', 'name', 'example', mode='before')
    @classmethod
    def clean_unicode_fields(cls, v):
        """清理所有文本字段中的无效Unicode字符"""
        if isinstance(v, str):
            # 移除无效的代理对字符 (U+DC80-U+DFFF)
            return re.sub(r'[\udc80-\udfff]', '', v)
        return v


class EtymologyBreakdown(BaseModel):
    """词源拆解数据模型"""
    prefix: Optional[Dict[str, str]] = None
    root: Optional[Dict[str, str]] = None
    suffix: Optional[Dict[str, str]] = None


class Etymology(BaseModel):
    """词源数据模型"""
    breakdown: EtymologyBreakdown
    story: str

    @field_validator('story', mode='before')
    @classmethod
    def clean_unicode_fields(cls, v):
        """清理所有文本字段中的无效Unicode字符"""
        if isinstance(v, str):
            # 移除无效的代理对字符 (U+DC80-U+DFFF)
            return re.sub(r'[\udc80-\udfff]', '', v)
        return v


class CoreGame(BaseModel):
    """核心游戏数据模型"""
    content: str

    @field_validator('content', mode='before')
    @classmethod
    def clean_unicode_fields(cls, v):
        """清理所有文本字段中的无效Unicode字符"""
        if isinstance(v, str):
            # 移除无效的代理对字符 (U+DC80-U+DFFF)
            return re.sub(r'[\udc80-\udfff]', '', v)
        return v


class CommonMistakes(BaseModel):
    """常见错误数据模型"""
    warning: str
    avoidance: str

    @field_validator('warning', 'avoidance', mode='before')
    @classmethod
    def clean_unicode_fields(cls, v):
        """清理所有文本字段中的无效Unicode字符"""
        if isinstance(v, str):
            # 移除无效的代理对字符 (U+DC80-U+DFFF)
            return re.sub(r'[\udc80-\udfff]', '', v)
        return v


class GameBoards(BaseModel):
    """游戏棋盘集合数据模型"""
    board_a_speculative: GameBoard
    board_b_life: GameBoard


class WordManualData(BaseModel):
    """单词手册数据模型 - 完整嵌套结构"""
    word: str
    phonetic: Optional[str] = ""
    translation: Optional[str] = ""
    part_of_speech: Optional[str] = ""
    core_game: CoreGame
    game_boards: GameBoards
    etymology: Etymology
    common_mistakes: CommonMistakes
    memory_trick: str
    images: Optional[Dict[str, Any]] = None  # 新增图片字段

    @field_validator('word', 'phonetic', 'translation', 'part_of_speech', 'memory_trick', mode='before')
    @classmethod
    def clean_unicode_fields(cls, v):
        """清理所有文本字段中的无效Unicode字符"""
        if isinstance(v, str):
            # 移除无效的代理对字符 (U+DC80-U+DFFF)
            return re.sub(r'[\udc80-\udfff]', '', v)
        return v

    # 向后兼容性方法
    def get_scenario_formal(self) -> str:
        """向后兼容：从board_a获取正式场景"""
        return f"{self.game_boards.board_a_speculative.name}：{self.game_boards.board_a_speculative.example}"

    def get_scenario_casual(self) -> str:
        """向后兼容：从board_b获取日常场景"""
        return f"{self.game_boards.board_b_life.name}：{self.game_boards.board_b_life.example}"

    def get_etymology_breakdown(self) -> str:
        """向后兼容：从breakdown获取词源拆解"""
        parts = []
        if self.etymology.breakdown.prefix:
            parts.append(f"前缀：{self.etymology.breakdown.prefix.get('part', '')}（{self.etymology.breakdown.prefix.get('meaning', '')}）")
        if self.etymology.breakdown.root:
            parts.append(f"词根：{self.etymology.breakdown.root.get('part', '')}（{self.etymology.breakdown.root.get('meaning', '')}）")
        if self.etymology.breakdown.suffix:
            parts.append(f"后缀：{self.etymology.breakdown.suffix.get('part', '')}（{self.etymology.breakdown.suffix.get('meaning', '')}）")
        return "；".join(parts)

    def get_etymology_story(self) -> str:
        """向后兼容：获取词源故事"""
        return self.etymology.story

    def get_core_game_content(self) -> str:
        """向后兼容：获取核心游戏内容"""
        return self.core_game.content

    def get_memory_trick(self) -> str:
        """向后兼容：获取记忆技巧"""
        return self.memory_trick

    def get_common_mistakes(self) -> str:
        """向后兼容：获取常见错误"""
        return f"{self.common_mistakes.warning}。{self.common_mistakes.avoidance}"


class AIServiceBase(ABC):
    """AI服务抽象基类"""

    @abstractmethod
    def generate_word_manual(self, word: str, language: str = "zh_CN") -> WordManualData:
        """生成单词学习手册

        Args:
            word: 目标单词
            language: 语言代码，默认为中文(zh_CN)

        Returns:
            WordManualData: 生成的单词学习手册数据
        """
        pass


# 异常类
class AIServiceError(Exception):
    """AI服务基础异常"""
    pass


class AITimeoutError(AIServiceError):
    """AI服务超时"""
    pass


class AIRateLimitError(AIServiceError):
    """API限流"""
    pass


class AIParseError(AIServiceError):
    """JSON解析错误"""
    pass
