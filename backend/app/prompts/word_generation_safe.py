"""安全版本的AI单词生成Prompt模板"""

SAFE_WORD_GENERATION_PROMPT = '''你是一位专业的英语教学专家，擅长使用"五步语言游戏学习法"帮助学习者记忆长单词。

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


def get_safe_word_generation_prompt(word: str) -> str:
    """获取安全的单词生成Prompt"""
    return SAFE_WORD_GENERATION_PROMPT.format(word=word)