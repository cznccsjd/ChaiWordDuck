"""Gemini AI服务的结构化输出Schema定义"""
from google.genai.types import Schema, Type

# 单词手册数据模型的完整Schema定义
# 基于app.services.ai.base.WordManualData模型定义
WORD_MANUAL_SCHEMA = Schema(
    type=Type.OBJECT,
    properties={
        "word": Schema(
            type=Type.STRING,
            description="学习的单词"
        ),
        "phonetic": Schema(
            type=Type.STRING,
            description="国际音标（可选）"
        ),
        "part_of_speech": Schema(
            type=Type.STRING,
            description="单词词性（可选）"
        ),
        "core_game": Schema(
            type=Type.STRING,
            description="核心语言游戏内容（拆解和创意说明）"
        ),
        "scenario_formal": Schema(
            type=Type.STRING,
            description="正式场景例句（英文 + 中文翻译）"
        ),
        "scenario_casual": Schema(
            type=Type.STRING,
            description="日常场景例句（英文 + 中文翻译）"
        ),
        "etymology_breakdown": Schema(
            type=Type.STRING,
            description="词源拆解内容（词根、前缀、后缀分析）"
        ),
        "etymology_story": Schema(
            type=Type.STRING,
            description="词源故事（简短有趣的历史背景，可选）"
        ),
        "memory_trick": Schema(
            type=Type.STRING,
            description="记忆小窍门（联想法、谐音法等）"
        ),
        "common_mistakes": Schema(
            type=Type.STRING,
            description="常见错误（学习者容易犯的错误，可选）"
        )
    },
    required=[
        "word", "core_game", "scenario_formal", "scenario_casual",
        "etymology_breakdown", "memory_trick"
    ],
    # 注意：pydantic模型中Optional字段不在required列表中
    # 可选字段：phonetic, part_of_speech, etymology_story, common_mistakes
)

# 系统提示词模板
SYSTEM_INSTRUCTION = "你是一位专业的英语教学专家，擅长使用'五步语言游戏学习法'帮助学习者记忆长单词。"

# 用户提示词模板
WORD_GENERATION_PROMPT_TEMPLATE = """
请为英语单词 "{word}" 生成完整的学习手册，必须严格按照以下五个核心部分的要求创作：

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

同时，请根据需要包含以下可选字段：
- phonetic（国际音标）
- part_of_speech（单词词性）
- etymology_story（词源历史背景故事）
- common_mistakes（常见学习错误）

所有内容必须适合教育用途，用词文明，避免任何可能触发安全过滤器的表达。
请严格按照提供的JSON Schema格式返回结果。
"""