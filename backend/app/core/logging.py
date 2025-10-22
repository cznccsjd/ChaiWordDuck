"""
日志配置模块

提供结构化日志支持
"""
import logging
import sys
from typing import Any

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        import json
        from datetime import datetime, timezone

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加自定义字段
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # 确保所有字段都是字符串，避免编码问题
        try:
            return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            # 如果序列化失败，回退到简单格式
            fallback_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": str(record.getMessage()),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "serialization_error": str(e)
            }
            return json.dumps(fallback_data, ensure_ascii=False, separators=(',', ':'))


class TextFormatter(logging.Formatter):
    """文本格式日志格式化器"""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录，确保中文正确显示"""
        try:
            result = super().format(record)
            # 确保返回的是正确的Unicode字符串
            return result
        except Exception as e:
            # 如果格式化失败，返回基本信息
            return f"{self.formatTime(record)} - {record.name} - {record.levelname} - FORMATTING_ERROR: {str(e)} - {record.getMessage()}"


def setup_logging() -> None:
    """配置应用日志"""
    import sys

    # 确保正确设置标准输出编码
    if sys.platform == "win32":
        # Windows下设置UTF-8编码
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')

    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # 设置日志格式
    if settings.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    console_handler.setFormatter(formatter)
    console_handler.stream.reconfigure(encoding='utf-8') if hasattr(console_handler.stream, 'reconfigure') else None
    root_logger.addHandler(console_handler)

    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        logging.Logger: 日志器实例
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs: Any) -> None:
    """
    记录带上下文的日志

    Args:
        logger: 日志器
        level: 日志级别
        message: 日志消息
        **kwargs: 额外的上下文数据
    """
    log_func = getattr(logger, level.lower())
    extra = {"extra_data": kwargs} if kwargs else {}
    log_func(message, extra=extra)
