# AI服务架构设计文档

## 文档信息

| 属性 | 内容 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2025-10-16 |
| 作者 | 架构师 |
| 审批状态 | 待评审 |
| 相关功能 | AI生成单词手册 |

---

## 1. 架构概述

### 1.1 设计目标

**核心需求**：
1. 支持多AI提供商（OpenAI、Gemini、Claude等）
2. 统一的服务接口，降低业务层与AI提供商的耦合
3. 自动降级和容错机制
4. 并发请求防重复生成
5. 成本和性能监控

**2025年技术标准**：
- 使用抽象基类（ABC）定义服务接口
- 异步I/O（async/await）
- 结构化日志和监控
- 分布式锁（Redis）
- 防雪崩机制（超时、重试、熔断）

### 1.2 系统架构图

```
┌──────────────────────────────────────────────────────────────┐
│                      业务层 (API Routes)                      │
│                                                               │
│  /api/v1/words/query/{word}                                  │
│  ↓                                                            │
│  1. 检查数据库（单词是否已存在）                                │
│  2. 检查用户限额（游客5次/天 AI生成）⭐ 新增                   │
│  3. 调用 AI服务生成单词手册                                    │
│  4. 存储到数据库                                               │
│  5. 返回给用户                                                │
└──────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────┐
│                    AI服务抽象层                                │
│                                                               │
│  ┌─────────────────────────────────────────────────┐         │
│  │         BaseAIService (抽象基类)                  │         │
│  │                                                   │         │
│  │  + generate_word_handbook(word: str) -> dict    │         │
│  │  + check_availability() -> bool                  │         │
│  │  + get_provider_name() -> str                    │         │
│  │  + get_estimated_cost(word: str) -> float        │         │
│  └─────────────────────────────────────────────────┘         │
│                        ↑                                      │
│           ┌────────────┼────────────┐                        │
│           │            │            │                        │
│  ┌────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  OpenAI    │ │   Gemini    │ │   Claude    │            │
│  │  Service   │ │   Service   │ │   Service   │            │
│  └────────────┘ └─────────────┘ └─────────────┘            │
│                                                               │
│  ┌─────────────────────────────────────────────────┐         │
│  │      AIServiceFactory (工厂类)                    │         │
│  │                                                   │         │
│  │  + create_primary() -> BaseAIService             │         │
│  │  + create_fallback() -> BaseAIService            │         │
│  │  + get_available_providers() -> List[str]        │         │
│  └─────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────┐
│                   并发控制层 (Redis)                           │
│                                                               │
│  分布式锁：ai_generation:lock:{word}                          │
│  生成状态：ai_generation:status:{word}                        │
│  AI生成计数：ai_generation:count:{user_or_guest}:{date}       │
└──────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────┐
│                   外部AI API                                   │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  OpenAI API  │  │  Gemini API  │  │ Claude API   │      │
│  │  gpt-4o-mini │  │ gemini-1.5   │  │ claude-3.5   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. AI服务接口设计

### 2.1 抽象基类（BaseAIService）

**核心职责**：
1. 定义统一的AI服务接口
2. 提供通用的错误处理逻辑
3. 实现重试和超时机制
4. 日志和监控埋点

**接口定义**：

```python
# app/services/ai/base.py

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from pydantic import BaseModel
import asyncio
from app.core.logging import get_logger

logger = get_logger(__name__)


class WordHandbook(BaseModel):
    """单词手册数据结构"""
    word: str
    phonetic: str
    part_of_speech: str
    core_game: str
    scenario_formal: str
    scenario_casual: str
    etymology_breakdown: str
    etymology_story: Optional[str] = None
    common_mistakes: str
    memory_trick: str


class AIGenerationError(Exception):
    """AI生成失败异常"""
    def __init__(self, message: str, provider: str, cause: Optional[Exception] = None):
        self.message = message
        self.provider = provider
        self.cause = cause
        super().__init__(self.message)


