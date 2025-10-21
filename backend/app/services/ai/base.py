"""AI服务抽象基类和数据模型"""
from abc import ABC, abstractmethod
from typing import Optional
import re
from pydantic import BaseModel, field_validator


class WordManualData(BaseModel):
    """单词手册数据模型"""
    word: str
    phonetic: Optional[str] = ""
    part_of_speech: Optional[str] = ""
    core_game: str
    scenario_formal: str
    scenario_casual: str
    etymology_breakdown: str
    etymology_story: Optional[str] = ""
    memory_trick: str
    common_mistakes: Optional[str] = ""

    @field_validator('word', 'phonetic', 'part_of_speech', 'core_game',
                   'scenario_formal', 'scenario_casual', 'etymology_breakdown',
                   'etymology_story', 'memory_trick', 'common_mistakes', mode='before')
    @classmethod
    def clean_unicode_fields(cls, v):
        """清理所有文本字段中的无效Unicode字符"""
        if isinstance(v, str):
            # 移除无效的代理对字符 (U+DC80-U+DFFF)
            return re.sub(r'[\udc80-\udfff]', '', v)
        return v


class AIServiceBase(ABC):
    """AI服务抽象基类"""

    @abstractmethod
    def generate_word_manual(self, word: str) -> WordManualData:
        """生成单词学习手册"""
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
