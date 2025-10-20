"""
单词查询API路由

实现单词查询、查询限制、根据ID获取单词功能
支持游客模式（无需登录即可查询）
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_optional_user
from app.core.logging import get_logger, log_with_context
from app.models import User, Word, QueryLog
from app.schemas.common import ErrorCode, SuccessResponse
from app.schemas.word import (
    WordQueryRequest,
    WordQueryResponse,
    QueryLimitInfo,
    WordByIdResponse,
)
from app.services.rate_limit import RateLimitService
from app.services.ai.factory import AIServiceFactory
from app.services.ai.base import AIServiceError, AITimeoutError, AIRateLimitError, AIParseError
from app.services.ai_generation_service import AIGenerationService

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
    current_user: Optional[User],
    db: AsyncSession,
    request: Optional[Request] = None,
) -> WordQueryResponse:
    """
    单词查询内部逻辑（供GET和POST共享，支持游客和注册用户）

    Args:
        word_text: 要查询的单词
        current_user: 当前用户（None表示游客）
        db: 数据库会话
        request: 请求对象（游客模式需要用于获取IP）

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

    # 记录日志
    user_info = f"user_id={current_user.id}" if current_user else "guest"
    log_with_context(
        logger, "info", "Word query attempt",
        user_info=user_info, word=normalized_word
    )

    # 查询单词
    result = await db.execute(
        select(Word)
        .where(Word.word == normalized_word)
        .order_by(Word.is_golden.desc())  # 优先返回黄金手册
    )
    word = result.scalar_one_or_none()

    if word:
        log_with_context(
            logger, "info", "Word found in cache",
            word=normalized_word, is_golden=word.is_golden
        )

        # 检查查询限制并记录
        rate_limiter = RateLimitService(db)
        allowed, used, limit, user_type = await rate_limiter.check_and_record_query(
            word_id=word.id,
            user=current_user,
            request=request,
        )

        # 计算剩余查询次数
        remaining_queries = limit - used if limit != -1 else -1

        log_with_context(
            logger,
            "info",
            "Word query successful",
            user_info=user_info,
            word_id=word.id,
            user_type=user_type,
            used_queries=used,
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

    # 2. 数据库无数据 → 检查AI生成限额
    log_with_context(
        logger, "info", "Word not in cache, checking AI limit",
        word=normalized_word
    )

    limit_exceeded = await AIGenerationService.check_generation_limit(
        current_user, request, db
    )

    if limit_exceeded:
        log_with_context(
            logger, "warning", "AI generation limit exceeded",
            word=normalized_word
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "AI_GENERATION_LIMIT_EXCEEDED",
                "message": "AI生成限额已用完（游客5次/天，注册用户10次/天）"
            }
        )

    # 3. 调用AI生成
    try:
        log_with_context(
            logger, "info", "Triggering AI generation",
            word=normalized_word
        )

        ai_service = AIServiceFactory.get_service()
        word_data = await ai_service.generate_word_manual(normalized_word)

        # 4. 保存到数据库
        new_word = Word(
            word=word_data.word,
            phonetic=word_data.phonetic or "",
            part_of_speech=word_data.part_of_speech or "",
            core_game=word_data.core_game,
            scenario_formal=word_data.scenario_formal,
            scenario_casual=word_data.scenario_casual,
            etymology_breakdown=word_data.etymology_breakdown,
            etymology_story=word_data.etymology_story or "",
            memory_trick=word_data.memory_trick,
            common_mistakes=word_data.common_mistakes or "",
            is_golden=False,
            source="ai"
        )
        db.add(new_word)
        await db.commit()
        await db.refresh(new_word)

        # 5. 记录AI生成日志
        await AIGenerationService.log_generation(
            normalized_word, current_user, request, db
        )

        log_with_context(
            logger, "info", "AI generation successful",
            word=normalized_word
        )

        # 6. 检查查询限制并记录
        rate_limiter = RateLimitService(db)
        allowed, used, limit, user_type = await rate_limiter.check_and_record_query(
            word_id=new_word.id,
            user=current_user,
            request=request,
        )

        # 计算剩余查询次数
        remaining_queries = limit - used if limit != -1 else -1

        return WordQueryResponse(
            id=new_word.id,
            word=new_word.word,
            phonetic=new_word.phonetic,
            part_of_speech=new_word.part_of_speech,
            core_game=new_word.core_game,
            scenario_formal=new_word.scenario_formal,
            scenario_casual=new_word.scenario_casual,
            etymology_breakdown=new_word.etymology_breakdown,
            etymology_story=new_word.etymology_story,
            common_mistakes=new_word.common_mistakes,
            memory_trick=new_word.memory_trick,
            is_golden=False,
            remaining_queries=remaining_queries,
        )

    except AIParseError as e:
        log_with_context(
            logger, "warning", "AI response parsing error",
            word=normalized_word, error=str(e)
        )
        # 判断是否是安全过滤器触发的错误
        if "安全过滤器" in str(e) or "safety filter" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "CONTENT_SAFETY_BLOCKED",
                    "message": "该词汇因内容安全政策无法生成，请尝试其他词汇或稍后重试"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "AI_PARSE_ERROR",
                    "message": "AI响应解析失败，请稍后重试"
                }
            )
    except AITimeoutError:
        log_with_context(
            logger, "error", "AI generation timeout",
            word=normalized_word
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "AI_TIMEOUT", "message": "AI生成超时，请稍后重试"}
        )
    except AIRateLimitError:
        log_with_context(
            logger, "error", "AI rate limit",
            word=normalized_word
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "AI_RATE_LIMIT", "message": "AI服务繁忙，请稍后重试"}
        )
    except AIServiceError as e:
        log_with_context(
            logger, "error", "AI service error",
            word=normalized_word, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "AI_ERROR", "message": "AI服务暂时不可用"}
        )


