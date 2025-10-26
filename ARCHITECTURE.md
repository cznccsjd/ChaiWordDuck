# 拆词鸭 ChaiWord Duck - 技术架构文档

## 1. 文档信息

| 属性 | 内容 |
|------|------|
| **文档版本** | v2.0 |
| **创建日期** | 2025-10-16 |
| **最后更新** | 2025-10-26 |
| **文档作者** | 架构师 |
| **审批状态** | 待评审 |
| **对应PRD版本** | PRD v1.2 |
| **相关文档** | [PRD.md](./PRD.md), [DESIGN.md](./DESIGN.md), [README.md](./README.md) |

---

## 2. 架构概述

### 2.1 设计原则

**核心原则**：
- **渐进式体验**：游客模式优先，降低使用门槛
- **可扩展性**：支持从100到100万用户的无缝扩展
- **性能优先**：95%请求响应时间 < 500ms
- **安全第一**：多层防护，防止滥用和攻击
- **多语言支持**：支持多语言Prompt系统和数据存储
- **向后兼容**：确保现有功能和数据格式的兼容性

**2025年技术标准**：
- 后端：Python 3.12+, FastAPI 0.104+, SQLAlchemy 2.0+ (async)
- 数据库：PostgreSQL 15+, Redis 7+
- 前端：React 18+, TypeScript 5+, Next.js 14+
- 部署：Docker, Kubernetes (可选), CI/CD with GitHub Actions

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web浏览器   │  │  移动浏览器   │  │    桌面应用   │          │
│  │  (React SPA) │  │ (响应式)     │  │   (未来)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                         HTTPS/REST
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      API网关层 (可选)                            │
│  ┌────────────────────────────────────────────────────┐         │
│  │  Nginx / Caddy / Cloudflare (负载均衡 + SSL)        │         │
│  │  - Rate Limiting (30次/分钟/IP)                     │         │
│  │  - DDoS防护                                        │         │
│  │  - 静态资源CDN                                      │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      应用层 (FastAPI)                            │
│                                                                  │
│  ┌───────────────────────────────────────────────────┐          │
│  │           认证与限流中间件                          │          │
│  │  - 可选认证 (Optional Authentication)              │          │
│  │  - 游客识别 (IP + 设备指纹)                         │          │
│  │  - Redis限流检查                                   │          │
│  └───────────────────────────────────────────────────┘          │
│                       │                                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│  │  用户API  │ 单词API  │ 收藏API  │ 查询API  │  AI API   │      │
│  │  /auth   │ /words   │/favorites│ /queries │  /ai     │      │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘      │
│                       │                                          │
│  ┌────────────────────────────────────────────────────┐         │
│  │              业务逻辑层 (Services)                   │         │
│  │  - AuthService (认证服务)                           │         │
│  │  - RateLimitService (限流服务)                        │         │
│  │  - WordService (单词服务)                           │         │
│  │  - FavoriteService (收藏服务)                       │         │
│  │  - AIService (AI生成服务) ⭐ 多语言支持             │         │
│  │  - EmailService (邮件服务)                          │         │
│  │  - WordDataConverter (数据格式转换服务) ⭐ 新增      │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       数据层                                     │
│                                                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │   PostgreSQL 15+     │      │     Redis 7+         │        │
│  │  ─────────────────   │      │  ─────────────────   │        │
│  │  - users             │      │  - 限流计数器         │        │
│  │  - words ⭐ 多语言字段│      │  - 会话缓存          │        │
│  │  - favorites         │      │  - 单词缓存          │        │
│  │  - query_logs        │      │  - IP限流            │        │
│  │  - guest_sessions    │      │  - 多语言Prompt缓存  │        │
│  │  - ai_generation_logs⭐     │      └──────────────────────┘        │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    外部服务层                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ OpenAI API   │  │  SendGrid    │  │  Sentry监控  │         │
│  │ (多语言AI)   │  │  (邮件服务)  │  │  (错误追踪)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 技术栈总览

| 层级 | 技术选型 | 版本要求 | 说明 |
|------|---------|---------|------|
| **前端** | Next.js | 14+ | React SSR/SSG框架 |
| | React | 18+ | UI框架 |
| | TypeScript | 5+ | 类型安全 |
| | Tailwind CSS | 3+ | 样式框架 |
| | Zustand/Jotai | - | 轻量状态管理 |
| **后端** | FastAPI | 0.104+ | 现代Python Web框架 |
| | Python | 3.12+ | 编程语言 |
| | SQLAlchemy | 2.0+ | ORM (async模式) |
| | Pydantic | 2.0+ | 数据验证 |
| | asyncpg | - | PostgreSQL异步驱动 |
| | redis-py | 5.0+ | Redis客户端 (async支持) |
| **数据库** | PostgreSQL | 15+ | 关系数据库，支持JSONB |
| | Redis | 7+ | 缓存和限流 |
| **认证** | JWT | - | 无状态认证 |
| | bcrypt | - | 密码加密 |
| **部署** | Docker | 24+ | 容器化 |
| | Docker Compose | 2.0+ | 本地开发 |
| | GitHub Actions | - | CI/CD |
| | Vercel | - | 前端托管 (可选) |
| | Railway/Render | - | 后端托管 (可选) |

---

## 3. 多语言Prompt系统架构 (v2.0核心特性)

### 3.1 设计理念

**从单一语言到多语言支持的演进**：