class BaseAIService(ABC):
    """
    AI服务抽象基类

    所有AI提供商的服务实现都必须继承此类
    """

    def __init__(self, timeout: int = 30, max_retries: int = 2):
        """
        初始化AI服务

        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        获取提供商名称

        Returns:
            str: 提供商名称（如 "openai", "gemini", "claude"）
        """
        pass

    @abstractmethod
    async def _generate_raw(self, word: str) -> Dict[str, Any]:
        """
        调用AI API生成原始响应（子类实现）

        Args:
            word: 要生成手册的单词

        Returns:
            Dict: AI API的原始响应

        Raises:
            AIGenerationError: AI生成失败
        """
        pass

    @abstractmethod
    def _parse_response(self, raw_response: Dict[str, Any], word: str) -> WordHandbook:
        """
        解析AI响应为WordHandbook格式（子类实现）

        Args:
            raw_response: AI API的原始响应
            word: 单词

        Returns:
            WordHandbook: 解析后的单词手册

        Raises:
            ValueError: 响应格式不正确
        """
        pass

    async def generate_word_handbook(self, word: str) -> WordHandbook:
        """
        生成单词手册（带重试和超时机制）

        Args:
            word: 要生成手册的单词

        Returns:
            WordHandbook: 生成的单词手册

        Raises:
            AIGenerationError: 生成失败（多次重试后）
        """
        provider = self.get_provider_name()

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"[{provider}] 开始生成单词手册",
                    extra={
                        "word": word,
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries + 1,
                        "provider": provider,
                    }
                )

                # 使用asyncio.wait_for实现超时
                raw_response = await asyncio.wait_for(
                    self._generate_raw(word),
                    timeout=self.timeout
                )

                # 解析响应
                handbook = self._parse_response(raw_response, word)

                logger.info(
                    f"[{provider}] 单词手册生成成功",
                    extra={
                        "word": word,
                        "provider": provider,
                        "attempt": attempt + 1,
                    }
                )

                return handbook

            except asyncio.TimeoutError:
                logger.warning(
                    f"[{provider}] 生成超时（{self.timeout}秒）",
                    extra={
                        "word": word,
                        "attempt": attempt + 1,
                        "timeout": self.timeout,
                        "provider": provider,
                    }
                )
                if attempt == self.max_retries:
                    raise AIGenerationError(
                        f"AI生成超时（{self.timeout}秒），已重试{self.max_retries}次",
                        provider
                    )
                await asyncio.sleep(2 ** attempt)  # 指数退避

            except AIGenerationError:
                raise  # 直接抛出AI生成错误

            except Exception as e:
                logger.error(
                    f"[{provider}] 生成失败",
                    extra={
                        "word": word,
                        "attempt": attempt + 1,
                        "error": str(e),
                        "provider": provider,
                    },
                    exc_info=True
                )
                if attempt == self.max_retries:
                    raise AIGenerationError(
                        f"AI生成失败：{str(e)}",
                        provider,
                        cause=e
                    )
                await asyncio.sleep(2 ** attempt)

    @abstractmethod
    async def check_availability(self) -> bool:
        """
        检查AI服务是否可用

        Returns:
            bool: True表示可用，False表示不可用
        """
        pass

    @abstractmethod
    def get_estimated_cost(self, word: str) -> float:
        """
        估算生成成本（美元）

        Args:
            word: 单词

        Returns:
            float: 估算成本（美元）
        """
        pass

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词（通用部分，可被子类覆盖）

        Returns:
            str: 系统提示词
        """
        return """你是拆词鸭的AI助手，专门帮助成人学习英语长单词。

你的任务是为给定的单词生成一份"单词手册"，包含以下内容：

1. **核心游戏**（core_game）: 用一句话概括单词的核心含义，像给单词起个外号。
2. **思辨场景**（scenario_formal）: 描述这个单词在正式场合（学术、商业）的典型使用场景。
3. **生活场景**（scenario_casual）: 描述这个单词在日常生活中的使用场景。
4. **词根拆解**（etymology_breakdown）: 拆解单词的词根、前缀、后缀，解释构词逻辑。
5. **词源故事**（etymology_story）: 简短讲述单词的历史来源和演变故事。
6. **犯规警告**（common_mistakes）: 列出常见的拼写、发音或用法错误。
7. **通关秘籍**（memory_trick）: 提供一个有趣的记忆技巧或联想方法。

要求：
- 语言风格：幽默、轻松、接地气（像朋友聊天）
- 避免枯燥的学术语言
- 每个部分控制在50-100字
- 确保内容准确且易于理解

