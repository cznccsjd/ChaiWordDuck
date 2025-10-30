"""
用户偏好相关的验证器

提供语言偏好验证功能
"""
from typing import Optional

# 支持的语言列表 - 使用2字符ISO 639-1标准语言代码
SUPPORTED_LANGUAGES = ["zh", "en"]
DEFAULT_LANGUAGE = "zh"


def is_supported_language(language: str) -> bool:
    """
    检查是否为支持的语言代码

    Args:
        language: 语言代码

    Returns:
        bool: 是否支持
    """
    return language in SUPPORTED_LANGUAGES


def validate_preferred_language(language: str) -> str:
    """
    验证用户语言偏好

    Args:
        language: 语言代码

    Returns:
        str: 验证后的语言代码

    Raises:
        ValueError: 不支持的语言代码
    """
    if not language or not language.strip():
        raise ValueError("语言代码不能为空")

    language = language.strip()
    if not is_supported_language(language):
        raise ValueError("不支持的语言代码，仅支持: zh, en")

    return language


def get_default_language() -> str:
    """
    获取默认语言代码

    Returns:
        str: 默认语言代码
    """
    return DEFAULT_LANGUAGE


def normalize_language_code(language: Optional[str]) -> str:
    """
    标准化语言代码

    Args:
        language: 原始语言代码

    Returns:
        str: 标准化后的语言代码
    """
    if not language:
        return DEFAULT_LANGUAGE

    language = language.strip()
    if is_supported_language(language):
        return language

    # 尝试映射常见的语言代码到2字符格式
    language_mapping = {
        "zh_cn": "zh",
        "zh-cn": "zh",
        "zh": "zh",
        "en_us": "en",
        "en-us": "en",
        "en": "en",
    }

    # 先尝试直接匹配
    if is_supported_language(language):
        return language

    # 然后尝试映射
    normalized = language_mapping.get(language.lower(), DEFAULT_LANGUAGE)
    return normalized if is_supported_language(normalized) else DEFAULT_LANGUAGE