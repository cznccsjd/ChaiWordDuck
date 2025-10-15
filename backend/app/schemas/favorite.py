"""
收藏相关的Pydantic模型

定义收藏添加、删除、查询相关的数据模型
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.word import WordDetail


# ============= Request Models =============


class FavoriteAddRequest(BaseModel):
    """添加收藏请求"""

    word_id: int = Field(..., description="单词ID", alias="wordId", gt=0)

    class Config:
        populate_by_name = True


# ============= Response Models =============


class FavoriteAddResponse(BaseModel):
    """添加收藏响应"""

    id: int = Field(..., description="收藏ID")
    user_id: int = Field(..., description="用户ID", alias="userId")
    word_id: int = Field(..., description="单词ID", alias="wordId")
    created_at: datetime = Field(..., description="创建时间", alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class FavoriteDeleteResponse(BaseModel):
    """删除收藏响应"""

    message: str = Field(..., description="响应消息")


class FavoriteItem(BaseModel):
    """收藏列表项"""

    id: int = Field(..., description="收藏ID")
    word: WordDetail = Field(..., description="单词详情")
    created_at: datetime = Field(..., description="收藏时间", alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""

    favorites: list[FavoriteItem] = Field(..., description="收藏列表")
    total: int = Field(..., description="总数")

    class Config:
        populate_by_name = True


class FavoriteCheckResponse(BaseModel):
    """检查是否已收藏响应"""

    is_favorited: bool = Field(..., description="是否已收藏", alias="isFavorited")
    favorite_id: Optional[int] = Field(None, description="收藏ID（如果已收藏）", alias="favoriteId")

    class Config:
        populate_by_name = True
