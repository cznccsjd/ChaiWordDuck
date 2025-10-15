"""
单词相关的Pydantic模型

定义单词查询、响应相关的数据模型
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


# ============= Request Models =============


class WordQueryRequest(BaseModel):
    """单词查询请求"""

    word: str = Field(..., description="要查询的单词", min_length=1, max_length=100)

    @field_validator("word")
    @classmethod
    def validate_word(cls, v: str) -> str:
        """验证单词格式"""
        # 去除首尾空格
        word = v.strip()

        # 检查是否为空
        if not word:
            raise ValueError("单词不能为空")

        # 检查是否只包含字母、连字符和空格
        if not all(c.isalpha() or c in ['-', ' '] for c in word):
            raise ValueError("单词只能包含字母、连字符和空格")

        return word.lower()


# ============= Response Models =============


class WordDetail(BaseModel):
    """单词详细信息"""

    id: int = Field(..., description="单词ID")
    word: str = Field(..., description="单词")
    phonetic: Optional[str] = Field(None, description="音标")
    part_of_speech: Optional[str] = Field(None, description="词性", alias="partOfSpeech")

    # 核心内容
    core_game: str = Field(..., description="核心游戏", alias="coreGame")
    scenario_formal: str = Field(..., description="思辨场景", alias="scenarioFormal")
    scenario_casual: str = Field(..., description="生活场景", alias="scenarioCasual")
    etymology_breakdown: str = Field(..., description="词根拆解", alias="etymologyBreakdown")
    etymology_story: Optional[str] = Field(None, description="词源故事", alias="etymologyStory")
    common_mistakes: str = Field(..., description="犯规警告", alias="commonMistakes")
    memory_trick: str = Field(..., description="通关秘籍", alias="memoryTrick")

    # 元数据
    is_golden: bool = Field(..., description="是否黄金手册", alias="isGolden")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间", alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class WordQueryResponse(BaseModel):
    """单词查询响应"""

    id: int = Field(..., description="单词ID")
    word: str = Field(..., description="单词")
    phonetic: Optional[str] = Field(None, description="音标")
    part_of_speech: Optional[str] = Field(None, description="词性", alias="partOfSpeech")

    # 核心内容
    core_game: str = Field(..., description="核心游戏", alias="coreGame")
    scenario_formal: str = Field(..., description="思辨场景", alias="scenarioFormal")
    scenario_casual: str = Field(..., description="生活场景", alias="scenarioCasual")
    etymology_breakdown: str = Field(..., description="词根拆解", alias="etymologyBreakdown")
    etymology_story: Optional[str] = Field(None, description="词源故事", alias="etymologyStory")
    common_mistakes: str = Field(..., description="犯规警告", alias="commonMistakes")
    memory_trick: str = Field(..., description="通关秘籍", alias="memoryTrick")

    # 元数据
    is_golden: bool = Field(..., description="是否黄金手册", alias="isGolden")

    # 查询限制信息
    remaining_queries: int = Field(..., description="今日剩余查询次数", alias="remainingQueries")

    class Config:
        from_attributes = True
        populate_by_name = True


class QueryLimitInfo(BaseModel):
    """查询限制信息"""

    total_queries: int = Field(..., description="总查询次数限制", alias="totalQueries")
    remaining_queries: int = Field(..., description="剩余查询次数", alias="remainingQueries")
    used_queries: int = Field(..., description="已使用查询次数", alias="usedQueries")
    queried_words: List[int] = Field(..., description="已查询单词ID列表", alias="queriedWords")

    class Config:
        populate_by_name = True


class WordByIdResponse(BaseModel):
    """根据ID获取单词响应"""

    id: int = Field(..., description="单词ID")
    word: str = Field(..., description="单词")
    phonetic: Optional[str] = Field(None, description="音标")
    part_of_speech: Optional[str] = Field(None, description="词性", alias="partOfSpeech")

    # 核心内容
    core_game: str = Field(..., description="核心游戏", alias="coreGame")
    scenario_formal: str = Field(..., description="思辨场景", alias="scenarioFormal")
    scenario_casual: str = Field(..., description="生活场景", alias="scenarioCasual")
    etymology_breakdown: str = Field(..., description="词根拆解", alias="etymologyBreakdown")
    etymology_story: Optional[str] = Field(None, description="词源故事", alias="etymologyStory")
    common_mistakes: str = Field(..., description="犯规警告", alias="commonMistakes")
    memory_trick: str = Field(..., description="通关秘籍", alias="memoryTrick")

    # 元数据
    is_golden: bool = Field(..., description="是否黄金手册", alias="isGolden")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间", alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True
