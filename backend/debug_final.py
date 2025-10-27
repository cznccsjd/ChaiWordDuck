#!/usr/bin/env python3
"""
最终调试get_language_from_accept_language
"""
from app.services.guest_preferences import get_language_from_accept_language
from app.validators.user_preferences import get_default_language

def debug_get_language_from_accept_language():
    """调试get_language_from_accept_language函数"""
    print("=== 调试get_language_from_accept_language ===")

    accept_language = "en-US,en;q=0.9"
    print(f"输入: {accept_language}")
    print(f"默认语言: {get_default_language()}")

    # 调用函数
    result = get_language_from_accept_language(accept_language)
    print(f"结果: '{result}'")

    # 手动检查函数的步骤
    print("\n=== 手动检查步骤 ===")
    if not accept_language:
        print("1. Accept-Language为空")
        result = get_default_language()
    else:
        print("1. Accept-Language不为空")
        languages = accept_language.split(',')
        print(f"2. 分割后: {languages}")

        parsed_languages = []
        for lang in languages:
            lang = lang.strip()
            print(f"3. 处理语言: '{lang}'")

            if ';' in lang:
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
                lang_code = lang
                q = 1.0

            print(f"   语言代码: '{lang_code}', 质量值: {q}")

            # 标准化语言代码
            from app.services.guest_preferences import normalize_accept_language_code
            normalized = normalize_accept_language_code(lang_code.strip())
            print(f"   标准化后: '{normalized}'")

            if normalized:
                parsed_languages.append((normalized, q))
                print(f"   添加到列表")
            else:
                print(f"   跳过（不支持）")

        print(f"4. 解析结果: {parsed_languages}")

        # 按质量值排序
        parsed_languages.sort(key=lambda x: x[1], reverse=True)
        print(f"5. 排序后: {parsed_languages}")

        # 返回第一个支持的语言
        if parsed_languages:
            result = parsed_languages[0][0]
            print(f"6. 返回第一个: '{result}'")
        else:
            result = get_default_language()
            print(f"6. 没有支持的语言，返回默认: '{result}'")

    print(f"\n最终结果: '{result}'")
    return result

if __name__ == "__main__":
    debug_get_language_from_accept_language()