传统设计仅支持英语单词学习，新架构支持：
1. **多语言Prompt模板**：支持不同语言的AI生成模板
2. **混合存储策略**：简单字段使用VARCHAR/TEXT，复杂嵌套使用JSONB
3. **向后兼容**：保证现有数据和API的完全兼容
4. **动态语言检测**：根据用户偏好自动选择语言版本

### 3.2 数据模型升级

#### 3.2.1 Words表结构扩展

```sql
-- 原有字段（保持不变）
id: integer (primary key)
word: varchar(100) (unique)
phonetic: varchar(200)
part_of_speech: varchar(255)
core_game: text
scenario_formal: text
scenario_casual: text
etymology_breakdown: text
etymology_story: text
common_mistakes: text
memory_trick: text
is_golden: boolean
source: varchar(50)
created_at: timestamp
updated_at: timestamp

-- 新增多语言支持字段 ⭐ v2.0新增
translation: varchar(500)                -- 单词翻译
language_code: varchar(10)               -- 语言代码 (en, zh_CN, etc.)
prompt_version: varchar(20)               -- Prompt版本标识
is_legacy_format: boolean                -- 是否为旧格式数据

-- 新增JSONB字段用于复杂嵌套结构 ⭐ v2.0新增
core_game_new: jsonb                     -- 结构化核心游戏数据
game_boards: jsonb                       -- 结构化游戏棋盘数据
etymology_new: jsonb                     -- 结构化词源数据
common_mistakes_new: jsonb               -- 结构化常见错误数据
```

#### 3.2.2 新字段详解

**简单字段（VARCHAR/TEXT）**：
- `translation`: 单词的翻译，支持多语言
- `language_code`: 语言代码，遵循ISO标准
  - `en`: 英语
  - `zh_CN`: 简体中文
  - `zh_TW`: 繁体中文
  - `ja`: 日语
  - `ko`: 韩语
  - `fr`: 法语
  - `de`: 德语
  - `es`: 西班牙语
  - `it`: 意大利语
  - `ru`: 俄语

**复杂字段（JSONB）**：
- `core_game_new`: 结构化核心游戏数据
```json
{
  "content": "这是一个问候语游戏",
  "difficulty_level": "beginner",
  "estimated_time": "5分钟",
  "learning_objectives": ["学习基本问候", "理解使用场景"]
}
```

- `game_boards`: 结构化游戏棋盘数据
```json
{
  "board_a_speculative": {
    "type": "棋盘A (思辨场)",
    "name": "思辨场景",
    "example": "在正式会议中使用hello表示问候",
    "context": "business_meeting",
    "formality_level": "formal"
  },
  "board_b_life": {
    "type": "棋盘B (生活场)",
    "name": "生活场景",
    "example": "和朋友见面时说hello",
    "context": "casual_meeting",
    "formality_level": "informal"
  }
}
```

- `etymology_new`: 结构化词源数据
```json
{
  "breakdown": {
    "prefix": {
      "part": "",
      "meaning": "",
      "examples": []
    },
    "root": {
      "part": "hello",
      "meaning": "问候",
      "examples": ["hello", "hallo", "hola"]
    },
    "suffix": {
      "part": "",
      "meaning": "",
      "examples": []
    }
  },
  "story": "源自古英语hell，用于吸引注意力",
  "historical_usage": [
    {"period": "古英语", "form": "hell", "meaning": "呼叫"},
    {"period": "中古英语", "form": "hello", "meaning": "问候"}
  ]
}
```

### 3.3 数据格式转换系统

#### 3.3.1 WordDataConverter服务

```python
# app/models/word_converter.py

from typing import Dict, Any, Optional
from app.models.word import Word

class WordDataConverter:
    """单词数据格式转换器"""

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'zh_CN': '简体中文',
        'zh_TW': '繁体中文',
        'ja': '日本語',
        'ko': '한국어',
        'fr': 'Français',
        'de': 'Deutsch',
        'es': 'Español',
        'it': 'Italiano',
        'ru': 'Русский'
    }

    @classmethod
    def get_word_display_format(cls, word: Word, preferred_format: str = 'auto') -> Dict[str, Any]:
        """
        获取单词的显示格式数据，自动处理新旧格式

        Args:
            word: Word模型实例
            preferred_format: 首选格式 ('auto', 'legacy', 'new')

        Returns:
            标准化的显示数据字典
        """
        if preferred_format == 'auto':
            # 自动选择格式：优先新格式，降级到旧格式
            if cls._should_use_new_format(word):
                return cls._convert_to_new_format(word)
            else:
                return cls._convert_to_legacy_format(word)
        elif preferred_format == 'new':
            return cls._convert_to_new_format(word)
        else:
            return cls._convert_to_legacy_format(word)

    @classmethod
    def _should_use_new_format(cls, word: Word) -> bool:
        """判断是否应该使用新格式"""
        # 1. 检查格式标记
        if hasattr(word, 'is_legacy_format') and not word.is_legacy_format:
            return True

        # 2. 检查新格式字段是否有数据
        if (word.core_game_new or word.game_boards or
            word.etymology_new or word.common_mistakes_new):
            return True

        # 3. 检查多语言字段
        if (hasattr(word, 'language_code') and word.language_code != 'en') or \
           (hasattr(word, 'translation') and word.translation):
            return True

        return False

    @classmethod
    def _convert_to_new_format(cls, word: Word) -> Dict[str, Any]:
        """转换为新格式数据"""
        return {
            'id': word.id,
            'word': word.word,
            'phonetic': getattr(word, 'phonetic', None),
            'translation': getattr(word, 'translation', None) or '',
            'part_of_speech': getattr(word, 'part_of_speech', None),
            'language_code': getattr(word, 'language_code', 'en'),
            'core_game': cls._get_core_game_content(word),
            'game_boards': cls._get_game_boards_data(word),
            'etymology': cls._get_etymology_data(word),
            'common_mistakes': cls._get_common_mistakes_data(word),
            'memory_trick': cls._get_memory_trick_content(word),
            'is_golden': word.is_golden,
            'source': getattr(word, 'source', 'ai'),
            'prompt_version': getattr(word, 'prompt_version', 'v1.0'),
            'created_at': word.created_at.isoformat() if word.created_at else None,
            'updated_at': word.updated_at.isoformat() if word.updated_at else None
        }

    @classmethod
    def _convert_to_legacy_format(cls, word: Word) -> Dict[str, Any]:
        """转换为旧格式数据（向后兼容）"""
        return {
            'id': word.id,
            'word': word.word,
            'phonetic': getattr(word, 'phonetic', None),
            'part_of_speech': getattr(word, 'part_of_speech', None),
            'core_game': word.core_game,
            'scenario_formal': word.scenario_formal,
            'scenario_casual': word.scenario_casual,
            'etymology_breakdown': word.etymology_breakdown,
            'etymology_story': getattr(word, 'etymology_story', None),
            'common_mistakes': word.common_mistakes,
            'memory_trick': word.memory_trick,
            'is_golden': word.is_golden,
            'source': getattr(word, 'source', 'ai'),
            'created_at': word.created_at.isoformat() if word.created_at else None,
            'updated_at': word.updated_at.isoformat() if word.updated_at else None
        }
```

