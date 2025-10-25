"""Prompts package for AI generation

提供配置化驱动的多语言Prompt管理系统，支持多种AI提供商。
"""

from app.prompts.manager import PromptManager, get_prompt_manager
from app.prompts.enums import Language, AIProvider, PromptType
from app.prompts.legacy import (
    get_word_generation_prompt,
    get_prompt_with_metadata,
    WORD_GENERATION_PROMPT  # 向后兼容
)

__all__ = [
    # 新接口
    "PromptManager",
    "get_prompt_manager",
    "Language",
    "AIProvider",
    "PromptType",

    # 向后兼容接口
    "get_word_generation_prompt",
    "get_prompt_with_metadata",
    "WORD_GENERATION_PROMPT",
]

# 版本信息
__version__ = "1.0.0"