@router.get(
    "/query/{word}",
    response_model=SuccessResponse[WordQueryResponse],
    status_code=status.HTTP_200_OK,
    summary="查询单词（GET路径参数）",
    description="通过URL路径参数查询单词，支持游客模式和注册用户",
)
async def query_word_by_path(
    word: str,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[WordQueryResponse]:
    """
    查询单词（GET方式）- 支持游客和注册用户

    Args:
        word: 要查询的单词（路径参数）
        request: 请求对象（用于获取游客IP）
        current_user: 当前用户（None表示游客）
        db: 数据库会话

    Returns:
        SuccessResponse: 包含单词详细信息和剩余查询次数

    Raises:
        HTTPException: 404 单词不存在
        HTTPException: 400 查询次数用尽
    """
    # 记录路由匹配日志
    user_info = f"user_id={current_user.id}" if current_user else "guest"
    log_with_context(
        logger,
        "info",
        "GET /query/{word} route matched",
        user_info=user_info,
        word_param=word,
        word_length=len(word),
    )

    # 检查是否为非预期的路径参数
    if word in ["contributions", "limit", "health", "docs"]:
        log_with_context(
            logger,
            "warning",
            "Unexpected word parameter - possible routing issue",
            user_info=user_info,
            word_param=word,
            message="This might be a mismatched route. Check if the intended endpoint exists.",
        )

    response_data = await query_word_internal(word, current_user, db, request)
    return SuccessResponse(data=response_data)


@router.post(
    "/query",
    response_model=SuccessResponse[WordQueryResponse],
    status_code=status.HTTP_200_OK,
    summary="查询单词（POST JSON）",
    description="通过POST JSON body查询单词，支持游客模式和注册用户",
)
async def query_word(
    data: WordQueryRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[WordQueryResponse]:
    """
    查询单词（POST方式）- 支持游客和注册用户

    Args:
        data: 查询请求数据
        request: 请求对象（用于获取游客IP）
        current_user: 当前用户（None表示游客）
        db: 数据库会话

    Returns:
        SuccessResponse: 包含单词详细信息和剩余查询次数

    Raises:
        HTTPException: 404 单词不存在
        HTTPException: 400 查询次数用尽
    """
    response_data = await query_word_internal(data.word, current_user, db, request)
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