#### 3.3.2 向后兼容处理

Word模型提供兼容方法：

```python
class Word(Base):
    # ... 其他字段和方法 ...

    def get_display_data(self, preferred_format: str = 'auto') -> Dict[str, Any]:
        """获取显示数据，自动处理格式转换"""
        return WordDataConverter.get_word_display_format(self, preferred_format)

    def is_new_format(self) -> bool:
        """检查是否为新格式数据"""
        return WordDataConverter._should_use_new_format(self)

    def get_core_game_content(self) -> str:
        """获取核心游戏内容（兼容新旧格式）"""
        if self.is_new_format() and self.core_game_new:
            return self.core_game_new.get('content', '')
        return self.core_game

    def get_game_boards_data(self) -> Dict[str, Any]:
        """获取游戏棋盘数据（兼容新旧格式）"""
        if self.is_new_format() and self.game_boards:
            return self.game_boards

        # 返回旧格式的默认结构
        return {
            'board_a_speculative': {
                'type': '棋盘A (思辨场)',
                'name': '思辨场景',
                'example': self.scenario_formal
            },
            'board_b_life': {
                'type': '棋盘B (生活场)',
                'name': '生活场景',
                'example': self.scenario_casual
            }
        }
```

### 3.4 多语言AI生成系统

#### 3.4.1 多语言Prompt模板

```python
# app/services/multilang_prompt.py

class MultilangPromptService:
    """多语言Prompt生成服务"""

    PROMPT_TEMPLATES = {
        'en': {
            'v1.0': """
Generate a comprehensive word learning guide for the English word "{word}".

Include the following sections:
1. Core Game: Create an engaging learning game concept
2. Scenarios: Formal and casual usage examples
3. Etymology: Word breakdown and origin story
4. Common Mistakes: Typical errors and how to avoid them
5. Memory Tricks: Creative memorization techniques

Please output in JSON format matching the v1.0 schema.
""",
            'v2.0': """
Generate a structured multilingual word learning guide for "{word}".

Language: {language_code}
Target Audience: {target_audience}

Output Schema (JSON):
{
  "core_game": {{
    "content": "string",
    "difficulty_level": "beginner|intermediate|advanced",
    "estimated_time": "string",
    "learning_objectives": ["string"]
  }},
  "game_boards": {{
    "board_a_speculative": {{
      "type": "string",
      "name": "string",
      "example": "string",
      "context": "string",
      "formality_level": "formal|informal"
    }},
    "board_b_life": {{
      "type": "string",
      "name": "string",
      "example": "string",
      "context": "string",
      "formality_level": "formal|informal"
    }}
  }},
  "etymology": {{
    "breakdown": {{
      "prefix": {{"part": "string", "meaning": "string", "examples": ["string"]}},
      "root": {{"part": "string", "meaning": "string", "examples": ["string"]}},
      "suffix": {{"part": "string", "meaning": "string", "examples": ["string"]}}
    }},
    "story": "string",
    "historical_usage": [{{"period": "string", "form": "string", "meaning": "string"}}]
  }},
  "common_mistakes": {{
    "warning": "string",
    "avoidance": "string",
    "examples": [{{"wrong": "string", "correct": "string", "explanation": "string"}}]
  }}
}}
""",
        },
        'zh_CN': {
            'v1.0': """
为英语单词"{word}"生成综合学习指南。

包含以下部分：
1. 核心游戏：创建有趣的学习游戏概念
2. 场景应用：正式和日常使用例子
3. 词源学：单词拆解和起源故事
4. 常见错误：典型错误及避免方法
5. 记忆技巧：创意记忆技巧

请按照v1.0模式输出JSON格式。
""",
            'v2.0': """
为英语单词"{word}"生成结构化多语言学习指南。

语言：{language_code}
目标受众：{target_audience}

输出模式（JSON）：
{schema}
"""
        }
    }

    @classmethod
    def generate_prompt(cls, word: str, language_code: str = 'en',
                       prompt_version: str = 'v2.0', target_audience: str = 'adult') -> str:
        """生成多语言Prompt"""
        template = cls.PROMPT_TEMPLATES.get(language_code, {}).get(prompt_version)
        if not template:
            # 降级到英文v2.0模板
            template = cls.PROMPT_TEMPLATES['en']['v2.0']

        return template.format(
            word=word,
            language_code=language_code,
            target_audience=target_audience,
            schema=cls._get_schema_for_language(language_code)
        )

    @classmethod
    def _get_schema_for_language(cls, language_code: str) -> str:
        """获取对应语言的JSON schema描述"""
        # 返回本地化的schema描述
        return cls.PROMPT_TEMPLATES[language_code]['v2.0'].split('Output Schema (JSON):')[1].strip()
```

