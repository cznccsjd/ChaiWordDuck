#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版prompt内容分析脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.prompts.word_generation import get_word_generation_prompt

def analyze_prompt_content():
    """分析prompt内容"""
    print("=" * 60)
    print("分析Prompt内容 - 寻找可能触发安全过滤器的问题")
    print("=" * 60)

    # 测试不同词汇的prompt内容
    test_words = ["hello", "world", "contribution", "test"]

    for word in test_words:
        print(f"\n分析词汇: {word}")
        print("-" * 40)

        # 获取prompt内容
        prompt = get_word_generation_prompt(word)

        print(f"Prompt长度: {len(prompt)} 字符")
        print(f"Prompt内容预览:")
        print("-" * 20)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print("-" * 20)

        # 分析潜在问题词汇
        sensitive_keywords = [
            "kill", "death", "murder", "violence", "weapon", "gun",
            "drug", "alcohol", "sex", "nude", "porn", "adult",
            "hate", "racist", "terrorism", "bomb", "explosive"
        ]

        found_keywords = []
        for keyword in sensitive_keywords:
            if keyword.lower() in prompt.lower():
                found_keywords.append(keyword)

        if found_keywords:
            print(f"WARNING: 发现可能敏感的关键词: {found_keywords}")
        else:
            print("OK: 未发现明显的敏感关键词")

        # 特别检查中文示例
        if "啊！靠！没得神" in prompt:
            print("WARNING: 发现可能触发过滤的中文示例: '啊！靠！没得神'")
            print("   '靠'字可能被误判为不当用语")

        # 检查其他可能的敏感中文词汇
        chinese_sensitive = ["杀", "死", "暴力", "毒品", "性", "裸", "色情"]
        for chinese_word in chinese_sensitive:
            if chinese_word in prompt:
                print(f"WARNING: 发现敏感中文词汇: {chinese_word}")

def create_safe_prompt():
    """创建安全的prompt版本"""
    print(f"\n{'='*60}")
    print("创建安全的Prompt版本")
    print("=" * 60)

    safe_prompt_template = '''你是一位专业的英语教学专家，擅长使用"五步语言游戏学习法"帮助学习者记忆长单词。

请为英语单词 "{word}" 生成完整的学习手册，包含以下五个部分：

1. 核心语言游戏 (core_game)
   - 用形象化、有趣的中文拆解单词
   - 例如：accommodation = "安心！得！神！"
   - 要求：创意、易记、贴近发音、用词文明

2. 正式场景例句 (scenario_formal)
   - 展示单词在正式场合的用法
   - 包含英文例句和中文翻译

3. 日常场景例句 (scenario_casual)
   - 展示单词在日常对话中的用法
   - 包含英文例句和中文翻译

4. 词源拆解 (etymology_breakdown)
   - 从语言学角度分析单词的词根、前缀、后缀
   - 解释单词的构词逻辑

5. 记忆小窍门 (memory_trick)
   - 提供独特的记忆技巧
   - 可以是联想法、谐音法、故事法等

**重要提示**: 请确保所有内容适合教育用途，用词文明，避免任何可能触发安全过滤器的表达。

**返回格式**（必须是有效JSON）：
{{
  "word": "{word}",
  "phonetic": "音标",
  "part_of_speech": "词性",
  "core_game": "核心语言游戏内容",
  "scenario_formal": "正式场景例句（英文 + 中文翻译）",
  "scenario_casual": "日常场景例句（英文 + 中文翻译）",
  "etymology_breakdown": "词源拆解内容",
  "etymology_story": "词源故事（简短有趣的历史背景）",
  "memory_trick": "记忆小窍门",
  "common_mistakes": "常见错误（学习者容易犯的错误）"
}}

请生成单词 "{word}" 的学习手册：'''

    print("安全的Prompt模板已创建:")
    print("1. 移除了可能触发过滤的中文示例 '啊！靠！没得神'")
    print("2. 替换为 '安心！得！神！'")
    print("3. 添加了文明用语的明确要求")
    print("4. 增加了教育用途的强调说明")

    return safe_prompt_template

def main():
    """主函数"""
    print("Gemini Prompt内容分析")
    print("=" * 60)

    # 1. 分析当前prompt内容
    analyze_prompt_content()

    # 2. 创建安全的prompt版本
    safe_prompt = create_safe_prompt()

    # 3. 比较两种版本
    print(f"\n{'='*60}")
    print("问题分析和解决方案")
    print("=" * 60)

    print("发现的问题:")
    print("1. 示例中的'啊！靠！没得神'可能被Gemini误判")
    print("   - '靠'字在中文网络用语中可能有不当含义")
    print("   - Gemini的安全过滤器对中文词汇判断可能过于严格")

    print("\n2. 缺少明确的教育用途说明")
    print("   - 需要明确指出内容用于教育目的")
    print("   - 强调用词文明和适当性")

    print("\n解决方案:")
    print("1. 修改中文示例，避免敏感词汇")
    print("2. 添加教育用途的明确说明")
    print("3. 考虑调整Gemini API的安全设置")
    print("4. 如果问题持续，考虑切换到OpenAI API")

    # 保存安全的prompt版本
    safe_prompt_file = project_root / "app" / "prompts" / "word_generation_safe.py"

    safe_prompt_content = f'''"""安全版本的AI单词生成Prompt模板"""

SAFE_WORD_GENERATION_PROMPT = """{safe_prompt_template}"""

def get_safe_word_generation_prompt(word: str) -> str:
    """获取安全的单词生成Prompt"""
    return SAFE_WORD_GENERATION_PROMPT.format(word=word)
'''

    try:
        with open(safe_prompt_file, 'w', encoding='utf-8') as f:
            f.write(safe_prompt_content)
        print(f"\n安全版本的Prompt已保存到: {safe_prompt_file}")
    except Exception as e:
        print(f"\n保存安全Prompt文件失败: {e}")

if __name__ == "__main__":
    main()