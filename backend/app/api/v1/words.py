"""
单词查询API路由

实现单词查询、查询限制、根据ID获取单词功能
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.logging import get_logger, log_with_context
from app.models import User, Word, QueryLog
from app.schemas.common import ErrorCode, SuccessResponse
from app.schemas.word import (
    WordQueryRequest,
    WordQueryResponse,
    QueryLimitInfo,
    WordByIdResponse,
)

router = APIRouter()
logger = get_logger(__name__)


async def get_user_query_count(
    db: AsyncSession,
    user: User,
    query_date: date,
) -> int:
    """
    获取用户今日查询次数

    Args:
        db: 数据库会话
        user: 用户对象
        query_date: 查询日期

    Returns:
        int: 今日查询次数
    """
    result = await db.execute(
        select(func.count(QueryLog.id))
        .where(QueryLog.user_id == user.id)
        .where(QueryLog.query_date == query_date)
    )
    return result.scalar_one()


async def get_user_queried_word_ids(
    db: AsyncSession,
    user: User,
    query_date: date,
) -> list[int]:
    """
    获取用户今日已查询的单词ID列表

    Args:
        db: 数据库会话
        user: 用户对象
        query_date: 查询日期

    Returns:
        list[int]: 已查询单词ID列表
    """
    result = await db.execute(
        select(QueryLog.word_id)
        .where(QueryLog.user_id == user.id)
        .where(QueryLog.query_date == query_date)
        .distinct()
    )
    return [row[0] for row in result.all()]


async def check_word_already_queried(
    db: AsyncSession,
    user: User,
    word_id: int,
    query_date: date,
) -> bool:
    """
    检查单词今日是否已查询过

    Args:
        db: 数据库会话
        user: 用户对象
        word_id: 单词ID
        query_date: 查询日期

    Returns:
        bool: 是否已查询过
    """
    result = await db.execute(
        select(QueryLog.id)
        .where(QueryLog.user_id == user.id)
        .where(QueryLog.word_id == word_id)
        .where(QueryLog.query_date == query_date)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


def get_user_daily_limit(user: User) -> int:
    """
    获取用户每日查询限制

    Args:
        user: 用户对象

    Returns:
        int: 每日查询限制次数
    """
    if user.membership_tier == "premium":
        return settings.premium_user_daily_limit
    else:
        return settings.free_user_daily_limit


async def query_word_internal(
    word_text: str,
    current_user: User,
    db: AsyncSession,
) -> WordQueryResponse:
    """
    单词查询内部逻辑（供GET和POST共享）

    Args:
        word_text: 要查询的单词
        current_user: 当前用户
        db: 数据库会话

    Returns:
        WordQueryResponse: 单词查询响应数据

    Raises:
        HTTPException: 404 单词不存在
        HTTPException: 400 查询次数用尽
    """
    # 标准化单词（转小写并去除空格）
    normalized_word = word_text.strip().lower()

    # 验证单词格式
    if not normalized_word:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "单词不能为空",
            },
        )

    if not all(c.isalpha() or c in ['-', ' '] for c in normalized_word):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "单词只能包含字母、连字符和空格",
            },
        )

    log_with_context(
        logger, "info", "Word query attempt", user_id=current_user.id, word=normalized_word
    )

    # 查询单词
    result = await db.execute(
        select(Word)
        .where(Word.word == normalized_word)
        .order_by(Word.is_golden.desc())  # 优先返回黄金手册
    )
    word = result.scalar_one_or_none()

    if not word:
        log_with_context(
            logger,
            "warning",
            "Word not found",
            user_id=current_user.id,
            word=normalized_word,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.WORD_NOT_FOUND,
                "message": "未找到该单词，请检查拼写",
            },
        )

    today = date.today()

    # 检查是否已查询过该单词
    already_queried = await check_word_already_queried(db, current_user, word.id, today)

    if not already_queried:
        # 首次查询，检查查询次数限制
        used_queries = await get_user_query_count(db, current_user, today)
        daily_limit = get_user_daily_limit(current_user)

        if used_queries >= daily_limit:
            log_with_context(
                logger,
                "warning",
                "Query limit exceeded",
                user_id=current_user.id,
                used_queries=used_queries,
                daily_limit=daily_limit,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.QUERY_LIMIT_EXCEEDED,
                    "message": f"今日查询次数已用完。游客1次/天，注册用户3次/天",
                },
            )

        # 记录查询日志
        query_log = QueryLog(
            user_id=current_user.id,
            word_id=word.id,
            query_date=today,
        )
        db.add(query_log)
        await db.commit()

        log_with_context(
            logger,
            "info",
            "Query log created",
            user_id=current_user.id,
            word_id=word.id,
        )

    # 计算剩余查询次数
    current_used_queries = await get_user_query_count(db, current_user, today)
    daily_limit = get_user_daily_limit(current_user)
    remaining_queries = max(0, daily_limit - current_used_queries)

    log_with_context(
        logger,
        "info",
        "Word query successful",
        user_id=current_user.id,
        word_id=word.id,
        remaining_queries=remaining_queries,
    )

    # 构造响应
    return WordQueryResponse(
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
        remaining_queries=remaining_queries,
    )


@router.get(
    "/query/{word}",
    response_model=SuccessResponse[WordQueryResponse],
    status_code=status.HTTP_200_OK,
    summary="查询单词（GET路径参数）",
    description="通过URL路径参数查询单词，适用于浏览器和简单HTTP客户端",
)
async def query_word_by_path(
    word: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[WordQueryResponse]:
    """
    查询单词（GET方式）

    Args:
        word: 要查询的单词（路径参数）
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 包含单词详细信息和剩余查询次数

    Raises:
        HTTPException: 404 单词不存在
        HTTPException: 400 查询次数用尽
    """
    response_data = await query_word_internal(word, current_user, db)
    return SuccessResponse(data=response_data)


@router.post(
    "/query",
    response_model=SuccessResponse[WordQueryResponse],
    status_code=status.HTTP_200_OK,
    summary="查询单词（POST JSON）",
    description="通过POST JSON body查询单词详细信息，包含拆解数据和查询次数限制",
)
async def query_word(
    data: WordQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[WordQueryResponse]:
    """
    查询单词（POST方式）

    Args:
        data: 查询请求数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 包含单词详细信息和剩余查询次数

    Raises:
        HTTPException: 404 单词不存在
        HTTPException: 400 查询次数用尽
    """
    response_data = await query_word_internal(data.word, current_user, db)
    return SuccessResponse(data=response_data)


@router.get(
    "/query-limit",
    response_model=SuccessResponse[QueryLimitInfo],
    status_code=status.HTTP_200_OK,
    summary="获取查询限制信息",
    description="获取用户今日查询次数统计和已查询单词列表",
)
async def get_query_limit(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[QueryLimitInfo]:
    """
    获取查询限制信息

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 查询限制信息
    """
    log_with_context(
        logger, "info", "Query limit info requested", user_id=current_user.id
    )

    today = date.today()

    # 获取今日查询次数
    used_queries = await get_user_query_count(db, current_user, today)

    # 获取已查询单词ID列表
    queried_word_ids = await get_user_queried_word_ids(db, current_user, today)

    # 获取每日限制
    daily_limit = get_user_daily_limit(current_user)

    # 计算剩余次数
    remaining_queries = max(0, daily_limit - used_queries)

    response_data = QueryLimitInfo(
        total_queries=daily_limit,
        remaining_queries=remaining_queries,
        used_queries=used_queries,
        queried_words=queried_word_ids,
    )

    return SuccessResponse(data=response_data)


@router.get(
    "/{word_id}",
    response_model=SuccessResponse[WordByIdResponse],
    status_code=status.HTTP_200_OK,
    summary="根据ID获取单词",
    description="根据单词ID获取详细信息，不计入查询次数（用于复习和收藏列表）",
)
async def get_word_by_id(
    word_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[WordByIdResponse]:
    """
    根据ID获取单词

    Args:
        word_id: 单词ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        SuccessResponse: 单词详细信息

    Raises:
        HTTPException: 404 单词不存在
    """
    log_with_context(
        logger, "info", "Get word by ID", user_id=current_user.id, word_id=word_id
    )

    # 查询单词
    result = await db.execute(select(Word).where(Word.id == word_id))
    word = result.scalar_one_or_none()

    if not word:
        log_with_context(
            logger, "warning", "Word not found by ID", word_id=word_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.WORD_NOT_FOUND,
                "message": "单词不存在",
            },
        )

    log_with_context(
        logger,
        "info",
        "Word retrieved by ID",
        user_id=current_user.id,
        word_id=word.id,
    )

    # 构造响应
    response_data = WordByIdResponse(
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

    return SuccessResponse(data=response_data)