#### 3.4.2 AI服务增强

```python
# app/services/ai_service.py

class AIService:
    """AI生成服务（增强多语言支持）"""

    def __init__(self, openai_client, multilang_prompt_service):
        self.openai_client = openai_client
        self.prompt_service = multilang_prompt_service

    async def generate_word_content(
        self,
        word: str,
        language_code: str = 'en',
        prompt_version: str = 'v2.0',
        target_audience: str = 'adult'
    ) -> Dict[str, Any]:
        """
        生成多语言单词学习内容

        Args:
            word: 目标单词
            language_code: 语言代码
            prompt_version: Prompt版本
            target_audience: 目标受众

        Returns:
            结构化的单词学习数据
        """
        # 1. 生成多语言Prompt
        prompt = self.prompt_service.generate_prompt(
            word=word,
            language_code=language_code,
            prompt_version=prompt_version,
            target_audience=target_audience
        )

        # 2. 调用OpenAI API
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a language learning expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        # 3. 解析JSON响应
        content = response.choices[0].message.content
        try:
            structured_data = json.loads(content)
        except json.JSONDecodeError:
            # JSON解析失败，使用备用格式
            structured_data = self._fallback_parsing(content)

        # 4. 返回结构化数据
        return {
            'core_game_new': structured_data.get('core_game'),
            'game_boards': structured_data.get('game_boards'),
            'etymology_new': structured_data.get('etymology'),
            'common_mistakes_new': structured_data.get('common_mistakes'),
            'translation': structured_data.get('translation'),
            'language_code': language_code,
            'prompt_version': prompt_version,
            'is_legacy_format': False
        }

    def _fallback_parsing(self, content: str) -> Dict[str, Any]:
        """JSON解析失败时的备用解析"""
        # 实现简单的文本解析逻辑
        # 返回基本结构，避免完全失败
        return {
            'core_game': {'content': content[:500]},
            'game_boards': {},
            'etymology': {},
            'common_mistakes': {}
        }
```

### 3.5 数据库迁移策略

#### 3.5.1 渐进式迁移

采用三阶段迁移策略，确保数据完整性：

**阶段1：添加新字段（零停机）**
```sql
-- 1. 添加新字段，允许NULL
ALTER TABLE words ADD COLUMN translation VARCHAR(500);
ALTER TABLE words ADD COLUMN language_code VARCHAR(10) DEFAULT 'en';
ALTER TABLE words ADD COLUMN prompt_version VARCHAR(20) DEFAULT 'v1.0';
ALTER TABLE words ADD COLUMN is_legacy_format BOOLEAN DEFAULT TRUE;

-- 2. 添加JSONB字段
ALTER TABLE words ADD COLUMN core_game_new JSONB;
ALTER TABLE words ADD COLUMN game_boards JSONB;
ALTER TABLE words ADD COLUMN etymology_new JSONB;
ALTER TABLE words ADD COLUMN common_mistakes_new JSONB;
```

**阶段2：数据迁移（后台进行）**
```sql
-- 3. 迁移现有数据到新格式
UPDATE words SET
    core_game_new = jsonb_build_object('content', core_game),
    game_boards = jsonb_build_object(
        'board_a_speculative', jsonb_build_object(
            'type', '棋盘A (思辨场)',
            'name', '思辨场景',
            'example', scenario_formal
        ),
        'board_b_life', jsonb_build_object(
            'type', '棋盘B (生活场)',
            'name', '生活场景',
            'example', scenario_casual
        )
    ),
    etymology_new = jsonb_build_object(
        'breakdown', jsonb_build_object(
            'prefix', jsonb_build_object('part', '', 'meaning', ''),
            'root', jsonb_build_object('part', etymology_breakdown, 'meaning', '词根拆解'),
            'suffix', jsonb_build_object('part', '', 'meaning', '')
        ),
        'story', COALESCE(etymology_story, '')
    ),
    common_mistakes_new = jsonb_build_object(
        'warning', common_mistakes,
        'avoidance', memory_trick
    )
WHERE is_legacy_format = TRUE;
```

**阶段3：索引优化（低峰期）**
```sql
-- 4. 创建性能优化索引
CREATE INDEX CONCURRENTLY idx_words_core_game_new_gin
ON words USING gin (core_game_new);

CREATE INDEX CONCURRENTLY idx_words_game_boards_gin
ON words USING gin (game_boards);

CREATE INDEX CONCURRENTLY idx_words_etymology_new_gin
ON words USING gin (etymology_new);

CREATE INDEX CONCURRENTLY idx_words_common_mistakes_new_gin
ON words USING gin (common_mistakes_new);

CREATE INDEX CONCURRENTLY idx_words_language_code
ON words (language_code);

CREATE INDEX CONCURRENTLY idx_words_prompt_version
ON words (prompt_version);
```