请以JSON格式返回，格式如下：
{
  "core_game": "...",
  "scenario_formal": "...",
  "scenario_casual": "...",
  "etymology_breakdown": "...",
  "etymology_story": "...",
  "common_mistakes": "...",
  "memory_trick": "..."
}
"""
```

### 2.2 OpenAI服务实现

```python
# app/services/ai/openai_service.py

from typing import Dict, Any, Optional
import json
from openai import AsyncOpenAI
from app.services.ai.base import BaseAIService, WordHandbook, AIGenerationError
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIService(BaseAIService):
    """
    OpenAI服务实现

    使用gpt-4o-mini模型生成单词手册
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        timeout: int = 30,
        max_retries: int = 2,
    ):
        """
        初始化OpenAI服务

        Args:
            api_key: OpenAI API密钥（如果不提供则从settings读取）
            model: 使用的模型名称
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        super().__init__(timeout, max_retries)
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model

        if not self.api_key:
            raise ValueError("OpenAI API Key未配置")

        self.client = AsyncOpenAI(api_key=self.api_key)

    def get_provider_name(self) -> str:
        return "openai"

    async def _generate_raw(self, word: str) -> Dict[str, Any]:
        """
        调用OpenAI API生成原始响应

        Args:
            word: 单词

        Returns:
            Dict: OpenAI API响应

        Raises:
            AIGenerationError: API调用失败
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": f"请为单词 '{word}' 生成单词手册。"},
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"},  # 强制JSON响应
            )

            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            }

        except Exception as e:
            logger.error(
                f"OpenAI API调用失败: {str(e)}",
                extra={"word": word, "model": self.model},
                exc_info=True
            )
            raise AIGenerationError(f"OpenAI API调用失败: {str(e)}", "openai", e)

    def _parse_response(self, raw_response: Dict[str, Any], word: str) -> WordHandbook:
        """
        解析OpenAI响应

        Args:
            raw_response: OpenAI API响应
            word: 单词

        Returns:
            WordHandbook: 解析后的单词手册

        Raises:
            ValueError: 响应格式错误
        """
        try:
            content = raw_response["content"]
            data = json.loads(content)

            return WordHandbook(
                word=word,
                phonetic=data.get("phonetic", ""),
                part_of_speech=data.get("part_of_speech", ""),
                core_game=data["core_game"],
                scenario_formal=data["scenario_formal"],
                scenario_casual=data["scenario_casual"],
                etymology_breakdown=data["etymology_breakdown"],
                etymology_story=data.get("etymology_story"),
                common_mistakes=data["common_mistakes"],
                memory_trick=data["memory_trick"],
            )
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(
                f"OpenAI响应解析失败: {str(e)}",
                extra={"word": word, "response": raw_response},
                exc_info=True
            )
            raise ValueError(f"OpenAI响应格式错误: {str(e)}")

    async def check_availability(self) -> bool:
        """
        检查OpenAI服务是否可用（通过简单的API调用测试）

        Returns:
            bool: True表示可用
        """
        try:
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return True
        except Exception as e:
            logger.warning(f"OpenAI服务不可用: {str(e)}")
            return False

    def get_estimated_cost(self, word: str) -> float:
        """
        估算生成成本

        gpt-4o-mini 价格（2025年）:
        - Input: $0.15 / 1M tokens
        - Output: $0.60 / 1M tokens

        估算：
        - 输入约 300 tokens（系统提示词 + 用户输入）
        - 输出约 600 tokens（单词手册）

        Returns:
            float: 估算成本（美元）
        """
        input_tokens = 300
        output_tokens = 600

        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60

        return input_cost + output_cost  # 约 $0.00041/次
```

### 2.3 Gemini服务实现

```python
# app/services/ai/gemini_service.py

from typing import Dict, Any, Optional
import json
import google.generativeai as genai
from app.services.ai.base import BaseAIService, WordHandbook, AIGenerationError
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiService(BaseAIService):
    """
    Google Gemini服务实现

    使用gemini-1.5-flash模型生成单词手册
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        timeout: int = 30,
        max_retries: int = 2,
    ):
        """
        初始化Gemini服务

        Args:
            api_key: Gemini API密钥（如果不提供则从settings读取）
            model: 使用的模型名称
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        super().__init__(timeout, max_retries)
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model or settings.gemini_model

        if not self.api_key:
            raise ValueError("Gemini API Key未配置")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1000,
                "response_mime_type": "application/json",  # 强制JSON响应
            }
        )

    def get_provider_name(self) -> str:
        return "gemini"

    async def _generate_raw(self, word: str) -> Dict[str, Any]:
        """
        调用Gemini API生成原始响应

        Args:
            word: 单词

        Returns:
            Dict: Gemini API响应

        Raises:
            AIGenerationError: API调用失败
        """
        try:
            prompt = f"{self._build_system_prompt()}\n\n请为单词 '{word}' 生成单词手册。"

            response = await self.model.generate_content_async(prompt)

            return {
                "content": response.text,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }
            }

        except Exception as e:
            logger.error(
                f"Gemini API调用失败: {str(e)}",
                extra={"word": word, "model": self.model_name},
                exc_info=True
            )
            raise AIGenerationError(f"Gemini API调用失败: {str(e)}", "gemini", e)

    def _parse_response(self, raw_response: Dict[str, Any], word: str) -> WordHandbook:
        """
        解析Gemini响应（与OpenAI相同的JSON格式）

        Args:
            raw_response: Gemini API响应
            word: 单词

        Returns:
            WordHandbook: 解析后的单词手册

        Raises:
            ValueError: 响应格式错误
        """
        try:
            content = raw_response["content"]
            data = json.loads(content)

            return WordHandbook(
                word=word,
                phonetic=data.get("phonetic", ""),
                part_of_speech=data.get("part_of_speech", ""),
                core_game=data["core_game"],
                scenario_formal=data["scenario_formal"],
                scenario_casual=data["scenario_casual"],
                etymology_breakdown=data["etymology_breakdown"],
                etymology_story=data.get("etymology_story"),
                common_mistakes=data["common_mistakes"],
                memory_trick=data["memory_trick"],
            )
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(
                f"Gemini响应解析失败: {str(e)}",
                extra={"word": word, "response": raw_response},
                exc_info=True
            )
            raise ValueError(f"Gemini响应格式错误: {str(e)}")

    async def check_availability(self) -> bool:
        """
        检查Gemini服务是否可用

        Returns:
            bool: True表示可用
        """
        try:
            await self.model.generate_content_async("test")
            return True
        except Exception as e:
            logger.warning(f"Gemini服务不可用: {str(e)}")
            return False

    def get_estimated_cost(self, word: str) -> float:
        """
        估算生成成本

        gemini-1.5-flash 价格（2025年）:
        - Input: $0.075 / 1M tokens（0-128K context）
        - Output: $0.30 / 1M tokens

        估算：
        - 输入约 300 tokens
        - 输出约 600 tokens

        Returns:
            float: 估算成本（美元）
        """
        input_tokens = 300
        output_tokens = 600

        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.30

        return input_cost + output_cost  # 约 $0.0002025/次（比OpenAI便宜约50%）
