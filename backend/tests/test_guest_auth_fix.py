"""
游客模式认证修复测试

测试验证 /api/v1/words/{word_id} 端点是否支持游客模式访问
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.word import Word


class TestGuestModeAuthFix:
    """游客模式认证修复测试类"""

    @pytest.mark.asyncio
    async def test_guest_can_get_word_by_id_without_auth(self, client: AsyncClient, test_db: AsyncSession):
        """
        测试游客可以在没有认证的情况下通过ID获取单词详情

        这是修复的核心测试用例，验证：
        1. 游客访问 /api/v1/words/{word_id} 返回200而不是401
        2. 返回的单词数据格式正确
        """
        # 创建测试单词
        test_word = Word(
            word="testauth",
            phonetic="testauth",
            part_of_speech="noun",
            core_game="测试游戏",
            scenario_formal="正式场景",
            scenario_casual="非正式场景",
            etymology_breakdown="词源分解",
            etymology_story="词源故事",
            memory_trick="记忆技巧",
            common_mistakes="常见错误",
            is_golden=False
        )
        test_db.add(test_word)
        await test_db.commit()
        await test_db.refresh(test_word)

        # 游客访问单词详情（不提供Authorization header）
        response = await client.get(f"/api/v1/words/{test_word.id}")

        # 验证响应状态码
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # 验证响应结构
        data = response.json()
        assert data["success"] is True
        assert "data" in data

        # 验证单词数据（使用别名后的字段名）
        word_data = data["data"]
        assert word_data["id"] == test_word.id
        assert word_data["word"] == "testauth"
        assert word_data["coreGame"] == "测试游戏"
        assert word_data["createdAt"] is not None

    @pytest.mark.asyncio
    async def test_guest_gets_404_for_nonexistent_word(self, client: AsyncClient):
        """
        测试游客访问不存在的单词ID时返回404而不是401

        这确保认证逻辑正确工作，不会将所有错误都当作认证错误
        """
        response = await client.get("/api/v1/words/99999")

        # 应该返回404（单词不存在）而不是401（认证失败）
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_auth_user_can_still_get_word_by_id(self, client: AsyncClient, test_db: AsyncSession, auth_headers: dict):
        """
        测试认证用户仍然可以正常访问单词详情

        这确保修复没有破坏现有功能
        """
        # 创建测试单词
        test_word = Word(
            word="authuser",
            phonetic="authuser",
            part_of_speech="verb",
            core_game="认证用户游戏",
            scenario_formal="正式场景",
            scenario_casual="非正式场景",
            etymology_breakdown="词源分解",
            etymology_story="词源故事",
            memory_trick="记忆技巧",
            common_mistakes="常见错误",
            is_golden=False
        )
        test_db.add(test_word)
        await test_db.commit()
        await test_db.refresh(test_word)

        # 认证用户访问单词详情
        response = await client.get(f"/api/v1/words/{test_word.id}", headers=auth_headers)

        # 验证响应状态码
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # 验证响应结构
        data = response.json()
        assert data["success"] is True
        word_data = data["data"]
        assert word_data["word"] == "authuser"

    @pytest.mark.asyncio
    async def test_guest_and_auth_get_same_word_data(self, client: AsyncClient, test_db: AsyncSession, auth_headers: dict):
        """
        测试游客和认证用户获取同一单词的数据相同

        这确保单词数据访问权限正确
        """
        # 创建测试单词
        test_word = Word(
            word="compare",
            phonetic="compare",
            part_of_speech="adjective",
            core_game="比较游戏",
            scenario_formal="正式场景",
            scenario_casual="非正式场景",
            etymology_breakdown="词源分解",
            etymology_story="词源故事",
            memory_trick="记忆技巧",
            common_mistakes="常见错误",
            is_golden=False
        )
        test_db.add(test_word)
        await test_db.commit()
        await test_db.refresh(test_word)

        # 游客访问
        guest_response = await client.get(f"/api/v1/words/{test_word.id}")

        # 认证用户访问
        auth_response = await client.get(f"/api/v1/words/{test_word.id}", headers=auth_headers)

        # 验证两个响应都成功
        assert guest_response.status_code == 200
        assert auth_response.status_code == 200

        # 验证返回的数据相同（使用别名后的字段名）
        guest_data = guest_response.json()["data"]
        auth_data = auth_response.json()["data"]

        assert guest_data["id"] == auth_data["id"]
        assert guest_data["word"] == auth_data["word"]
        assert guest_data["coreGame"] == auth_data["coreGame"]
        assert guest_data["phonetic"] == auth_data["phonetic"]

    @pytest.mark.asyncio
    async def test_invalid_token_does_not_prevent_guest_access(self, client: AsyncClient, test_db: AsyncSession):
        """
        测试无效token不会阻止游客访问

        这验证get_optional_user的正确行为：无效token时降级为游客模式
        """
        # 创建测试单词
        test_word = Word(
            word="invalidtoken",
            phonetic="invalidtoken",
            part_of_speech="noun",
            core_game="无效令牌游戏",
            scenario_formal="正式场景",
            scenario_casual="非正式场景",
            etymology_breakdown="词源分解",
            etymology_story="词源故事",
            memory_trick="记忆技巧",
            common_mistakes="常见错误",
            is_golden=False
        )
        test_db.add(test_word)
        await test_db.commit()
        await test_db.refresh(test_word)

        # 使用无效token访问
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = await client.get(f"/api/v1/words/{test_word.id}", headers=headers)

        # 应该成功访问（降级为游客模式）
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["success"] is True
        assert data["data"]["word"] == "invalidtoken"


if __name__ == "__main__":
    # 运行测试的说明
    print("""
    运行游客模式认证修复测试：

    # 运行所有相关测试
    pdm run pytest tests/test_guest_auth_fix.py -v

    # 运行特定测试
    pdm run pytest tests/test_guest_auth_fix.py::TestGuestModeAuthFix::test_guest_can_get_word_by_id_without_auth -v

    # 查看测试覆盖率
    pdm run pytest tests/test_guest_auth_fix.py --cov=app.api.v1.words --cov-report=html
    """)