#### 3.5.2 完整迁移脚本

已实现：`backend/alembic/versions/005_add_multilang_prompt_support.py`

该脚本包含：
- ✅ 新字段添加（支持向后兼容）
- ✅ 数据迁移逻辑
- ✅ 索引优化
- ✅ 约束检查
- ✅ 回滚方案

### 3.6 API兼容性处理

#### 3.6.1 响应格式标准化

API响应自动处理格式转换：

```python
# app/schemas/word.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class WordResponse(BaseModel):
    """单词查询响应（支持新旧格式）"""

    # 基础字段
    id: int
    word: str
    phonetic: Optional[str] = None
    part_of_speech: Optional[str] = None

    # 多语言字段 ⭐ v2.0新增
    translation: Optional[str] = Field(default=None, description="单词翻译")
    language_code: Optional[str] = Field(default="en", description="语言代码")

    # 核心内容（自动格式适配）
    core_game: str = Field(description="核心游戏内容")
    game_boards: Optional[Dict[str, Any]] = Field(default=None, description="游戏棋盘数据")
    etymology: Optional[Dict[str, Any]] = Field(default=None, description="词源数据")
    common_mistakes: Optional[Dict[str, Any]] = Field(default=None, description="常见错误数据")
    memory_trick: str = Field(description="记忆技巧")

    # 元数据
    is_golden: bool = Field(description="是否黄金手册")
    source: str = Field(description="数据来源")
    prompt_version: Optional[str] = Field(default=None, description="Prompt版本")

    # 向后兼容字段（仅当include_legacy=true时返回）
    scenario_formal: Optional[str] = Field(default=None, include=False)
    scenario_casual: Optional[str] = Field(default=None, include=False)
    etymology_breakdown: Optional[str] = Field(default=None, include=False)
    etymology_story: Optional[str] = Field(default=None, include=False)

    class Config:
        from_attributes = True

        @classmethod
        def from_word_model(cls, word: 'Word', include_legacy: bool = False):
            """从Word模型创建响应，自动处理格式转换"""
            display_data = word.get_display_data('auto')

            if include_legacy:
                # 包含向后兼容字段
                display_data.update({
                    'scenario_formal': word.scenario_formal,
                    'scenario_casual': word.scenario_casual,
                    'etymology_breakdown': word.etymology_breakdown,
                    'etymology_story': word.etymology_story
                })

            return cls(**display_data)
```

#### 3.6.2 API端点升级

```python
# app/api/v1/endpoints/words.py

from fastapi import APIRouter, Depends, Query
from typing import Optional

router = APIRouter()

@router.get("/words/query/{word}")
async def query_word(
    word: str,
    include_legacy: bool = Query(default=False, description="是否包含向后兼容字段"),
    user_or_guest: Union[User, GuestIdentifier] = Depends(get_user_or_guest),
    db: AsyncSession = Depends(get_db)
):
    """
    查询单词详细信息（支持多语言和向后兼容）

    Args:
        word: 要查询的单词
        include_legacy: 是否包含向后兼容的字段
        user_or_guest: 用户或游客标识
        db: 数据库会话
    """
    # 1. 查询单词
    word_model = await word_service.get_word_by_text(db, word)
    if not word_model:
        # 2. 尝试AI生成
        word_data = await ai_service.generate_word_content(word)
        word_model = await word_service.create_word(db, word_data)

    # 3. 检查查询限制
    await rate_limit_service.check_query_limit(user_or_guest, word_model.id)

    # 4. 记录查询日志
    await query_log_service.create_query_log(
        db, user_or_guest, word_model.id
    )

    # 5. 返回响应（自动格式适配）
    response = WordResponse.from_word_model(
        word_model,
        include_legacy=include_legacy
    )

    return {
        "success": True,
        "data": response.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 4. 性能优化策略

### 4.1 数据库优化

#### 4.1.1 JSONB索引优化

```sql
-- 1. GIN索引用于JSONB字段查询
CREATE INDEX CONCURRENTLY idx_words_core_game_new_gin
ON words USING gin (core_game_new);

-- 2. 特定路径的索引（如果经常查询特定字段）
CREATE INDEX CONCURRENTLY idx_words_game_boards_path
ON words USING gin ((game_boards->'board_a_speculative'));

-- 3. 语言代码索引（多语言查询优化）
CREATE INDEX CONCURRENTLY idx_words_language_code_word
ON words (language_code, word);

-- 4. 混合索引（格式+语言+黄金手册）
CREATE INDEX CONCURRENTLY idx_words_format_lang_golden
ON words (is_legacy_format, language_code, is_golden);
```

#### 4.1.2 查询优化

```python
# app/services/word_query_optimizer.py

class WordQueryOptimizer:
    """单词查询优化器"""

    @staticmethod
    async def search_words_optimized(
        db: AsyncSession,
        query: str,
        language_code: Optional[str] = None,
        is_golden: Optional[bool] = None,
        limit: int = 20
    ) -> List[Word]:
        """
        优化的单词搜索

        优化策略：
        1. 优先使用索引
        2. 分页查询
        3. 只查询必要字段
        """

        # 构建优化查询
        stmt = select(Word).where(Word.word.ilike(f"%{query}%"))

        # 添加语言过滤（使用索引）
        if language_code:
            stmt = stmt.where(Word.language_code == language_code)

        # 添加黄金手册过滤
        if is_golden is not None:
            stmt = stmt.where(Word.is_golden == is_golden)

        # 限制查询字段（性能优化）
        stmt = stmt.options(
            load_only(
                Word.id, Word.word, Word.phonetic, Word.translation,
                Word.language_code, Word.is_golden, Word.source
            )
        )

        # 分页
        stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()
