"""
API v1路由包
"""
from fastapi import APIRouter

from app.api.v1 import auth

# 创建v1 API路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 未来添加更多路由
# api_router.include_router(words.router, prefix="/words", tags=["单词"])
# api_router.include_router(favorites.router, prefix="/favorites", tags=["收藏"])
