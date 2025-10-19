"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def basic_health_check() -> dict:
    """
    Basic health check endpoint

    Used by load balancers and monitoring services
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Detailed health check endpoint

    Checks:
    - Database connectivity
    - Redis connectivity (if configured)
    - System resources
    """
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
        "checks": {}
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis (if configured)
    if settings.redis_url:
        try:
            # TODO: Add Redis health check when Redis is integrated
            health_status["checks"]["redis"] = "not_implemented"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

    return health_status
