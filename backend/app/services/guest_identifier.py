"""
游客身份识别服务

负责从HTTP请求中提取游客唯一标识符，用于查询限流。
"""
import hashlib
from typing import Optional
from fastapi import Request

from app.core.logging import get_logger

logger = get_logger(__name__)


class GuestIdentifierService:
    """
    游客身份识别服务

    MVP阶段使用IP地址作为游客唯一标识符。
    未来可升级为IP+User-Agent的组合hash，提高识别准确性。
    """

    @staticmethod
    def get_identifier(request: Request) -> str:
        """
        获取游客唯一标识符（MVP：使用IP地址）

        支持代理和负载均衡场景，优先从X-Forwarded-For头获取真实IP。

        Args:
            request: FastAPI Request对象

        Returns:
            str: 游客唯一标识符（IP地址）

        Examples:
            >>> identifier = GuestIdentifierService.get_identifier(request)
            >>> # 返回: "192.168.1.100"
        """
        # 1. 优先从X-Forwarded-For获取真实IP（代理/负载均衡场景）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For格式: "client, proxy1, proxy2"
            # 取第一个IP（真实客户端IP）
            ip = forwarded.split(",")[0].strip()
            logger.debug(f"从X-Forwarded-For获取游客IP: {ip}")
            return ip

        # 2. 从直连请求获取IP
        if request.client:
            ip = request.client.host
            logger.debug(f"从request.client获取游客IP: {ip}")
            return ip

        # 3. 无法获取IP的降级处理
        logger.warning("无法获取游客IP地址，使用默认标识符")
        return "unknown"

    @staticmethod
    def get_enhanced_identifier(request: Request) -> str:
        """
        获取增强型游客标识符（Phase 2备用）

        组合IP地址和User-Agent生成hash，提高识别准确性。
        可以防止同一IP下不同用户被误识别为同一游客。

        Args:
            request: FastAPI Request对象

        Returns:
            str: 游客唯一标识符（SHA256 hash的前32位）

        Examples:
            >>> identifier = GuestIdentifierService.get_enhanced_identifier(request)
            >>> # 返回: "a1b2c3d4e5f6..."（32字符hash）

        Note:
            此方法暂未启用，预留给Phase 2使用。
        """
        # 获取IP地址
        ip = GuestIdentifierService.get_identifier(request)

        # 获取User-Agent
        user_agent = request.headers.get("User-Agent", "")

        # 组合并生成hash
        combined = f"{ip}:{user_agent}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()[:32]

        logger.debug(f"生成增强型游客标识符: {hash_value} (基于IP={ip}, UA长度={len(user_agent)})")

        return hash_value

    @staticmethod
    def is_valid_identifier(identifier: str) -> bool:
        """
        验证标识符是否有效

        Args:
            identifier: 游客标识符

        Returns:
            bool: 是否有效

        Examples:
            >>> GuestIdentifierService.is_valid_identifier("192.168.1.100")
            True
            >>> GuestIdentifierService.is_valid_identifier("")
            False
            >>> GuestIdentifierService.is_valid_identifier("unknown")
            False
        """
        if not identifier:
            return False

        if identifier == "unknown":
            return False

        return True
