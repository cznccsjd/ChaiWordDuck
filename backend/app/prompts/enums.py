"""枚举类定义 - 支持多语言和多AI提供商"""

from enum import Enum


class Language(str, Enum):
    """支持的语言枚举"""

    CHINESE = "zh_CN"
    ENGLISH = "en_US"

    @classmethod
    def get_display_name(cls, language: str) -> str:
        """获取语言的显示名称"""
        display_names = {
            cls.CHINESE: "简体中文",
            cls.ENGLISH: "English"
        }
        return display_names.get(language, language)

    @classmethod
    def is_supported(cls, language: str) -> bool:
        """检查是否支持该语言"""
        return language in [cls.CHINESE, cls.ENGLISH]


class AIProvider(str, Enum):
    """AI提供商枚举"""

    GEMINI = "gemini"
    OPENAI = "openai"

    @classmethod
    def get_display_name(cls, provider: str) -> str:
        """获取提供商的显示名称"""
        display_names = {
            cls.GEMINI: "Google Gemini",
            cls.OPENAI: "OpenAI"
        }
        return display_names.get(provider, provider)

    @classmethod
    def is_supported(cls, provider: str) -> bool:
        """检查是否支持该提供商"""
        return provider in [cls.GEMINI, cls.OPENAI]


class PromptType(str, Enum):
    """Prompt类型枚举"""

    WORD_GENERATION = "word_generation"
    WORD_EXPLANATION = "word_explanation"
    WORD_PRACTICE = "word_practice"

    @classmethod
    def get_display_name(cls, prompt_type: str) -> str:
        """获取Prompt类型的显示名称"""
        display_names = {
            cls.WORD_GENERATION: "单词生成",
            cls.WORD_EXPLANATION: "单词解释",
            cls.WORD_PRACTICE: "单词练习"
        }
        return display_names.get(prompt_type, prompt_type)