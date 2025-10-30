"""
游客偏好设置服务

提供游客语言偏好的处理逻辑
"""
from typing import Dict, Optional

from app.validators.user_preferences import get_default_language, normalize_language_code


def get_language_from_accept_language(accept_language: Optional[str]) -> str:
    """
    从Accept-Language头部获取语言偏好

    Args:
        accept_language: Accept-Language头部值

    Returns:
        str: 语言代码
    """
    if not accept_language:
        return get_default_language()

    # 解析Accept-Language头部
    # 格式示例: "zh-CN,zh;q=0.9,en;q=0.8"
    languages = accept_language.split(',')

    # 提取语言代码并按质量值排序
    parsed_languages = []
    for lang in languages:
        lang = lang.strip()
        if ';' in lang:
            # 有质量值的情况: "zh-CN;q=0.9"
            lang_code, q_value = lang.split(';')
            q_value = q_value.strip()
            if q_value.startswith('q='):
                try:
                    q = float(q_value[2:])
                except ValueError:
                    q = 1.0
            else:
                q = 1.0
        else:
            # 没有质量值的情况: "zh-CN"
            lang_code = lang
            q = 1.0

        # 标准化语言代码
        normalized = normalize_accept_language_code(lang_code.strip())
        if normalized:
            parsed_languages.append((normalized, q))

    # 按质量值降序排序
    parsed_languages.sort(key=lambda x: x[1], reverse=True)

    # 返回第一个支持的语言
    for lang_code, _ in parsed_languages:
        return lang_code

    return get_default_language()


def normalize_accept_language_code(lang_code: str) -> Optional[str]:
    """
    标准化Accept-Language中的语言代码

    Args:
        lang_code: 原始语言代码

    Returns:
        Optional[str]: 标准化后的语言代码，如果不支持则返回None
    """
    if not lang_code:
        return None

    lang_code = lang_code.strip()
    if not lang_code:
        return None

    lang_code = lang_code.lower()

    # 映射常见的Accept-Language代码到我们支持的2字符语言
    language_mapping = {
        "zh-cn": "zh",
        "zh": "zh",
        "en-us": "en",
        "en": "en",
    }

    # 处理特殊情况 - 映射到2字符代码
    if lang_code.startswith("zh"):
        return "zh"
    elif lang_code.startswith("en"):
        return "en"

    # 尝试直接映射
    return language_mapping.get(lang_code)


def get_language_from_cookie(cookies: Dict[str, str]) -> str:
    """
    从Cookie获取语言偏好

    Args:
        cookies: Cookie字典

    Returns:
        str: 语言代码
    """
    if not cookies:
        return get_default_language()

    language = cookies.get("language")
    if not language:
        return get_default_language()

    return normalize_language_code(language)


def get_guest_language_preference(
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None
) -> str:
    """
    获取游客语言偏好

    优先级：
    1. Cookie中的语言设置
    2. Accept-Language头部
    3. 默认语言

    Args:
        headers: HTTP请求头
        cookies: Cookie字典

    Returns:
        str: 游客语言偏好
    """
    # 1. 优先使用Cookie中的语言设置
    if cookies:
        cookie_language = get_language_from_cookie(cookies)
        if cookie_language:
            return cookie_language

    # 2. 使用Accept-Language头部
    if headers:
        # HTTP头部通常会被小写化，但我们也要处理大写的情况
        accept_language = headers.get("accept-language") or headers.get("Accept-Language")
        if accept_language:
            header_language = get_language_from_accept_language(accept_language)
            if header_language:
                return header_language

    # 3. 使用默认语言
    return get_default_language()


def get_effective_language_for_guest(
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, str]] = None,
    explicit_language: Optional[str] = None
) -> str:
    """
    获取游客的有效语言代码

    优先级：
    1. 显式指定的语言参数
    2. Cookie中的语言设置
    3. Accept-Language头部
    4. 默认语言

    Args:
        headers: HTTP请求头
        cookies: Cookie字典
        explicit_language: 显式指定的语言参数

    Returns:
        str: 有效的语言代码
    """
    # 1. 优先使用显式指定的语言
    if explicit_language:
        return normalize_language_code(explicit_language)

    # 2. 使用Cookie中的语言设置
    if cookies:
        cookie_language = get_language_from_cookie(cookies)
        if cookie_language:
            return cookie_language

    # 3. 使用Accept-Language头部
    if headers:
        accept_language = headers.get("accept-language") or headers.get("Accept-Language")
        if accept_language:
            header_language = get_language_from_accept_language(accept_language)
            if header_language:
                return header_language

    # 4. 使用默认语言
    return get_default_language()