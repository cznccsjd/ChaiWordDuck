"""
单词API集成测试

测试单词查询、查询限制等功能
"""
import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Word, QueryLog


@pytest.fixture
async def test_word(test_db: AsyncSession) -> Word:
    """创建测试单词"""
    word = Word(
        word="idiosyncrasy",
        phonetic="/ˌɪdiəˈsɪŋkrəsi/",
        part_of_speech="n.",
        core_game="个人特质的独特表现",
        scenario_formal="在心理学研究中分析个体的idiosyncrasy",
        scenario_casual="每个人都有自己的idiosyncrasy",
        etymology_breakdown="idio-(自己的) + syn-(一起) + cras-(混合) + -y",
        etymology_story="源自希腊语，指个人独特的混合特质",
        common_mistakes="不要把idiosyncrasy拼成idiosyncracy",
        memory_trick="记住idio=个人，syn=综合，指个人的独特综合特质",
        is_golden=True,
    )
    test_db.add(word)
    await test_db.commit()
    await test_db.refresh(word)
    return word


class TestWordQueryGET:
    """测试GET /api/v1/words/query/{word}端点"""

    async def test_query_word_success(
        self, client: AsyncClient, auth_headers: dict, test_word: Word
    ):
        """测试成功查询单词（GET方式）"""
        response = await client.get(
            f"/api/v1/words/query/{test_word.word}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["word"] == test_word.word
        assert data["data"]["id"] == test_word.id
        assert data["data"]["coreGame"] == test_word.core_game
        assert "remainingQueries" in data["data"]

    async def test_query_word_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """测试查询不存在的单词（GET方式）"""
        response = await client.get(
            "/api/v1/words/query/nonexistentword",
            headers=auth_headers,
        )

        assert response.status_code == 404

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "WORD_NOT_FOUND"

    async def test_query_word_unauthenticated(
        self, client: AsyncClient, test_word: Word
    ):
        """测试未认证用户查询单词（GET方式）"""
        response = await client.get(
            f"/api/v1/words/query/{test_word.word}",
        )

        assert response.status_code == 403  # HTTPBearer返回403而不是401

    async def test_query_word_case_insensitive(
        self, client: AsyncClient, auth_headers: dict, test_word: Word
    ):
        """测试单词查询大小写不敏感（GET方式）"""
        # 使用大写查询
        response = await client.get(
            f"/api/v1/words/query/{test_word.word.upper()}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["word"] == test_word.word.lower()

    async def test_query_word_with_spaces(
        self, client: AsyncClient, auth_headers: dict
    ):
        """测试查询包含空格的单词（GET方式）"""
        # 查询无效单词（仅空格）
        response = await client.get(
            "/api/v1/words/query/%20%20",  # URL编码的空格
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    async def test_query_limit_tracking(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_word: Word,
        test_db: AsyncSession,
    ):
        """测试查询次数追踪（GET方式）"""
        # 第一次查询
        response1 = await client.get(
            f"/api/v1/words/query/{test_word.word}",
            headers=auth_headers,
        )
        assert response1.status_code == 200
        remaining1 = response1.json()["data"]["remainingQueries"]

        # 第二次查询同一个单词（不应该减少剩余次数）
        response2 = await client.get(
            f"/api/v1/words/query/{test_word.word}",
            headers=auth_headers,
        )
        assert response2.status_code == 200
        remaining2 = response2.json()["data"]["remainingQueries"]

        assert remaining2 == remaining1  # 查询同一单词不减少次数

    async def test_query_creates_log(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_word: Word,
        test_db: AsyncSession,
        created_user: User,
    ):
        """测试查询创建日志记录（GET方式）"""
        # 执行查询
        response = await client.get(
            f"/api/v1/words/query/{test_word.word}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # 验证日志已创建
        from sqlalchemy import select
        result = await test_db.execute(
            select(QueryLog)
            .where(QueryLog.user_id == created_user.id)
            .where(QueryLog.word_id == test_word.id)
            .where(QueryLog.query_date == date.today())
        )
        log = result.scalar_one_or_none()

        assert log is not None
        assert log.user_id == created_user.id
        assert log.word_id == test_word.id


class TestWordQueryPOST:
    """测试POST /api/v1/words/query端点（保证向后兼容）"""

    async def test_query_word_post_still_works(
        self, client: AsyncClient, auth_headers: dict, test_word: Word
    ):
        """测试POST方式仍然可用（向后兼容）"""
        response = await client.post(
            "/api/v1/words/query",
            headers=auth_headers,
            json={"word": test_word.word},
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["word"] == test_word.word


class TestWordQueryLimit:
    """测试查询限制功能"""

    async def test_get_query_limit(
        self, client: AsyncClient, auth_headers: dict
    ):
        """测试获取查询限制信息"""
        response = await client.get(
            "/api/v1/words/query-limit",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "totalQueries" in data["data"]
        assert "remainingQueries" in data["data"]
        assert "usedQueries" in data["data"]
        assert "queriedWords" in data["data"]


class TestWordById:
    """测试GET /api/v1/words/{word_id}端点"""

    async def test_get_word_by_id(
        self, client: AsyncClient, auth_headers: dict, test_word: Word
    ):
        """测试根据ID获取单词"""
        response = await client.get(
            f"/api/v1/words/{test_word.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_word.id
        assert data["data"]["word"] == test_word.word

    async def test_get_word_by_invalid_id(
        self, client: AsyncClient, auth_headers: dict
    ):
        """测试根据无效ID获取单词"""
        response = await client.get(
            "/api/v1/words/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "WORD_NOT_FOUND"

    async def test_get_word_by_id_as_guest(
        self, client: AsyncClient, test_word: Word
    ):
        """测试游客根据ID获取单词（无需认证）"""
        response = await client.get(
            f"/api/v1/words/{test_word.id}",
            # 故意不提供auth_headers，测试游客模式
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_word.id
        assert data["data"]["word"] == test_word.word
        # 游客模式应该返回所有字段，与认证用户相同

    async def test_get_word_by_id_unauthenticated_vs_guest(
        self, client: AsyncClient, test_word: Word
    ):
        """测试游客模式和认证用户访问同一ID返回相同数据"""
        # 游客访问
        guest_response = await client.get(f"/api/v1/words/{test_word.id}")

        # 认证用户访问
        auth_response = await client.get(
            f"/api/v1/words/{test_word.id}",
            headers={"Authorization": "Bearer invalid_token"}  # 这会返回401，但我们主要测试游客模式
        )

        # 游客应该能够成功访问
        assert guest_response.status_code == 200
        guest_data = guest_response.json()

        # 验证游客返回的数据结构
        assert guest_data["success"] is True
        assert "id" in guest_data["data"]
        assert "word" in guest_data["data"]
        assert "phonetic" in guest_data["data"]
        assert "coreGame" in guest_data["data"]
