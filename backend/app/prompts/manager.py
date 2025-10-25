"""Prompt管理器 - 配置化驱动的多语言Prompt管理系统"""

import os
import yaml
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from functools import lru_cache

from app.prompts.enums import Language, AIProvider, PromptType
from app.prompts.templates.config import PromptTemplateConfig, LanguageTemplate, ProviderConfig
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptManager:
    """Prompt管理器核心类

    负责加载、缓存和管理多语言、多AI提供商的Prompt模板
    支持配置化驱动的模板管理和降级策略
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """初始化Prompt管理器

        Args:
            templates_dir: 模板文件目录路径，默认为当前包下的templates目录
        """
        self._templates_dir = templates_dir or self._get_default_templates_dir()
        self._config: Optional[PromptTemplateConfig] = None
        self._lock = threading.RLock()
        self._load_config()

    def _get_default_templates_dir(self) -> str:
        """获取默认模板目录路径"""
        current_dir = Path(__file__).parent
        templates_dir = current_dir / "templates"
        return str(templates_dir)

    def _load_config(self) -> None:
        """加载配置文件"""
        with self._lock:
            try:
                config_file = Path(self._templates_dir) / "word_generation.yml"
                if not config_file.exists():
                    raise FileNotFoundError(f"模板配置文件不存在: {config_file}")

                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)

                self._config = PromptTemplateConfig(**config_data)
                logger.info(f"Prompt模板配置加载成功: {config_file}")

            except Exception as e:
                logger.error(f"加载Prompt模板配置失败: {e}")
                # 创建最小可用配置作为降级策略
                self._config = self._create_fallback_config()

    def _create_fallback_config(self) -> PromptTemplateConfig:
        """创建降级配置 - 当主配置加载失败时使用"""
        logger.warning("使用降级Prompt配置")

        fallback_data = {
            "metadata": {
                "version": "1.0.0-fallback",
                "description": "降级配置",
                "last_updated": "2025-01-25"
            },
            "templates": {
                "zh_CN": {
                    "system_prompt": "你是一位专业的英语教学专家。",
                    "user_prompt": "请详细解释单词 {word} 的含义和用法。"
                }
            },
            "providers": {
                "gemini": {
                    "default_temperature": 0.7,
                    "default_max_tokens": 1000,
                    "supports_structured_output": False
                }
            }
        }

        return PromptTemplateConfig(**fallback_data)

    @lru_cache(maxsize=128)
    def get_template(
        self,
        language: str = Language.CHINESE,
        provider: str = AIProvider.GEMINI,
        prompt_type: str = PromptType.WORD_GENERATION
    ) -> Tuple[LanguageTemplate, ProviderConfig]:
        """获取Prompt模板和提供商配置

        Args:
            language: 语言代码，默认中文
            provider: AI提供商，默认Gemini
            prompt_type: Prompt类型，默认单词生成

        Returns:
            Tuple[LanguageTemplate, ProviderConfig]: 模板和配置的元组

        Raises:
            ValueError: 当语言或提供商不支持时
        """
        if not self._config:
            raise RuntimeError("Prompt配置未加载")

        # 验证语言支持
        if not self._config.validate_language_support(language):
            # 尝试降级到中文
            if language != Language.CHINESE and self._config.validate_language_support(Language.CHINESE):
                logger.warning(f"不支持的语言 {language}，降级到中文")
                language = Language.CHINESE
            else:
                raise ValueError(f"不支持的语言: {language}")

        # 验证提供商支持
        if not self._config.validate_provider_support(provider):
            # 尝试降级到Gemini
            if provider != AIProvider.GEMINI and self._config.validate_provider_support(AIProvider.GEMINI):
                logger.warning(f"不支持的提供商 {provider}，降级到Gemini")
                provider = AIProvider.GEMINI
            else:
                raise ValueError(f"不支持的AI提供商: {provider}")

        template = self._config.get_template(language)
        provider_config = self._config.get_provider_config(provider)

        if not template:
            raise ValueError(f"未找到语言模板: {language}")
        if not provider_config:
            raise ValueError(f"未找到提供商配置: {provider}")

        return template, provider_config

    def render_prompt(
        self,
        word: str,
        language: str = Language.CHINESE,
        provider: str = AIProvider.GEMINI,
        prompt_type: str = PromptType.WORD_GENERATION,
        **kwargs
    ) -> Tuple[str, str]:
        """渲染完整的Prompt

        Args:
            word: 目标单词
            language: 语言代码
            provider: AI提供商
            prompt_type: Prompt类型
            **kwargs: 额外的模板变量

        Returns:
            Tuple[str, str]: (system_prompt, user_prompt)
        """
        template, _ = self.get_template(language, provider, prompt_type)

        # 准备模板变量
        template_vars = {"word": word}
        template_vars.update(kwargs)

        # 渲染系统提示词
        system_prompt = template.system_prompt.format(**template_vars)

        # 渲染用户提示词
        try:
            user_prompt = template.user_prompt.format(**template_vars)
        except KeyError as e:
            raise ValueError(f"模板变量缺失: {e}")

        return system_prompt, user_prompt

    def get_provider_config(self, provider: str) -> ProviderConfig:
        """获取AI提供商配置"""
        if not self._config:
            raise RuntimeError("Prompt配置未加载")

        if not self._config.validate_provider_support(provider):
            raise ValueError(f"不支持的AI提供商: {provider}")

        config = self._config.get_provider_config(provider)
        if not config:
            raise ValueError(f"未找到提供商配置: {provider}")

        return config

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        if not self._config:
            return []
        return self._config.get_supported_languages()

    def get_supported_providers(self) -> list[str]:
        """获取支持的提供商列表"""
        if not self._config:
            return []
        return self._config.get_supported_providers()

    def reload_config(self) -> None:
        """重新加载配置文件"""
        logger.info("重新加载Prompt配置...")
        self._load_config()

    def validate_config(self) -> Dict[str, Any]:
        """验证当前配置的有效性

        Returns:
            Dict[str, Any]: 验证结果
        """
        if not self._config:
            return {
                "valid": False,
                "error": "配置未加载"
            }

        try:
            # 测试模板渲染
            system_prompt, user_prompt = self.render_prompt("test")

            # 验证渲染结果
            if not system_prompt or not user_prompt:
                return {
                    "valid": False,
                    "error": "模板渲染失败"
                }

            return {
                "valid": True,
                "languages": self.get_supported_languages(),
                "providers": self.get_supported_providers(),
                "config_version": self._config.metadata.version
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        if not self._config:
            return {"error": "配置未加载"}

        return {
            "metadata": {
                "version": self._config.metadata.version,
                "description": self._config.metadata.description,
                "last_updated": self._config.metadata.last_updated
            },
            "supported_languages": self.get_supported_languages(),
            "supported_providers": self.get_supported_providers()
        }


# 全局单例实例
_prompt_manager: Optional[PromptManager] = None
_manager_lock = threading.Lock()


def get_prompt_manager() -> PromptManager:
    """获取全局Prompt管理器单例"""
    global _prompt_manager

    if _prompt_manager is None:
        with _manager_lock:
            if _prompt_manager is None:
                _prompt_manager = PromptManager()
                logger.info("全局Prompt管理器初始化完成")

    return _prompt_manager