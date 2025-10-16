"""AI服务工厂"""
from typing import Optional
from app.services.ai.base import AIServiceBase
from app.services.ai.openai_service import OpenAIService
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIServiceFactory:
    """AI服务工厂（单例模式）"""

    _instance: Optional[AIServiceBase] = None

    @classmethod
    def get_service(cls) -> AIServiceBase:
        """获取AI服务实例"""
        if cls._instance is None:
            settings = get_settings()

            if settings.AI_PROVIDER == "openai":
                logger.info("Initializing OpenAI service")
                cls._instance = OpenAIService(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL,
                    timeout=settings.OPENAI_TIMEOUT
                )
            else:
                raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")

        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置实例（用于测试）"""
        cls._instance = None