```

---

## 3. AI服务工厂和管理

### 3.1 服务工厂

```python
# app/services/ai/factory.py

from typing import Optional, List, Dict
from enum import Enum
from app.services.ai.base import BaseAIService
from app.services.ai.openai_service import OpenAIService
from app.services.ai.gemini_service import GeminiService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIProvider(str, Enum):
    """AI提供商枚举"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"  # 待实现


class AIServiceFactory:
    """
    AI服务工厂

    职责：
    1. 根据配置创建AI服务实例
    2. 管理多提供商的优先级
    3. 提供降级策略
    """

    _instances: Dict[str, BaseAIService] = {}  # 单例缓存

    @classmethod
    def create_service(
        cls,
        provider: AIProvider,
        timeout: int = 30,
        max_retries: int = 2,
    ) -> BaseAIService:
        """
        创建AI服务实例（单例模式）

        Args:
            provider: AI提供商
            timeout: 超时时间
            max_retries: 最大重试次数

        Returns:
            BaseAIService: AI服务实例

        Raises:
            ValueError: 不支持的提供商或配置缺失
        """
        cache_key = f"{provider.value}_{timeout}_{max_retries}"

        if cache_key in cls._instances:
            return cls._instances[cache_key]

        if provider == AIProvider.OPENAI:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API Key未配置")
            service = OpenAIService(timeout=timeout, max_retries=max_retries)

        elif provider == AIProvider.GEMINI:
            if not settings.gemini_api_key:
                raise ValueError("Gemini API Key未配置")
            service = GeminiService(timeout=timeout, max_retries=max_retries)

        elif provider == AIProvider.CLAUDE:
            raise NotImplementedError("Claude服务尚未实现")

        else:
            raise ValueError(f"不支持的AI提供商: {provider}")

        cls._instances[cache_key] = service
        return service

    @classmethod
    def get_primary_service(cls) -> BaseAIService:
        """
        获取主要AI服务

        优先级从配置读取（settings.ai_primary_provider）

        Returns:
            BaseAIService: 主要AI服务
        """
        provider = AIProvider(settings.ai_primary_provider)
        return cls.create_service(provider)

    @classmethod
    def get_fallback_service(cls) -> Optional[BaseAIService]:
        """
        获取备用AI服务

        从配置读取（settings.ai_fallback_provider）

        Returns:
            Optional[BaseAIService]: 备用AI服务，如果未配置则返回None
        """
        if not settings.ai_fallback_provider:
            return None

        try:
            provider = AIProvider(settings.ai_fallback_provider)
            return cls.create_service(provider)
        except (ValueError, NotImplementedError) as e:
            logger.warning(f"备用AI服务创建失败: {str(e)}")
            return None

    @classmethod
    async def get_available_providers(cls) -> List[str]:
        """
        获取当前可用的AI提供商列表

        Returns:
            List[str]: 可用的提供商名称列表
        """
        available = []

        for provider in AIProvider:
            try:
                service = cls.create_service(provider)
                if await service.check_availability():
                    available.append(provider.value)
            except (ValueError, NotImplementedError):
                continue

        return available
```

### 3.2 AI服务管理器（带降级和并发控制）

```python
# app/services/ai/manager.py

from typing import Optional, Dict
import asyncio
from redis.asyncio import Redis
from app.services.ai.base import BaseAIService, WordHandbook, AIGenerationError
from app.services.ai.factory import AIServiceFactory
from app.core.logging import get_logger
from app.core.redis_keys import RedisKeys

logger = get_logger(__name__)


class AIGenerationManager:
    """
    AI生成管理器

    职责：
    1. 统一管理AI生成流程
    2. 实现降级策略（主服务失败时切换到备用服务）
    3. 防止并发重复生成（分布式锁）
    4. 监控和日志记录
    """

    def __init__(self, redis: Redis):
        """
        初始化AI生成管理器

        Args:
            redis: Redis客户端
        """
        self.redis = redis
        self.primary_service = AIServiceFactory.get_primary_service()
        self.fallback_service = AIServiceFactory.get_fallback_service()

    async def generate_word_handbook(
        self,
        word: str,
        enable_fallback: bool = True,
    ) -> WordHandbook:
        """
        生成单词手册（带降级和并发控制）

        Args:
            word: 单词
            enable_fallback: 是否启用降级（主服务失败时切换到备用服务）

        Returns:
            WordHandbook: 生成的单词手册

        Raises:
            AIGenerationError: 所有服务都失败
            ValueError: 单词格式不正确
        """
        # 标准化单词
        normalized_word = word.strip().lower()

        if not normalized_word:
            raise ValueError("单词不能为空")

        # 获取分布式锁（防止并发重复生成）
        lock_key = RedisKeys.get_ai_generation_lock(normalized_word)

        async with self._distributed_lock(lock_key, timeout=60):
            logger.info(
                f"开始生成单词手册: {normalized_word}",
                extra={"word": normalized_word}
            )

            # 尝试主服务
            try:
                handbook = await self.primary_service.generate_word_handbook(normalized_word)
                logger.info(
                    f"主服务生成成功: {normalized_word}",
                    extra={
                        "word": normalized_word,
                        "provider": self.primary_service.get_provider_name(),
                    }
                )
                return handbook

            except AIGenerationError as e:
                logger.warning(
                    f"主服务生成失败: {normalized_word}",
                    extra={
                        "word": normalized_word,
                        "provider": self.primary_service.get_provider_name(),
                        "error": str(e),
                    }
                )

                # 如果启用降级且有备用服务，尝试备用服务
                if enable_fallback and self.fallback_service:
                    try:
                        logger.info(
                            f"尝试备用服务: {normalized_word}",
                            extra={
                                "word": normalized_word,
                                "fallback_provider": self.fallback_service.get_provider_name(),
                            }
                        )
                        handbook = await self.fallback_service.generate_word_handbook(normalized_word)
                        logger.info(
                            f"备用服务生成成功: {normalized_word}",
                            extra={
                                "word": normalized_word,
                                "provider": self.fallback_service.get_provider_name(),
                            }
                        )
                        return handbook

                    except AIGenerationError as fallback_error:
                        logger.error(
                            f"备用服务也失败: {normalized_word}",
                            extra={
                                "word": normalized_word,
                                "primary_error": str(e),
                                "fallback_error": str(fallback_error),
                            }
                        )
                        raise AIGenerationError(
                            f"所有AI服务都失败（主服务: {e.message}, 备用服务: {fallback_error.message}）",
                            "all"
                        )
                else:
                    raise  # 没有备用服务，直接抛出主服务错误

    async def _distributed_lock(self, lock_key: str, timeout: int = 60):
        """
        分布式锁上下文管理器（防止并发重复生成）

        Args:
            lock_key: 锁的键
            timeout: 锁的超时时间（秒）

        Yields:
            None
        """
        lock_acquired = False
        lock_value = f"lock_{asyncio.current_task().get_name()}"

        try:
            # 尝试获取锁（SET NX EX）
            for attempt in range(10):  # 最多等待10秒
                lock_acquired = await self.redis.set(
                    lock_key,
                    lock_value,
                    nx=True,  # Only set if not exists
                    ex=timeout,  # Expire after timeout seconds
                )

                if lock_acquired:
                    logger.debug(f"获取锁成功: {lock_key}")
                    break

                # 锁被占用，等待1秒后重试
                logger.debug(f"锁被占用，等待重试: {lock_key}")
                await asyncio.sleep(1)

            if not lock_acquired:
                raise TimeoutError(f"获取分布式锁超时: {lock_key}")

            yield

        finally:
            # 释放锁（只释放自己持有的锁）
            if lock_acquired:
                current_value = await self.redis.get(lock_key)
                if current_value == lock_value:
                    await self.redis.delete(lock_key)
                    logger.debug(f"释放锁成功: {lock_key}")

    async def get_service_status(self) -> Dict[str, bool]:
        """
        获取所有AI服务的健康状态

        Returns:
            Dict[str, bool]: 服务名称 -> 是否可用
        """
        status = {}

        # 检查主服务
        try:
            status[self.primary_service.get_provider_name()] = await self.primary_service.check_availability()
        except Exception as e:
            logger.warning(f"主服务健康检查失败: {str(e)}")
            status[self.primary_service.get_provider_name()] = False

        # 检查备用服务
        if self.fallback_service:
            try:
                status[self.fallback_service.get_provider_name()] = await self.fallback_service.check_availability()
            except Exception as e:
                logger.warning(f"备用服务健康检查失败: {str(e)}")
                status[self.fallback_service.get_provider_name()] = False

        return status
```

---

## 4. 配置管理

### 4.1 配置项扩展

```python
# app/core/config.py（新增配置项）

class Settings(BaseSettings):
    """应用配置类"""

    # ... 现有配置 ...

    # ===== AI服务配置 =====

    # 主AI提供商（openai | gemini | claude）
    ai_primary_provider: str = Field(
        default="gemini",
        description="主AI提供商"
    )

    # 备用AI提供商（可选，用于降级）
    ai_fallback_provider: Optional[str] = Field(
        default="openai",
        description="备用AI提供商（主服务失败时使用）"
    )

    # OpenAI配置（保留现有）
    openai_api_key: str = Field(default="", description="OpenAI API密钥")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI模型")
    openai_timeout: int = Field(default=30, description="OpenAI请求超时(秒)")

    # Gemini配置（新增）
    gemini_api_key: str = Field(default="", description="Google Gemini API密钥")
    gemini_model: str = Field(default="gemini-1.5-flash", description="Gemini模型")
    gemini_timeout: int = Field(default=30, description="Gemini请求超时(秒)")

    # Claude配置（预留）
    claude_api_key: str = Field(default="", description="Anthropic Claude API密钥")
    claude_model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude模型")
    claude_timeout: int = Field(default=30, description="Claude请求超时(秒)")

    # AI生成限额（游客和注册用户）
    guest_ai_generation_limit: int = Field(
        default=5,
        description="游客每日AI生成限额"
    )
    free_user_ai_generation_limit: int = Field(
        default=20,
        description="免费用户每日AI生成限额"
    )
    premium_user_ai_generation_limit: int = Field(
        default=-1,
        description="高级用户每日AI生成限额（-1=无限）"
    )

    # AI生成超时配置
    ai_generation_timeout: int = Field(
        default=60,
        description="AI生成超时时间（秒）"
    )
    ai_generation_max_retries: int = Field(
        default=2,
        description="AI生成最大重试次数"
    )
```

### 4.2 环境变量配置示例

```bash
# .env.example（新增部分）

# ===== AI服务配置 =====

# 主AI提供商（openai | gemini | claude）
AI_PRIMARY_PROVIDER=gemini

# 备用AI提供商（可选）
AI_FALLBACK_PROVIDER=openai

# OpenAI配置
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30

# Gemini配置
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TIMEOUT=30

# Claude配置（预留）
# CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
# CLAUDE_MODEL=claude-3-5-sonnet-20241022
# CLAUDE_TIMEOUT=30

# AI生成限额
GUEST_AI_GENERATION_LIMIT=5
FREE_USER_AI_GENERATION_LIMIT=20
PREMIUM_USER_AI_GENERATION_LIMIT=-1

# AI生成超时和重试
AI_GENERATION_TIMEOUT=60
AI_GENERATION_MAX_RETRIES=2
```

---

## 5. Redis键设计（并发控制）

```python
# app/core/redis_keys.py（新增AI相关键）

class RedisKeys:
    """Redis键命名规范"""

    # ... 现有键 ...

    # ===== AI生成相关 =====

    # AI生成分布式锁
    AI_GENERATION_LOCK = "ai_generation:lock:{word}"  # TTL: 60s

    # AI生成状态（存储生成中的单词列表）
    AI_GENERATION_STATUS = "ai_generation:status:{word}"  # TTL: 60s

    # 游客AI生成计数
    GUEST_AI_GENERATION_COUNT = "ai_generation:count:guest:{guest_id}:{date}"  # TTL: 24h

    # 用户AI生成计数
    USER_AI_GENERATION_COUNT = "ai_generation:count:user:{user_id}:{date}"  # TTL: 24h

    @classmethod
    def get_ai_generation_lock(cls, word: str) -> str:
        """获取AI生成锁的键"""
        return cls.AI_GENERATION_LOCK.format(word=word.lower())

    @classmethod
    def get_guest_ai_generation_count_key(cls, guest_id: str, date: str) -> str:
        """获取游客AI生成计数键"""
        return cls.GUEST_AI_GENERATION_COUNT.format(guest_id=guest_id, date=date)

    @classmethod
    def get_user_ai_generation_count_key(cls, user_id: int, date: str) -> str:
        """获取用户AI生成计数键"""
        return cls.USER_AI_GENERATION_COUNT.format(user_id=user_id, date=date)
```

---

## 6. API集成示例

### 6.1 单词查询API（集成AI生成）

```python
# app/api/v1/words.py（修改query_word_internal函数）

from app.services.ai.manager import AIGenerationManager
from app.services.ai.base import WordHandbook, AIGenerationError
from app.core.redis_keys import RedisKeys

async def query_word_internal(
    word_text: str,
    current_user: Optional[User],
    db: AsyncSession,
    request: Optional[Request] = None,
    redis: Optional[Redis] = None,  # 新增Redis依赖
) -> WordQueryResponse:
    """
    单词查询内部逻辑（增强：支持AI生成）

    流程：
    1. 检查数据库（单词是否已存在）
    2. 如果不存在，检查AI生成限额
    3. 调用AI生成服务
    4. 存储到数据库
    5. 返回结果
    """
    # 标准化单词
    normalized_word = word_text.strip().lower()

    # ... 验证逻辑（省略）...

    # 查询单词
    result = await db.execute(
        select(Word)
        .where(Word.word == normalized_word)
        .order_by(Word.is_golden.desc())
    )
    word = result.scalar_one_or_none()

    # 如果单词不存在，尝试AI生成
    if not word:
        logger.info(
            f"单词不存在，尝试AI生成: {normalized_word}",
            extra={"word": normalized_word}
        )

        # 检查AI生成限额
        await check_ai_generation_limit(current_user, request, redis)

        # 调用AI生成服务
        try:
            ai_manager = AIGenerationManager(redis)
            handbook = await ai_manager.generate_word_handbook(normalized_word)

            # 存储到数据库
            word = Word(
                word=handbook.word,
                phonetic=handbook.phonetic,
                part_of_speech=handbook.part_of_speech,
                core_game=handbook.core_game,
                scenario_formal=handbook.scenario_formal,
                scenario_casual=handbook.scenario_casual,
                etymology_breakdown=handbook.etymology_breakdown,
                etymology_story=handbook.etymology_story,
                common_mistakes=handbook.common_mistakes,
                memory_trick=handbook.memory_trick,
                is_golden=False,
                source="ai",
            )
            db.add(word)
            await db.commit()
            await db.refresh(word)

            logger.info(
                f"AI生成单词手册成功并已存储: {normalized_word}",
                extra={"word": normalized_word, "word_id": word.id}
            )

        except AIGenerationError as e:
            logger.error(
                f"AI生成失败: {normalized_word}",
                extra={"word": normalized_word, "error": str(e)},
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": ErrorCode.AI_GENERATION_FAILED,
                    "message": f"AI生成失败: {e.message}，请稍后重试",
                },
            )

    # ... 后续逻辑（省略）...


async def check_ai_generation_limit(
    current_user: Optional[User],
    request: Optional[Request],
    redis: Redis,
):
    """
    检查AI生成限额

    Args:
        current_user: 当前用户（None表示游客）
        request: 请求对象（游客模式需要）
        redis: Redis客户端

    Raises:
        HTTPException: 429 超出限额
    """
    today = date.today().isoformat()

    if current_user is None:
        # 游客模式
        identifier = GuestIdentifierService.get_identifier(request)
        limit = settings.guest_ai_generation_limit
        count_key = RedisKeys.get_guest_ai_generation_count_key(identifier, today)
    elif current_user.membership_tier == "premium":
        # Premium用户无限制
        return
    else:
        # 免费注册用户
        limit = settings.free_user_ai_generation_limit
        count_key = RedisKeys.get_user_ai_generation_count_key(current_user.id, today)

    # 获取今日已生成次数
    current_count = await redis.get(count_key)
    used = int(current_count) if current_count else 0

    if used >= limit:
        user_type = "游客" if current_user is None else "免费用户"
        logger.warning(
            f"{user_type} AI生成限额已用完: {used}/{limit}",
            extra={"used": used, "limit": limit}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": ErrorCode.AI_GENERATION_LIMIT_EXCEEDED,
                "message": f"今日AI生成次数已用完（{limit}次）。{'注册可获得更多次数' if current_user is None else '升级Premium可无限生成'}！",
            },
        )

    # 递增计数（SET EX）
    await redis.incr(count_key)
    await redis.expire(count_key, 86400)  # 24小时过期

    logger.info(
        f"AI生成计数递增: {used + 1}/{limit}",
        extra={"count_key": count_key, "used": used + 1, "limit": limit}
    )
```

---

## 7. 依赖项和安装

### 7.1 Python依赖（pyproject.toml）

```toml
[project]
dependencies = [
    # ... 现有依赖 ...

    # AI服务依赖
    "openai>=1.0.0",                      # OpenAI官方SDK
    "google-generativeai>=0.3.0",        # Google Gemini SDK
    "anthropic>=0.7.0",                  # Anthropic Claude SDK（预留）
]
```

### 7.2 安装命令

```bash
# 使用PDM安装
pdm add openai
pdm add google-generativeai
pdm add anthropic  # 预留Claude支持
```

---

## 8. 成本和性能对比

### 8.1 AI提供商对比表

| 提供商 | 模型 | 输入价格 | 输出价格 | 估算单次成本 | 平均响应时间 | 可用性 |
|--------|------|----------|----------|-------------|------------|--------|
| **Gemini** | gemini-1.5-flash | $0.075/1M | $0.30/1M | ~$0.0002 | 2-3秒 | 99.5% |
| **OpenAI** | gpt-4o-mini | $0.15/1M | $0.60/1M | ~$0.0004 | 3-5秒 | 99.9% |
| **Claude** | claude-3-5-sonnet | $3.00/1M | $15.00/1M | ~$0.009 | 4-6秒 | 99.7% |

**推荐配置**：
- **主服务**：Gemini（成本最低，速度快）
- **备用服务**：OpenAI（稳定性最高）

**成本估算**（假设每日1000次AI生成）：
- Gemini: $0.20/天 × 30天 = $6/月
- OpenAI: $0.40/天 × 30天 = $12/月
- Claude: $9/天 × 30天 = $270/月

**结论**：Gemini成本比OpenAI低50%，比Claude低95%，适合作为主服务。

### 8.2 性能优化建议

1. **缓存策略**：
   - 已生成的单词缓存到Redis（7天TTL）
   - 避免重复生成

2. **批量生成**：
   - 预生成高频单词（如GRE/TOEFL核心词汇）
   - 后台任务异步生成

3. **并发控制**：
   - 使用Redis分布式锁防止重复生成
   - 限制同时进行的AI请求数量（避免API限流）

4. **降级策略**：
   - 主服务失败自动切换到备用服务
   - 记录失败率，自动调整优先级

---

## 9. 监控和告警

### 9.1 监控指标

```python
# app/services/ai/metrics.py（监控指标收集）

from dataclasses import dataclass
from typing import Dict
from datetime import datetime

@dataclass
class AIGenerationMetrics:
    """AI生成指标"""
    provider: str
    word: str
    success: bool
    duration_ms: int
    cost_usd: float
    error_message: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class AIMetricsCollector:
    """AI指标收集器"""

    async def record_generation(self, metrics: AIGenerationMetrics):
        """记录AI生成指标（发送到Sentry/Datadog/Prometheus）"""
        # TODO: 实现指标上报
        pass
```

### 9.2 告警规则

| 指标 | 阈值 | 告警级别 |
|------|------|---------|
| AI生成失败率 | >10% | Warning |
| AI生成失败率 | >30% | Critical |
| 平均响应时间 | >10秒 | Warning |
| 平均响应时间 | >30秒 | Critical |
| 单日成本 | >$20 | Warning |
| 单日成本 | >$50 | Critical |

---

## 10. 测试策略

### 10.1 单元测试

```python
# tests/unit/test_ai_services.py

import pytest
from app.services.ai.openai_service import OpenAIService
from app.services.ai.gemini_service import GeminiService
from app.services.ai.base import AIGenerationError


@pytest.mark.asyncio
async def test_openai_service_generate():
    """测试OpenAI服务生成单词手册"""
    service = OpenAIService()
    handbook = await service.generate_word_handbook("serendipity")

    assert handbook.word == "serendipity"
    assert handbook.core_game
    assert handbook.etymology_breakdown


@pytest.mark.asyncio
async def test_gemini_service_generate():
    """测试Gemini服务生成单词手册"""
    service = GeminiService()
    handbook = await service.generate_word_handbook("serendipitous")

    assert handbook.word == "serendipitous"
    assert handbook.scenario_formal
    assert handbook.memory_trick


@pytest.mark.asyncio
async def test_fallback_mechanism(monkeypatch):
    """测试降级机制"""
    # Mock主服务失败
    async def mock_generate_error(*args, **kwargs):
        raise AIGenerationError("主服务失败", "openai")

    monkeypatch.setattr(OpenAIService, "generate_word_handbook", mock_generate_error)

    # 应该自动切换到备用服务
    manager = AIGenerationManager(redis=mock_redis)
    handbook = await manager.generate_word_handbook("test")

    assert handbook.word == "test"
```

### 10.2 集成测试

```python
# tests/integration/test_ai_generation.py

@pytest.mark.asyncio
async def test_word_query_with_ai_generation(client, test_db):
    """测试单词查询（新单词自动AI生成）"""
    # 查询不存在的单词
    response = await client.get("/api/v1/words/query/serendipitous")

    assert response.status_code == 200
    data = response.json()

    assert data["data"]["word"] == "serendipitous"
    assert data["data"]["core_game"]

    # 验证数据库中已存储
    word = await test_db.execute(
        select(Word).where(Word.word == "serendipitous")
    )
    assert word.scalar_one_or_none() is not None
```

---

## 11. 部署和运维

### 11.1 Docker环境变量

```dockerfile
# Dockerfile（新增AI服务环境变量）

ENV AI_PRIMARY_PROVIDER=gemini
ENV AI_FALLBACK_PROVIDER=openai

# 生产环境通过Secrets管理API Key
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
```

### 11.2 健康检查端点

```python
# app/api/endpoints/health.py（新增AI服务健康检查）

@router.get("/health/ai", summary="AI服务健康检查")
async def health_check_ai(redis: Redis = Depends(get_redis)):
    """
    检查所有AI服务的健康状态

    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "services": {
                "openai": true,
                "gemini": false
            }
        }
    """
    manager = AIGenerationManager(redis)
    service_status = await manager.get_service_status()

    healthy_count = sum(1 for status in service_status.values() if status)
    total_count = len(service_status)

    if healthy_count == total_count:
        overall_status = "healthy"
    elif healthy_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "services": service_status,
        "timestamp": datetime.utcnow().isoformat(),
    }
```

---

## 12. 未来扩展

### 12.1 Phase 2功能

1. **Claude服务支持**：
   - 实现ClaudeService类
   - 成本较高，可作为Premium用户专属

2. **自定义Prompt模板**：
   - 允许用户选择生成风格（严肃/幽默/简洁）
   - 存储到数据库

3. **批量生成**：
   - 后台任务批量生成高频单词
   - 减少用户等待时间

4. **生成质量评分**：
   - 用户反馈系统
   - 根据评分调整Prompt

### 12.2 技术债务

1. **流式生成**：
   - 使用SSE（Server-Sent Events）流式返回生成内容
   - 提升用户体验

2. **本地模型**：
   - 探索开源模型（如Llama 3、Mistral）
   - 降低成本，提高隐私

---

## 附录

### A. 目录结构

```
backend/app/services/ai/
├── __init__.py
├── base.py                 # 抽象基类
├── openai_service.py       # OpenAI服务实现
├── gemini_service.py       # Gemini服务实现
├── claude_service.py       # Claude服务实现（待开发）
├── factory.py              # 服务工厂
├── manager.py              # 生成管理器
└── metrics.py              # 监控指标
```

### B. 错误码定义

```python
# app/schemas/common.py（新增错误码）

class ErrorCode:
    # ... 现有错误码 ...

    # AI生成相关
    AI_GENERATION_FAILED = "AI_GENERATION_FAILED"
    AI_GENERATION_LIMIT_EXCEEDED = "AI_GENERATION_LIMIT_EXCEEDED"
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
```

---

**文档结束**
