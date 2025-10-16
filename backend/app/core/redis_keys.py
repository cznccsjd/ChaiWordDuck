"""
Redis键管理模块

统一管理所有Redis键的命名规范和操作方法
"""
from datetime import date
from typing import Optional


class RedisKeys:
    """
    Redis键命名规范

    命名规则：
    - 使用冒号分隔命名空间
    - 格式：{功能}:{类型}:{标识符}:{时间窗口}
    - 示例：query_limit:guest:abc123:2025-10-16

    TTL策略：
    - 分钟级：60秒
    - 小时级：3600秒
    - 日级：86400秒（24小时）
    """

    # ==================== IP限流（防爬虫/DDoS） ====================

    @staticmethod
    def ip_rate_limit_minute(ip: str) -> str:
        """
        IP分钟级限流键

        用途：限制单个IP每分钟的请求次数（30次/分钟）
        TTL：60秒
        数据类型：String（计数器）

        Args:
            ip: 客户端IP地址

        Returns:
            Redis键名

        示例:
            rate_limit:ip:192.168.1.100:minute
        """
        return f"rate_limit:ip:{ip}:minute"

    @staticmethod
    def ip_rate_limit_hour(ip: str) -> str:
        """
        IP小时级限流键（可选，用于更严格的限制）

        用途：限制单个IP每小时的请求次数（1000次/小时）
        TTL：3600秒
        数据类型：String（计数器）

        Args:
            ip: 客户端IP地址

        Returns:
            Redis键名
        """
        return f"rate_limit:ip:{ip}:hour"

    # ==================== 游客查询限额 ====================

    @staticmethod
    def guest_daily_limit(guest_id: str, query_date: Optional[date] = None) -> str:
        """
        游客日查询限额键

        用途：记录游客今日已查询次数（10次/天）
        TTL：86400秒（24小时）
        数据类型：String（计数器）

        Args:
            guest_id: 游客唯一标识（SHA256 hash）
            query_date: 查询日期（默认今天）

        Returns:
            Redis键名

        示例:
            query_limit:guest:abc123def456:2025-10-16
        """
        if query_date is None:
            query_date = date.today()
        date_str = query_date.isoformat()
        return f"query_limit:guest:{guest_id}:{date_str}"

    @staticmethod
    def guest_queried_words(guest_id: str, query_date: Optional[date] = None) -> str:
        """
        游客已查询单词集合键

        用途：记录游客今日已查询过的单词ID（用于"重复查询不计次数"）
        TTL：86400秒（24小时）
        数据类型：Set

        Args:
            guest_id: 游客唯一标识
            query_date: 查询日期（默认今天）

        Returns:
            Redis键名

        示例:
            queried_words:guest:abc123def456:2025-10-16
            Members: ["1", "5", "12", "23", "45"]
        """
        if query_date is None:
            query_date = date.today()
        date_str = query_date.isoformat()
        return f"queried_words:guest:{guest_id}:{date_str}"

    # ==================== 注册用户查询限额 ====================

    @staticmethod
    def user_daily_limit(user_id: int, query_date: Optional[date] = None) -> str:
        """
        用户日查询限额键

        用途：记录用户今日已查询次数（50次/天，Premium无限）
        TTL：86400秒（24小时）
        数据类型：String（计数器）

        Args:
            user_id: 用户ID
            query_date: 查询日期（默认今天）

        Returns:
            Redis键名

        示例:
            query_limit:user:123:2025-10-16
        """
        if query_date is None:
            query_date = date.today()
        date_str = query_date.isoformat()
        return f"query_limit:user:{user_id}:{date_str}"

    @staticmethod
    def user_queried_words(user_id: int, query_date: Optional[date] = None) -> str:
        """
        用户已查询单词集合键

        用途：记录用户今日已查询过的单词ID
        TTL：86400秒（24小时）
        数据类型：Set

        Args:
            user_id: 用户ID
            query_date: 查询日期（默认今天）

        Returns:
            Redis键名

        示例:
            queried_words:user:123:2025-10-16
        """
        if query_date is None:
            query_date = date.today()
        date_str = query_date.isoformat()
        return f"queried_words:user:{user_id}:{date_str}"

    # ==================== 防滥用检测 ====================

    @staticmethod
    def abuse_recent_queries(identifier: str) -> str:
        """
        最近查询记录键（用于滥用检测）

        用途：记录最近N次查询的单词，用于检测爬虫模式
        TTL：300秒（5分钟）
        数据类型：List（FIFO队列）

        Args:
            identifier: IP或guest_id

        Returns:
            Redis键名

        示例:
            abuse:recent:192.168.1.100
            List: ["word1", "word2", "word3", ...]
        """
        return f"abuse:recent:{identifier}"

    @staticmethod
    def captcha_required(identifier: str) -> str:
        """
        需要Captcha验证标记键

        用途：标记需要进行人机验证的IP/游客
        TTL：3600秒（1小时）
        数据类型：String（原因描述）

        Args:
            identifier: IP或guest_id

        Returns:
            Redis键名

        示例:
            captcha:required:192.168.1.100
            Value: "REPEATED_QUERY" 或 "ALPHABETICAL_CRAWLING"
        """
        return f"captcha:required:{identifier}"

    @staticmethod
    def ip_blacklist(ip: str) -> str:
        """
        IP黑名单键

        用途：临时封禁恶意IP
        TTL：86400秒（24小时）
        数据类型：String

        Args:
            ip: 客户端IP地址

        Returns:
            Redis键名
        """
        return f"blacklist:ip:{ip}"

    # ==================== 缓存 ====================

    @staticmethod
    def word_cache(word: str) -> str:
        """
        单词数据缓存键

        用途：缓存单词查询结果，减少数据库访问
        TTL：604800秒（7天）
        数据类型：String（JSON序列化）

        Args:
            word: 单词文本（小写）

        Returns:
            Redis键名

        示例:
            word:cache:accountability
        """
        return f"word:cache:{word.lower()}"

    @staticmethod
    def user_session(user_id: int) -> str:
        """
        用户会话缓存键

        用途：缓存用户信息，减少数据库查询
        TTL：3600秒（1小时）
        数据类型：String（JSON序列化）

        Args:
            user_id: 用户ID

        Returns:
            Redis键名
        """
        return f"session:user:{user_id}"

    # ==================== 统计数据 ====================

    @staticmethod
    def stats_daily_queries(query_date: Optional[date] = None) -> str:
        """
        每日查询统计键

        用途：记录每日总查询次数（所有用户+游客）
        TTL：永久保存
        数据类型：String（计数器）

        Args:
            query_date: 统计日期（默认今天）

        Returns:
            Redis键名
        """
        if query_date is None:
            query_date = date.today()
        date_str = query_date.isoformat()
        return f"stats:queries:daily:{date_str}"

    @staticmethod
    def stats_guest_to_user_conversion() -> str:
        """
        游客转化统计键

        用途：记录游客转注册用户的次数
        TTL：永久保存
        数据类型：String（计数器）
        """
        return "stats:conversion:guest_to_user"


