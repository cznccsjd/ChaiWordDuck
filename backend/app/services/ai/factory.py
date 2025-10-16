"""AI服务工厂（支持主备切换）"""
from typing import Optional
from app.services.ai.base import AIServiceBase, AIServiceError
from app.services.ai.openai_service import OpenAIService
from app.services.ai.gemini_service import GeminiService
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIServiceFactory:
    """AI服务工厂（单例模式，支持主备切换）"""

    _instance: Optional[AIServiceBase] = None
    _current_provider: Optional[str] = None

    @classmethod
    def get_service(cls) -> AIServiceBase:
        """
        获取AI服务实例（主备切换逻辑）

        Returns:
            AIServiceBase: AI服务实例

        Raises:
            AIServiceError: 主备服务都失败时抛出
        """
        settings = get_settings()

        # 如果已有实例，直接返回
        if cls._instance is not None:
            return cls._instance

        # 尝试初始化主服务
        primary_provider = settings.ai_primary_provider
        logger.info(f"Attempting to initialize primary AI provider: {primary_provider}")

        try:
            cls._instance = cls._create_provider(primary_provider, settings)
            cls._current_provider = primary_provider
            logger.info(f"✅ Primary AI provider initialized: {primary_provider}")
            return cls._instance
        except Exception as e:
            logger.warning(
                f"⚠️ Primary provider ({primary_provider}) failed: {e}. " f"Attempting fallback..."
            )

        # 主服务失败，尝试备用服务
        fallback_provider = settings.ai_fallback_provider
        logger.info(f"Attempting to initialize fallback AI provider: {fallback_provider}")

        try:
            cls._instance = cls._create_provider(fallback_provider, settings)
            cls._current_provider = fallback_provider
            logger.warning(f"⚠️ Using fallback AI provider: {fallback_provider}")
            return cls._instance
        except Exception as e:
            logger.error(f"❌ Fallback provider ({fallback_provider}) also failed: {e}")
            raise AIServiceError(
                f"Both primary ({primary_provider}) and fallback ({fallback_provider}) "
                f"AI providers failed to initialize. Please check configuration."
            )

    @classmethod
    def _create_provider(cls, provider: str, settings) -> AIServiceBase:
        """
        创建指定的AI服务提供商

        Args:
            provider: 提供商名称（gemini/openai）
            settings: 配置对象

        Returns:
            AIServiceBase: AI服务实例

        Raises:
            ValueError: 不支持的提供商
            AIServiceError: 初始化失败
        """
        if provider == "gemini":
            return GeminiService(
                api_key=settings.gemini_api_key, model=settings.gemini_model, timeout=settings.gemini_timeout
            )
        elif provider == "openai":
            return OpenAIService(
                api_key=settings.openai_api_key, model=settings.openai_model, timeout=settings.openai_timeout
            )
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

    @classmethod
    def reset_instance(cls):
        """重置实例（用于测试或强制重新初始化）"""
        cls._instance = None
        cls._current_provider = None
        logger.info("AI service instance reset")

    @classmethod
    def get_current_provider(cls) -> Optional[str]:
        """获取当前使用的提供商名称"""
        return cls._current_provider
