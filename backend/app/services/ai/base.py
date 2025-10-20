"""AI服务抽象基类和数据模型"""
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


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
