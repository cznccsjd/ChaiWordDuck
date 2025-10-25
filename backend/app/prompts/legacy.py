"""向后兼容层 - 保持现有API接口不变

提供与原有word_generation_gemini_zh_CN.py兼容的接口，
同时内部使用新的PromptManager系统。
"""

import warnings
from typing import Dict, Any

from app.prompts.manager import get_prompt_manager
from app.prompts.enums import Language, AIProvider
from app.core.logging import get_logger

logger = get_logger(__name__)

# 原有的常量保持兼容性
WORD_GENERATION_PROMPT = """你是一位深谙维特根斯坦哲学的"语言游戏设计师"。你的任务不是给单词下定义，而是为用户提供一份清晰、有趣的"游戏手册"，指导他们如何在不同的语言情境中自如地"使用"这个单词。

请严格遵循以下"游戏手册"的**五大结构**，一次性输出所有内容，确保用户阅读完毕后，就能直观地理解并牢牢记住这个单词的"玩法"。

游戏目标单词： **{word}**

---

### 1. 核心游戏：这是什么"局"？ (Core Game)
**指令：** 首先，请用一句话点明这个单词通常在什么样的"语言游戏"或"情景牌局"中被当作关键牌打出。描述这个"局"的本质，而不是单词的定义。

例如：对于单词"Ephemeral"，核心游戏是"捕捉并感叹那些转瞬即逝的美好"。

### 2. 游戏棋盘：它在哪两种"场"上玩？ (Game Boards)
**指令：** 为这个单词提供两个截然不同的"游戏棋盘"，**分别为它们命名一个富有创意和指向性的"场名"**，并各配一句**中英文混合的示例**，展示它在不同场上的玩法。

* **棋盘A (思辨场)：** 展示该单词在抽象、哲学或正式讨论中的用法。
* **棋盘B (生活场)：** 展示该单词在日常、具体或非正式情境中的用法。

**重要示例格式要求：** 示例必须是中英文混合，并将关键词 `{word}` 用括号和中文释义标注，例如："成功的婚姻需要双方不断地进行情感accommodation（调适），以应对彼此性格和生活习惯的差异。"

### 3. 游戏溯源与拆解：这副牌是如何组装的？ (Etymology)
**指令：**
* **卡牌拆解：** 像拆解机械一样，将单词拆分为"前缀 - 词根 - 后缀"，并清晰标注每个部件的核心含义。
* **组装故事：** 像讲述一则轶事一样，简介这些部件是如何组合起来，使其"游戏规则"从最初的形态演变成今天这个样子的。

### 4. 犯规警告：常见的"错招"是什么？ (Common Mistakes)
**指令：** 明确指出一个使用这个单词时最容易犯的"规"（比如与某个形近/义近词混淆），并用一句话点明如何避免这步"错招"。

### 5. 通关秘籍：一招制胜的记忆技巧 (Memory Trick)
**指令：** 提供一个巧妙、甚至有些出人意料的记忆"秘籍"。这个技巧应该能瞬间将单词的核心"玩法"刻入脑海。

---

**返回格式（必须是有效JSON）：**
请将所有生成内容封装在一个 JSON 对象中。

```json
{
  "word": "{word}",
  "phonetic": "[在此处插入音标]",
  "translation": "[在此处插入中文译文]",
  "part_of_speech": "[在此处插入主要词性]",
  "core_game": {
    "content": "[核心游戏的描述]"
  },
  "game_boards": {
    "board_a_speculative": {
      "type": "棋盘A (思辨场)",
      "name": "[富有创意和指向性的场名A]",
      "example": "[中英文混合的完整示例，如：成功的婚姻需要双方不断地进行情感accommodation（调适），以应对彼此性格和生活习惯的差异。]"
    },
    "board_b_life": {
      "type": "棋盘B (生活场)",
      "name": "[富有创意和指向性的场名B]",
      "example": "[中英文混合的完整示例，如：我们提前预订了酒店，但他们说在旅游旺季，找到便宜的accommodation（住宿）非常困难。]"
    }
  },
  "etymology": {
    "breakdown": {
      "prefix": {"part": "[前缀]", "meaning": "[核心含义]"},
      "root": {"part": "[词根]", "meaning": "[核心含义]"},
      "suffix": {"part": "[后缀]", "meaning": "[核心含义]"}
    },
    "story": "[组装故事的内容]"
  },
  "common_mistakes": {
    "warning": "[最容易犯的"规"/错招]",
    "avoidance": "[一句话避免"错招"的技巧]"
  },
  "memory_trick": "[通关秘籍的内容]"
}
```"""


def get_word_generation_prompt(word: str) -> str:
    """获取单词生成Prompt - 向后兼容接口

    Args:
        word: 目标单词

    Returns:
        str: 格式化的prompt字符串

    Note:
        此函数保持与原有接口的兼容性，内部使用新的PromptManager
        会发出弃用警告，建议使用get_prompt_manager().render_prompt()
    """
    warnings.warn(
        "get_word_generation_prompt() is deprecated. "
        "Use get_prompt_manager().render_prompt() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    try:
        # 使用新的PromptManager获取模板
        manager = get_prompt_manager()
        system_prompt, user_prompt = manager.render_prompt(
            word=word,
            language=Language.CHINESE,
            provider=AIProvider.GEMINI
        )

        logger.info(f"使用新的PromptManager生成prompt: {word}")

        # 为了兼容性，返回用户提示词
        return user_prompt

    except Exception as e:
        logger.warning(f"新PromptManager失败，使用降级策略: {e}")

        # 降级到原有的模板
        try:
            return WORD_GENERATION_PROMPT.format(word=word)
        except KeyError as e:
            # 如果格式化失败，使用简单的替换策略
            logger.error(f"降级模板格式化失败: {e}")
            return WORD_GENERATION_PROMPT.replace("{word}", word)


def get_prompt_with_metadata(word: str) -> Dict[str, Any]:
    """获取带元数据的Prompt - 新增的增强接口

    Args:
        word: 目标单词

    Returns:
        Dict[str, Any]: 包含prompt和元数据的字典
    """
    try:
        manager = get_prompt_manager()
        system_prompt, user_prompt = manager.render_prompt(
            word=word,
            language=Language.CHINESE,
            provider=AIProvider.GEMINI
        )

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "language": Language.CHINESE,
            "provider": AIProvider.GEMINI,
            "word": word,
            "generated_by": "PromptManager",
            "config_info": manager.get_config_info()
        }

    except Exception as e:
        logger.error(f"生成Prompt失败: {e}")

        # 返回降级结果
        try:
            user_prompt = WORD_GENERATION_PROMPT.format(word=word)
        except KeyError:
            # 如果格式化失败，使用简单的替换策略
            user_prompt = WORD_GENERATION_PROMPT.replace("{word}", word)

        return {
            "system_prompt": "你是一位专业的英语教学专家。",
            "user_prompt": user_prompt,
            "language": Language.CHINESE,
            "provider": AIProvider.GEMINI,
            "word": word,
            "generated_by": "LegacyFallback",
            "error": str(e)
        }


# 为了完全兼容，保留原有的模块级变量访问
def __getattr__(name: str):
    """动态属性访问，用于兼容原有代码"""
    if name == "WORD_GENERATION_PROMPT":
        logger.debug("访问原有的WORD_GENERATION_PROMPT常量")
        return WORD_GENERATION_PROMPT
    elif name == "get_word_generation_prompt":
        return get_word_generation_prompt
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")