"""
用户偏好设置服务

提供用户语言偏好的业务逻辑
"""
from typing import Optional

from app.models.user import User
from app.validators.user_preferences import get_default_language, normalize_language_code


def get_user_language_preference(user: Optional[User]) -> str:
    """
    获取用户语言偏好

    Args:
        user: 用户对象，None表示游客

    Returns:
        str: 用户语言偏好，游客返回默认值
    """
    if user and hasattr(user, 'preferred_language'):
        return user.preferred_language
    return get_default_language()


def get_default_language_for_new_user() -> str:
    """
    获取新用户的默认语言

    Returns:
        str: 默认语言代码
    """
    return get_default_language()


def should_use_user_preference(
    user: Optional[User],
    explicit_language: Optional[str] = None
) -> bool:
    """
    判断是否应该使用用户语言偏好

    Args:
        user: 用户对象
        explicit_language: 显式指定的语言参数

    Returns:
        bool: 是否使用用户偏好
    """
    # 如果有显式指定语言，优先使用显式参数
    if explicit_language:
        return False

    # 如果没有用户信息，不使用用户偏好
    if not user:
        return False

    # 如果用户有语言偏好设置，使用用户偏好
    return hasattr(user, 'preferred_language')


def get_effective_language(
    user: Optional[User],
    explicit_language: Optional[str] = None,
    fallback_language: Optional[str] = None
) -> str:
    """
    获取有效的语言代码

    优先级：
    1. 显式指定的语言参数
    2. 用户语言偏好
    3. 回退语言
    4. 默认语言

    Args:
        user: 用户对象
        explicit_language: 显式指定的语言参数
        fallback_language: 回退语言

    Returns:
        str: 有效的语言代码
    """
    # 1. 优先使用显式指定的语言
    if explicit_language:
        return normalize_language_code(explicit_language)

    # 2. 使用用户语言偏好
    if user and hasattr(user, 'preferred_language'):
        return normalize_language_code(user.preferred_language)

    # 3. 使用回退语言
    if fallback_language:
        return normalize_language_code(fallback_language)

    # 4. 使用默认语言
    return get_default_language()


def update_user_language_preference(user: User, language: str) -> User:
    """
    更新用户语言偏好

    Args:
        user: 用户对象
        language: 新的语言偏好

    Returns:
        User: 更新后的用户对象
    """
    from app.validators.user_preferences import validate_preferred_language

    # 验证语言代码
    validated_language = validate_preferred_language(language)

    # 更新用户偏好
    user.preferred_language = validated_language

    return user