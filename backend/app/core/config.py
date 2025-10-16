"""
应用配置模块

使用pydantic-settings管理环境变量配置
"""
from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用配置
    app_name: str = Field(default="ChaiWord Duck API", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    app_env: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=True, description="调试模式")

    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")

    # 数据库配置
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/chaiword_duck",
        description="数据库连接URL",
    )
    database_pool_size: int = Field(default=20, description="数据库连接池大小")
    database_max_overflow: int = Field(default=10, description="数据库连接池最大溢出")
    database_echo: bool = Field(default=False, description="是否打印SQL语句")

    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    redis_password: str = Field(default="", description="Redis密码")

    # JWT配置
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        description="JWT密钥",
        min_length=32,
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_access_token_expire_minutes: int = Field(default=10080, description="JWT过期时间(分钟)")

    # 密码加密配置
    password_bcrypt_rounds: int = Field(default=12, description="bcrypt加密轮数")

    # 限流配置
    rate_limit_per_minute: int = Field(default=30, description="每分钟请求限制")
    rate_limit_per_hour: int = Field(default=1000, description="每小时请求限制")

    # OpenAI配置
    openai_api_key: str = Field(default="", description="OpenAI API密钥")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI模型")
    openai_temperature: float = Field(default=0.7, description="OpenAI温度参数")
    openai_max_tokens: int = Field(default=1000, description="OpenAI最大token数")
    openai_timeout: int = Field(default=10, description="OpenAI请求超时(秒)")

    # 邮件配置
    sendgrid_api_key: str = Field(default="", description="SendGrid API密钥")
    from_email: str = Field(default="noreply@chaiwordduck.com", description="发件人邮箱")
    from_name: str = Field(default="拆词鸭", description="发件人名称")

    # CORS配置
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        description="允许的跨域源（逗号分隔）",
    )
    cors_allow_credentials: bool = Field(default=True, description="允许携带凭证")

    # 查询限制
    guest_daily_limit: int = Field(default=10, description="游客每日查询限制")
    free_user_daily_limit: int = Field(default=50, description="免费用户每日查询限制")
    premium_user_daily_limit: int = Field(default=-1, description="高级用户每日查询限制（-1=无限）")

    # 收藏限制
    free_user_favorite_limit: int = Field(default=10, description="免费用户收藏限制")
    premium_user_favorite_limit: int = Field(default=999999, description="高级用户收藏限制")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="json", description="日志格式")

    # Sentry配置
    sentry_dsn: str = Field(default="", description="Sentry DSN")

    # 其他配置
    timezone: str = Field(default="Asia/Shanghai", description="时区")

    @property
    def cors_origins_list(self) -> List[str]:
        """获取CORS源列表"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.app_env == "development"

    @property
    def is_testing(self) -> bool:
        """判断是否为测试环境"""
        return self.app_env == "testing"


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例

    使用lru_cache确保配置只加载一次
    """
    return Settings()


# 导出配置实例
settings = get_settings()
