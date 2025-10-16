"""AI生成服务（限额控制）"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import Request

from app.models.ai_generation_log import AIGenerationLog
from app.models.user import User
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIGenerationService:
    """AI生成服务"""

    @staticmethod
    async def check_generation_limit(
        current_user: User | None,
        request: Request,
        db: AsyncSession
    ) -> bool:
        """
        检查AI生成限额

        Returns:
            bool: True=超出限额，False=可继续
        """
        settings = get_settings()

        # 确定限额
        if current_user:
            limit = settings.ai_generation_limit_user
            user_id = current_user.id
        else:
            limit = settings.ai_generation_limit_guest
            user_id = None

        # 获取IP
        ip_address = request.client.host

        # 查询今天的生成次数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if user_id:
            result = await db.execute(
                select(func.count(AIGenerationLog.id))
                .where(
                    AIGenerationLog.user_id == user_id,
                    AIGenerationLog.created_at >= today_start
                )
            )
        else:
            result = await db.execute(
                select(func.count(AIGenerationLog.id))
                .where(
                    AIGenerationLog.ip_address == ip_address,
                    AIGenerationLog.user_id.is_(None),
                    AIGenerationLog.created_at >= today_start
                )
            )

        count = result.scalar() or 0

        logger.info(
            f"AI limit check: user={user_id}, ip={ip_address}, "
            f"count={count}/{limit}"
        )

        return count >= limit

    @staticmethod
    async def log_generation(
        word: str,
        current_user: User | None,
        request: Request,
        db: AsyncSession
    ):
        """记录AI生成日志"""
        log = AIGenerationLog(
            user_id=current_user.id if current_user else None,
            ip_address=request.client.host,
            word=word
        )
        db.add(log)
        await db.commit()

        user_info = f"user_id={current_user.id}" if current_user else "guest"
        logger.info(f"Logged AI generation: word={word}, {user_info}")