# ==================== 辅助工具函数 ====================


def get_ttl_seconds(key_type: str) -> int:
    """
    获取不同类型键的TTL时间（秒）

    Args:
        key_type: 键类型（minute/hour/daily/cache_short/cache_long）

    Returns:
        TTL秒数
    """
    ttl_map = {
        "minute": 60,
        "hour": 3600,
        "daily": 86400,  # 24小时
        "cache_short": 3600,  # 1小时
        "cache_long": 604800,  # 7天
        "permanent": -1,  # 永久
    }
    return ttl_map.get(key_type, 86400)


def parse_guest_id_from_key(key: str) -> Optional[str]:
    """
    从Redis键中提取guest_id

    Args:
        key: Redis键名

    Returns:
        guest_id 或 None

    示例:
        >>> parse_guest_id_from_key("query_limit:guest:abc123:2025-10-16")
        "abc123"
    """
    parts = key.split(":")
    if len(parts) >= 3 and parts[1] == "guest":
        return parts[2]
    return None


def parse_user_id_from_key(key: str) -> Optional[int]:
    """
    从Redis键中提取user_id

    Args:
        key: Redis键名

    Returns:
        user_id 或 None

    示例:
        >>> parse_user_id_from_key("query_limit:user:123:2025-10-16")
        123
    """
    parts = key.split(":")
    if len(parts) >= 3 and parts[1] == "user":
        try:
            return int(parts[2])
        except ValueError:
            return None
    return None


# ==================== 批量操作工具 ====================


class RedisKeysBatch:
    """Redis键批量操作工具类"""

    @staticmethod
    def get_all_guest_keys_for_date(guest_id: str, query_date: date) -> list[str]:
        """
        获取指定游客和日期的所有Redis键

        Args:
            guest_id: 游客ID
            query_date: 查询日期

        Returns:
            Redis键列表
        """
        return [
            RedisKeys.guest_daily_limit(guest_id, query_date),
            RedisKeys.guest_queried_words(guest_id, query_date),
        ]

    @staticmethod
    def get_all_user_keys_for_date(user_id: int, query_date: date) -> list[str]:
        """
        获取指定用户和日期的所有Redis键

        Args:
            user_id: 用户ID
            query_date: 查询日期

        Returns:
            Redis键列表
        """
        return [
            RedisKeys.user_daily_limit(user_id, query_date),
            RedisKeys.user_queried_words(user_id, query_date),
        ]


# ==================== 示例用法 ====================

if __name__ == "__main__":
    # 示例：生成游客限流键
    guest_id = "abc123def456"
    key = RedisKeys.guest_daily_limit(guest_id)
    print(f"游客限流键: {key}")
    # 输出: query_limit:guest:abc123def456:2025-10-16

    # 示例：生成IP限流键
    ip = "192.168.1.100"
    key = RedisKeys.ip_rate_limit_minute(ip)
    print(f"IP限流键: {key}")
    # 输出: rate_limit:ip:192.168.1.100:minute

    # 示例：获取TTL
    ttl = get_ttl_seconds("daily")
    print(f"日级TTL: {ttl}秒 ({ttl/3600}小时)")
    # 输出: 日级TTL: 86400秒 (24.0小时)

    # 示例：批量获取游客键
    keys = RedisKeysBatch.get_all_guest_keys_for_date(guest_id, date.today())
    print(f"游客所有键: {keys}")
    # 输出:
    # [
    #   'query_limit:guest:abc123def456:2025-10-16',
    #   'queried_words:guest:abc123def456:2025-10-16'
    # ]