```

### 4.2 缓存策略

#### 4.2.1 多层缓存架构

```python
# app/services/cache_service.py

class MultilangCacheService:
    """多语言缓存服务"""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def get_word_cached(
        self,
        word: str,
        language_code: str = 'en',
        format_type: str = 'auto'
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的单词数据

        缓存键结构：
        word:cache:{word}:{language_code}:{format_type}
        """
        cache_key = f"word:cache:{word}:{language_code}:{format_type}"

        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        return None

    async def cache_word_data(
        self,
        word: str,
        language_code: str,
        format_type: str,
        data: Dict[str, Any],
        ttl: int = 3600  # 1小时
    ):
        """缓存单词数据"""
        cache_key = f"word:cache:{word}:{language_code}:{format_type}"
        await self.redis.setex(
            cache_key,
            ttl,
            json.dumps(data, ensure_ascii=False)
        )

    async def get_multilang_prompt_cached(
        self,
        language_code: str,
        prompt_version: str = 'v2.0'
    ) -> Optional[str]:
        """获取缓存的多语言Prompt"""
        cache_key = f"prompt:template:{language_code}:{prompt_version}"
        return await self.redis.get(cache_key)

    async def cache_translation_bulk(
        self,
        translations: Dict[str, str],
        language_code: str,
        ttl: int = 86400  # 24小时
    ):
        """批量缓存翻译"""
        pipe = self.redis.pipeline()
        for word, translation in translations.items():
            cache_key = f"translation:{language_code}:{word}"
            pipe.setex(cache_key, ttl, translation)
        await pipe.execute()
```

### 4.3 AI生成优化

#### 4.3.1 预生成机制

```python
# app/services/pre_generation_service.py

class PreGenerationService:
    """预生成服务（减少实时AI调用）"""

    async def pre_generate_popular_words(self, language_code: str = 'en'):
        """
        预生成热门单词

        策略：
        1. 基于查询频率识别热门单词
        2. 批量生成多语言版本
        3. 缓存生成结果
        """

        # 1. 获取热门单词列表
        popular_words = await self._get_popular_words(limit=100)

        # 2. 批量生成
        batch_size = 10
        for i in range(0, len(popular_words), batch_size):
            batch = popular_words[i:i + batch_size]
            await self._generate_batch(batch, language_code)

    async def _generate_batch(self, words: List[str], language_code: str):
        """批量生成单词内容"""
        tasks = [
            self.ai_service.generate_word_content(
                word=word,
                language_code=language_code
            )
            for word in words
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for word, result in zip(words, results):
            if isinstance(result, Exception):
                logger.error(f"生成失败: {word} - {result}")
                continue

            # 缓存生成结果
            await self.cache_service.cache_word_data(
                word=word,
                language_code=language_code,
                format_type='new',
                data=result
            )
```

---

## 5. 监控与可观测性

### 5.1 多语言指标监控

```python
# app/core/multilang_metrics.py

from prometheus_client import Counter, Histogram, Gauge

# 多语言相关指标
multilang_requests_total = Counter(
    'multilang_requests_total',
    '多语言请求总数',
    ['language_code', 'prompt_version', 'status']
)

multilang_generation_duration = Histogram(
    'multilang_generation_duration_seconds',
    '多语言内容生成时间',
    ['language_code', 'prompt_version']
)

multilang_cache_hit_rate = Gauge(
    'multilang_cache_hit_rate',
    '多语言缓存命中率',
    ['language_code']
)

format_conversion_requests = Counter(
    'format_conversion_requests_total',
    '格式转换请求数',
    ['from_format', 'to_format', 'success']
)

# 数据存储指标
legacy_format_ratio = Gauge(
    'legacy_format_ratio',
    '旧格式数据占比'
)

multilang_data_ratio = Gauge(
    'multilang_data_ratio',
    '多语言数据占比',
    ['language_code']
)
```

### 5.2 日志增强

```python
# app/core/multilang_logging.py

import structlog

logger = structlog.get_logger(__name__)

def log_multilang_operation(
    operation: str,
    word: str,
    language_code: str,
    prompt_version: str,
    success: bool,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None
):
    """记录多语言操作日志"""
    log_data = {
        "operation": operation,
        "word": word,
        "language_code": language_code,
        "prompt_version": prompt_version,
        "success": success
    }

    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms

    if error_message:
        log_data["error"] = error_message

    if success:
        logger.info("multilang_operation_success", **log_data)
    else:
        logger.error("multilang_operation_failed", **log_data)

# 使用示例
log_multilang_operation(
    operation="ai_generation",
    word="hello",
    language_code="zh_CN",
    prompt_version="v2.0",
    success=True,
    duration_ms=1200
)
```

---

## 6. 安全与合规

### 6.1 数据隐私保护

```python
# app/services/privacy_service.py

class PrivacyService:
    """数据隐私保护服务"""

    @staticmethod
    def anonymize_query_logs(log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        匿名化查询日志

        移除或哈希化个人可识别信息（PII）
        """
        anonymized = log_data.copy()

        # 移除敏感字段
        sensitive_fields = ['ip_address', 'user_agent']
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = hashlib.sha256(
                    anonymized[field].encode()
                ).hexdigest()[:16]  # 只保留前16位哈希

        return anonymized

    @staticmethod
    def get_language_preference_consent(language_code: str) -> bool:
        """
        获取语言偏好同意状态

        某些语言可能需要特殊的用户同意
        """
        privacy_settings = {
            'en': True,  # 英语默认同意
            'zh_CN': True,  # 简体中文默认同意
            'zh_TW': True,  # 繁体中文默认同意
            # 其他语言可能需要明确同意
        }

        return privacy_settings.get(language_code, False)
```

### 6.2 内容审核

```python
# app/services/content_moderation.py

class ContentModerationService:
    """内容审核服务"""

    # 敏感词列表（示例）
    SENSITIVE_WORDS = {
        'en': ['profanity1', 'profanity2'],
        'zh_CN': ['敏感词1', '敏感词2']
    }

    @classmethod
    def check_content_appropriate(
        cls,
        content: str,
        language_code: str = 'en'
    ) -> Tuple[bool, List[str]]:
        """
        检查内容是否适当

        Returns:
            (是否适当, 发现的问题列表)
        """
        issues = []
        sensitive_words = cls.SENSITIVE_WORDS.get(language_code, [])

        for word in sensitive_words:
            if word.lower() in content.lower():
                issues.append(f"包含敏感词: {word}")

        # 检查其他规则
        if len(content) < 10:
            issues.append("内容过短")

        return len(issues) == 0, issues

    @classmethod
    def sanitize_content(cls, content: str) -> str:
        """清理敏感内容"""
        # 实现内容清理逻辑
        return content
```

---

## 7. 部署指南

### 7.1 环境准备

#### 7.1.1 数据库要求

```bash
# PostgreSQL 15+ 配置
# postgresql.conf 关键配置

# 1. 启用JSONB支持（默认已启用）
# 2. 优化内存设置
shared_buffers = 256MB                    # 根据服务器内存调整
effective_cache_size = 1GB               # 根据服务器内存调整
work_mem = 4MB                           # 提高JSONB查询性能

# 3. 连接配置
max_connections = 100                     # 并发连接数

# 4. 日志配置
log_statement = 'all'                    # 记录所有SQL语句
log_min_duration_statement = 1000         # 记录慢查询（1秒+）
```

#### 7.1.2 Redis配置

```bash
# redis.conf 关键配置

# 1. 内存配置
maxmemory 512mb                         # 根据服务器内存调整
maxmemory-policy allkeys-lru             # 内存满时的淘汰策略

# 2. 持久化配置
save 900 1                              # 15分钟内有1个key变更就保存
save 300 10                             # 5分钟内有10个key变更就保存
save 60 10000                           # 1分钟内有10000个key变更就保存

# 3. 网络配置
bind 127.0.0.1                          # 绑定地址
port 6379                               # 端口

# 4. 安全配置
requirepass your-redis-password         # 设置密码
```

### 7.2 部署步骤

#### 7.2.1 数据库迁移

```bash
# 1. 备份数据库
pg_dump -h localhost -U postgres -d chaiword_duck > backup_before_migration.sql

# 2. 检查迁移状态
cd backend
pdm run alembic current
pdm run alembic history

# 3. 执行迁移
pdm run alembic upgrade head

# 4. 验证迁移结果
pdm run python -c "
from app.core.database import get_db_session
from app.models.word import Word
import asyncio

async def verify():
    async with get_db_session() as db:
        result = await db.execute('SELECT COUNT(*) FROM words')
        total = result.scalar()
        result = await db.execute('SELECT COUNT(*) FROM words WHERE is_legacy_format = false')
        new_format = result.scalar()
        print(f'总单词数: {total}')
        print(f'新格式单词数: {new_format}')
        print(f'迁移比例: {new_format/total*100:.1f}%')

asyncio.run(verify())
"

# 5. 性能测试
pdm run python -c "
import asyncio
from app.services.word import WordService
from app.core.database import get_db_session

async def test_performance():
    async with get_db_session() as db:
        service = WordService()
        # 测试查询性能
        start = time.time()
        word = await service.get_word_by_text(db, 'hello')
        duration = time.time() - start
        print(f'查询耗时: {duration*1000:.1f}ms')

asyncio.run(test_performance())
"
```

#### 7.2.2 应用部署

```bash
# 1. 环境变量配置
# .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chaiword_duck
REDIS_URL=redis://:password@localhost:6379/0
OPENAI_API_KEY=sk-your-api-key

# 多语言配置
DEFAULT_LANGUAGE_CODE=en
SUPPORTED_LANGUAGES=en,zh_CN,zh_TW,ja,ko,fr,de,es,it,ru
PROMPT_VERSION=v2.0

# 2. 安装依赖
cd backend
pdm install

# 3. 运行测试
pdm run pytest tests/ -v

# 4. 启动服务
pdm run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. 健康检查
curl http://localhost:8000/health
```

### 7.3 Docker部署

#### 7.3.1 Dockerfile优化

```dockerfile
# backend/Dockerfile

FROM python:3.12-slim

# 1. 设置工作目录
WORKDIR /app

# 2. 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 3. 复制依赖文件
COPY pyproject.toml pdm.lock ./

# 4. 安装PDM并安装依赖
RUN pip install --no-cache-dir pdm && \
    pdm config pypi.url https://pypi.org/simple && \
    pdm install --prod --no-dev

# 5. 复制应用代码
COPY . .

# 6. 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 7. 创建非root用户
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# 8. 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 9. 暴露端口
EXPOSE 8000

# 10. 启动命令
CMD ["pdm", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 7.3.2 Docker Compose

```yaml
# docker-compose.yml

version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: chaiword_duck
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass password
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@postgres:5432/chaiword_duck
      REDIS_URL: redis://:password@redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DEFAULT_LANGUAGE_CODE: en
      PROMPT_VERSION: v2.0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/v1
    depends_on:
      - backend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## 8. 故障排除

### 8.1 常见问题

#### 8.1.1 数据库问题

**问题：迁移失败**
```bash
# 诊断步骤
1. 检查PostgreSQL版本
psql --version  # 需要 15+

2. 检查数据库连接
psql -h localhost -U postgres -d chaiword_duck

3. 检查表结构
\d words

4. 检查迁移状态
pdm run alembic current

# 解决方案
1. 回滚迁移
pdm run alembic downgrade -1

2. 检查错误日志
tail -f logs/app.log

3. 修复问题后重新执行
pdm run alembic upgrade head
```

**问题：JSONB查询性能慢**
```sql
-- 诊断
EXPLAIN ANALYZE SELECT * FROM words WHERE core_game_new->>'content' LIKE '%game%';

-- 解决方案
1. 添加GIN索引
CREATE INDEX CONCURRENTLY idx_words_core_game_new_gin ON words USING gin (core_game_new);

2. 优化查询
SELECT * FROM words WHERE core_game_new @> '{"content": "game"}';

3. 使用表达式索引
CREATE INDEX CONCURRENTLY idx_words_content ON words USING gin ((core_game_new->'content'));
```

#### 8.1.2 AI生成问题

**问题：多语言Prompt生成失败**
```python
# 诊断步骤
import json
from app.services.multilang_prompt import MultilangPromptService

# 测试Prompt生成
prompt = MultilangPromptService.generate_prompt(
    word='hello',
    language_code='zh_CN',
    prompt_version='v2.0'
)
print(prompt)

# 解决方案
1. 检查Prompt模板
2. 验证JSON schema
3. 添加错误处理
```

**问题：OpenAI API限流**
```python
# 解决方案
1. 实现指数退避重试
import asyncio
import random

async def generate_with_retry(word, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await ai_service.generate_word_content(word)
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt + random.random()
            await asyncio.sleep(wait_time)

2. 使用请求队列
3. 实现缓存减少API调用
```

### 8.2 性能调优

#### 8.2.1 数据库优化

```sql
-- 1. 查看慢查询
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;

-- 2. 优化索引使用
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'words';

-- 3. 分析表统计信息
ANALYZE words;

-- 4. 检查索引使用情况
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'words';
```

#### 8.2.2 Redis优化

```bash
# 1. 监控Redis性能
redis-cli info memory
redis-cli info stats
redis-cli slowlog get 10

# 2. 优化内存使用
redis-cli --eval optimize_memory.lua

# 3. 监控缓存命中率
redis-cli info keyspace
```

### 8.3 监控告警

```yaml
# monitoring/multilang-alerts.yml

groups:
  - name: multilang_system
    interval: 30s
    rules:
      # 多语言生成成功率
      - alert: LowMultilangGenerationSuccessRate
        expr: |
          (
            sum(rate(multilang_requests_total{status="success"}[5m])) /
            sum(rate(multilang_requests_total[5m]))
          ) < 0.95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "多语言生成成功率过低"
          description: "过去5分钟多语言生成成功率: {{ $value | humanizePercentage }}"

      # 格式转换错误率
      - alert: HighFormatConversionErrorRate
        expr: |
          (
            sum(rate(format_conversion_requests_total{success="false"}[5m])) /
            sum(rate(format_conversion_requests_total[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "格式转换错误率过高"
          description: "过去5分钟格式转换错误率: {{ $value | humanizePercentage }}"

      # 缓存命中率过低
      - alert: LowCacheHitRate
        expr: multilang_cache_hit_rate < 0.8
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "多语言缓存命中率过低"
          description: "缓存命中率: {{ $value | humanizePercentage }}"
```

---

## 9. 总结

### 9.1 架构亮点

1. **多语言Prompt系统**：支持10种语言的AI生成模板
2. **混合存储策略**：简单字段使用VARCHAR，复杂结构使用JSONB
3. **向后兼容设计**：100%兼容现有数据和API
4. **自动格式转换**：无缝处理新旧数据格式
5. **性能优化**：JSONB索引 + 多层缓存 + 预生成机制

### 9.2 技术创新

- **数据模型演进**：从单一格式到多格式兼容
- **Prompt版本管理**：支持多版本Prompt模板
- **智能格式检测**：自动选择最优数据格式
- **渐进式迁移**：零停机时间的数据升级
- **多语言缓存**：按语言优化的缓存策略

### 9.3 业务价值

- **用户体验提升**：多语言支持覆盖全球用户
- **内容质量保证**：结构化AI生成更高质量
- **运营成本降低**：缓存和预生成减少API调用
- **可扩展性增强**：支持更多语言和格式
- **风险控制**：向后兼容确保稳定性

### 9.4 后续规划

1. **Phase 1（已完成）**：多语言Prompt系统基础架构
2. **Phase 2（进行中）**：批量数据迁移和性能优化
3. **Phase 3（计划中）**：智能语言检测和自动翻译
4. **Phase 4（未来）**：个性化学习路径和自适应Prompt

---

**文档结束**

**版本**：v2.0
**日期**：2025-10-26
**状态**：待评审
**作者**：架构师

---

**变更日志**：
- v2.0 (2025-10-26): 新增多语言Prompt系统完整设计
- v1.1 (2025-10-16): 新增游客模式技术设计
- v1.0 (2025-10-16): 初始版本