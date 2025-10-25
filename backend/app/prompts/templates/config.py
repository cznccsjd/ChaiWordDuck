"""Prompt模板配置类 - 定义模板数据结构和验证逻辑"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class Metadata(BaseModel):
    """模板元数据"""

    version: str = Field(..., description="模板版本")
    description: str = Field(..., description="模板描述")
    last_updated: str = Field(..., description="最后更新时间")


class GameBoard(BaseModel):
    """游戏棋盘配置"""

    type: str = Field(..., description="棋盘类型")
    name: str = Field(..., description="创意场名")
    example: str = Field(..., description="示例句子")


class EtymologyBreakdown(BaseModel):
    """词源拆解配置"""

    prefix: Dict[str, str] = Field(default_factory=dict, description="前缀信息")
    root: Dict[str, str] = Field(default_factory=dict, description="词根信息")
    suffix: Dict[str, str] = Field(default_factory=dict, description="后缀信息")


class Etymology(BaseModel):
    """词源配置"""

    breakdown: EtymologyBreakdown = Field(default_factory=EtymologyBreakdown, description="拆解信息")
    story: str = Field(..., description="组装故事")


class CommonMistakes(BaseModel):
    """常见错误配置"""

    warning: str = Field(..., description="错误警告")
    avoidance: str = Field(..., description="避免技巧")


class TemplateSchema(BaseModel):
    """模板Schema定义"""

    word: str = Field(..., description="目标单词")
    phonetic: str = Field(..., description="国际音标")
    translation: str = Field(..., description="译文")
    part_of_speech: str = Field(..., description="词性")
    core_game: Dict[str, str] = Field(..., description="核心游戏")
    game_boards: Dict[str, GameBoard] = Field(..., description="游戏棋盘")
    etymology: Etymology = Field(..., description="词源信息")
    common_mistakes: CommonMistakes = Field(..., description="常见错误")
    memory_trick: str = Field(..., description="记忆技巧")


class LanguageTemplate(BaseModel):
    """单语言模板配置"""

    system_prompt: str = Field(..., description="系统提示词")
    user_prompt: str = Field(..., description="用户提示词")

    @field_validator('user_prompt')
    def validate_user_prompt(cls, v):
        """验证用户提示词包含必要的占位符"""
        if '{word}' not in v:
            raise ValueError("用户提示词必须包含 {word} 占位符")
        return v


class ProviderConfig(BaseModel):
    """AI提供商配置"""

    default_temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="默认温度参数")
    default_max_tokens: int = Field(default=2000, gt=0, le=4000, description="默认最大token数")
    supports_structured_output: bool = Field(default=True, description="是否支持结构化输出")
    model: Optional[str] = Field(None, description="推荐模型")


class PromptTemplateConfig(BaseModel):
    """完整的Prompt模板配置"""

    metadata: Metadata = Field(..., description="元数据")
    templates: Dict[str, LanguageTemplate] = Field(..., description="多语言模板")
    providers: Dict[str, ProviderConfig] = Field(..., description="AI提供商配置")

    @field_validator('templates')
    def validate_templates(cls, v):
        """验证模板配置"""
        if not v:
            raise ValueError("至少需要配置一个语言模板")
        return v

    @field_validator('providers')
    def validate_providers(cls, v):
        """验证提供商配置"""
        if not v:
            raise ValueError("至少需要配置一个AI提供商")
        return v

    def get_template(self, language: str) -> Optional[LanguageTemplate]:
        """获取指定语言的模板"""
        return self.templates.get(language)

    def get_provider_config(self, provider: str) -> Optional[ProviderConfig]:
        """获取指定提供商的配置"""
        return self.providers.get(provider)

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        return list(self.templates.keys())

    def get_supported_providers(self) -> list[str]:
        """获取支持的提供商列表"""
        return list(self.providers.keys())

    def validate_language_support(self, language: str) -> bool:
        """检查是否支持指定语言"""
        return language in self.templates

    def validate_provider_support(self, provider: str) -> bool:
        """检查是否支持指定提供商"""
        return provider in self.providers