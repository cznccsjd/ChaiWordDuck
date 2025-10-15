"""
收藏系统API路由

实现添加收藏、删除收藏、获取收藏列表、检查收藏状态功能
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.logging import get_logger, log_with_context
from app.models import User, Word, Favorite
from app.schemas.common import ErrorCode, SuccessResponse
from app.schemas.favorite import (
    FavoriteAddRequest,
    FavoriteAddResponse,
    FavoriteDeleteResponse,
    FavoriteListResponse,
    FavoriteItem,
    FavoriteCheckResponse,
)
from app.schemas.word import WordDetail

router = APIRouter()
logger = get_logger(__name__)


async def get_user_favorite_count(db: AsyncSession, user: User) -> int:
    """
    获取用户收藏数量

    Args:
        db: 数据库会话
        user: 用户对象

    Returns:
        int: 收藏数量
    """
    result = await db.execute(
        select(func.count(Favorite.id)).where(Favorite.user_id == user.id)
    )
    return result.scalar_one()


def get_user_favorite_limit(user: User) -> int:
    """
    获取用户收藏限制

    Args:
        user: 用户对象

    Returns:
        int: 收藏限制数量
    """
    if user.membership_tier == "premium":
        return settings.premium_user_favorite_limit
    else:
        return settings.free_user_favorite_limit


@router.post(
    "",
    response_model=SuccessResponse[FavoriteAddResponse],
    status_code=status.HTTP_201_CREATED,
    summary="添加收藏",
    description="将单词添加到收藏列表",
)
async def add_favorite(
    data: FavoriteAddRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[FavoriteAddResponse]:
    """
    添加收藏

    Args:
        data: 收藏请求数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 收藏信息

    Raises:
        HTTPException: 404 单词不存在
        HTTPException: 400 已收藏或收藏数量达到上限
    """
    log_with_context(
        logger,
        "info",
        "Add favorite attempt",
        user_id=current_user.id,
        word_id=data.word_id,
    )

    # 检查单词是否存在
    result = await db.execute(select(Word).where(Word.id == data.word_id))
    word = result.scalar_one_or_none()

    if not word:
        log_with_context(
            logger, "warning", "Word not found for favorite", word_id=data.word_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.WORD_NOT_FOUND,
                "message": "单词不存在",
            },
        )

    # 检查是否已收藏
    check_result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .where(Favorite.word_id == data.word_id)
    )
    existing_favorite = check_result.scalar_one_or_none()

    if existing_favorite:
        log_with_context(
            logger,
            "warning",
            "Word already favorited",
            user_id=current_user.id,
            word_id=data.word_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.ALREADY_FAVORITED,
                "message": "该单词已在收藏列表中",
            },
        )

    # 检查收藏数量限制
    favorite_count = await get_user_favorite_count(db, current_user)
    favorite_limit = get_user_favorite_limit(current_user)

    if favorite_count >= favorite_limit:
        log_with_context(
            logger,
            "warning",
            "Favorite limit exceeded",
            user_id=current_user.id,
            favorite_count=favorite_count,
            favorite_limit=favorite_limit,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.FAVORITE_LIMIT_EXCEEDED,
                "message": f"免费用户收藏已达上限（{favorite_limit}个），升级高级版可无限收藏",
            },
        )

    # 创建收藏
    favorite = Favorite(
        user_id=current_user.id,
        word_id=data.word_id,
    )
    db.add(favorite)

    try:
        await db.commit()
        await db.refresh(favorite)

        log_with_context(
            logger,
            "info",
            "Favorite added successfully",
            user_id=current_user.id,
            word_id=data.word_id,
            favorite_id=favorite.id,
        )

        # 构造响应
        response_data = FavoriteAddResponse(
            id=favorite.id,
            user_id=favorite.user_id,
            word_id=favorite.word_id,
            created_at=favorite.created_at,
        )

        return SuccessResponse(data=response_data)

    except IntegrityError as e:
        # 并发情况下可能已经收藏
        await db.rollback()
        log_with_context(
            logger,
            "warning",
            "Favorite integrity error",
            error=str(e),
            user_id=current_user.id,
            word_id=data.word_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.ALREADY_FAVORITED,
                "message": "该单词已在收藏列表中",
            },
        )
    except Exception as e:
        await db.rollback()
        log_with_context(
            logger,
            "error",
            "Add favorite failed",
            error=str(e),
            user_id=current_user.id,
            word_id=data.word_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.DATABASE_ERROR,
                "message": "添加收藏失败，请稍后重试",
            },
        )


@router.delete(
    "/{word_id}",
    response_model=SuccessResponse[FavoriteDeleteResponse],
    status_code=status.HTTP_200_OK,
    summary="删除收藏",
    description="从收藏列表中删除单词",
)
async def delete_favorite(
    word_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[FavoriteDeleteResponse]:
    """
    删除收藏

    Args:
        word_id: 单词ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 删除成功消息

    Raises:
        HTTPException: 404 收藏不存在
    """
    log_with_context(
        logger,
        "info",
        "Delete favorite attempt",
        user_id=current_user.id,
        word_id=word_id,
    )

    # 查询收藏
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .where(Favorite.word_id == word_id)
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        log_with_context(
            logger,
            "warning",
            "Favorite not found",
            user_id=current_user.id,
            word_id=word_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.NOT_FOUND,
                "message": "收藏不存在",
            },
        )

    # 删除收藏
    await db.delete(favorite)
    await db.commit()

    log_with_context(
        logger,
        "info",
        "Favorite deleted successfully",
        user_id=current_user.id,
        word_id=word_id,
    )

    response_data = FavoriteDeleteResponse(message="已取消收藏")

    return SuccessResponse(data=response_data)


@router.get(
    "",
    response_model=SuccessResponse[FavoriteListResponse],
    status_code=status.HTTP_200_OK,
    summary="获取收藏列表",
    description="获取用户的收藏列表，支持搜索和分页",
)
async def get_favorites(
    search: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[FavoriteListResponse]:
    """
    获取收藏列表

    Args:
        search: 搜索关键词（可选）
        limit: 每页数量
        offset: 偏移量
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 收藏列表和总数
    """
    log_with_context(
        logger,
        "info",
        "Get favorites list",
        user_id=current_user.id,
        search=search,
        limit=limit,
        offset=offset,
    )

    # 构建查询
    query = (
        select(Favorite, Word)
        .join(Word, Favorite.word_id == Word.id)
        .where(Favorite.user_id == current_user.id)
    )

    # 搜索过滤
    if search:
        search_pattern = f"%{search}%"
        query = query.where(Word.word.ilike(search_pattern))

    # 排序（按收藏时间倒序）
    query = query.order_by(Favorite.created_at.desc())

    # 查询总数
    count_query = (
        select(func.count(Favorite.id))
        .join(Word, Favorite.word_id == Word.id)
        .where(Favorite.user_id == current_user.id)
    )
    if search:
        count_query = count_query.where(Word.word.ilike(search_pattern))

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 分页查询
    result = await db.execute(query.limit(limit).offset(offset))
    rows = result.all()

    # 构造响应
    favorites = []
    for favorite, word in rows:
        word_detail = WordDetail(
            id=word.id,
            word=word.word,
            phonetic=word.phonetic,
            part_of_speech=word.part_of_speech,
            core_game=word.core_game,
            scenario_formal=word.scenario_formal,
            scenario_casual=word.scenario_casual,
            etymology_breakdown=word.etymology_breakdown,
            etymology_story=word.etymology_story,
            common_mistakes=word.common_mistakes,
            memory_trick=word.memory_trick,
            is_golden=word.is_golden,
            created_at=word.created_at,
        )
        favorite_item = FavoriteItem(
            id=favorite.id,
            word=word_detail,
            created_at=favorite.created_at,
        )
        favorites.append(favorite_item)

    response_data = FavoriteListResponse(favorites=favorites, total=total)

    return SuccessResponse(data=response_data)


@router.get(
    "/check/{word_id}",
    response_model=SuccessResponse[FavoriteCheckResponse],
    status_code=status.HTTP_200_OK,
    summary="检查收藏状态",
    description="检查指定单词是否已收藏",
)
async def check_favorite(
    word_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[FavoriteCheckResponse]:
    """
    检查收藏状态

    Args:
        word_id: 单词ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 收藏状态信息
    """
    log_with_context(
        logger,
        "info",
        "Check favorite status",
        user_id=current_user.id,
        word_id=word_id,
    )

    # 查询收藏
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .where(Favorite.word_id == word_id)
    )
    favorite = result.scalar_one_or_none()

    if favorite:
        response_data = FavoriteCheckResponse(
            is_favorited=True,
            favorite_id=favorite.id,
        )
    else:
        response_data = FavoriteCheckResponse(
            is_favorited=False,
            favorite_id=None,
        )

    return SuccessResponse(data=response_data)
