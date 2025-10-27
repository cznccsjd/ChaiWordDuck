"""
快速修复验证测试 - 紧急解决方案

验证新架构的核心功能是否正常工作
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.user import User
from app.models.word import Word


@pytest.mark.asyncio
async def test_basic_database_connection(async_session: AsyncSession):
    """测试数据库连接是否正常"""
    # 执行简单查询测试连接
    result = await async_session.execute(text("SELECT 1"))
    assert result.scalar() == 1

    # 测试words表结构是否正确
    result = await async_session.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'words'
        AND column_name IN ('translation', 'language_code', 'core_game_new')
    """))
    columns = result.fetchall()
    column_names = [row[0] for row in columns]

    # 验证新字段存在
    assert 'translation' in column_names
    assert 'language_code' in column_names
    assert 'core_game_new' in column_names


@pytest.mark.asyncio
async def test_new_format_word_creation_and_query(async_session: AsyncSession):
    """测试新格式单词创建和查询"""
    # 清理测试数据
    await async_session.execute(text("DELETE FROM words WHERE word = 'test_accommodation'"))
    await async_session.commit()

    # 创建新格式测试单词
    test_word = Word(
        word="test_accommodation",
        phonetic="[əˌkɒməˈdeɪʃ(ə)n]",
        part_of_speech="noun",
        translation="住宿，适应",
        language_code="zh_CN",
        prompt_version="v1.0",
        is_legacy_format=False,  # 新格式
        core_game="这是一个核心游戏内容",
        scenario_formal="思辨场景",
        scenario_casual="生活场景",
        etymology_breakdown="词根拆解",
        common_mistakes="常见错误",
        memory_trick="记忆技巧",
        is_golden=False,
        source="test",
        # 新格式JSON字段
        core_game_new={"content": "这是新格式的核心游戏内容", "difficulty": "medium"},
        game_boards={
            "board_a_speculative": {
                "type": "棋盘A (思辨场)",
                "name": "学术论坛",
                "example": "学术场景示例"
            },
            "board_b_life": {
                "type": "棋盘B (生活场)",
                "name": "生活场景",
                "example": "生活场景示例"
            }
        },
        etymology_new={
            "breakdown": {
                "prefix": {"part": "ac-", "meaning": "加强"},
                "root": {"part": "commod", "meaning": "适合"},
                "suffix": {"part": "-ation", "meaning": "名词后缀"}
            },
            "story": "词源故事"
        },
        common_mistakes_new={
            "warning": "常见错误警告",
            "avoidance": "避免方法"
        }
    )

    # 保存到数据库
    async_session.add(test_word)
    await async_session.commit()
    await async_session.refresh(test_word)

    # 验证创建成功
    assert test_word.id is not None
    assert test_word.word == "test_accommodation"
    assert test_word.language_code == "zh_CN"
    assert test_word.is_legacy_format == False
    assert test_word.core_game_new is not None
    assert test_word.game_boards is not None

    # 测试数据转换功能
    display_data = test_word.get_display_data('new')
    assert display_data['word'] == 'test_accommodation'
    assert display_data['language_code'] == 'zh_CN'
    assert display_data['core_game']['content'] == "这是新格式的核心游戏内容"
    assert display_data['game_boards']['board_a_speculative']['name'] == "学术论坛"

    # 清理测试数据
    await async_session.delete(test_word)
    await async_session.commit()


@pytest.mark.asyncio
async def test_word_converter_functionality():
    """测试WordDataConverter功能"""
    from app.models.word_converter import WordDataConverter

    # 测试支持的语言列表
    languages = WordDataConverter.SUPPORTED_LANGUAGES
    assert 'zh_CN' in languages
    assert 'en' in languages

    # 测试语言检测
    zh_code = WordDataConverter.detect_language("中文内容", "zh_CN")
    assert zh_code == "zh_CN"

    en_code = WordDataConverter.detect_language("English content", "en")
    assert en_code == "en"


@pytest.mark.asyncio
async def test_prompt_manager_basic_functionality():
    """测试Prompt管理器基本功能"""
    from app.prompts.manager import PromptManager

    # 测试配置加载
    config = PromptManager.get_config()
    assert config is not None

    # 测试模板获取
    template = PromptManager.get_template("word_generation", "gemini", "zh_CN")
    assert template is not None

    # 测试渲染器获取
    renderer = PromptManager.get_renderer("word_generation", "gemini", "zh_CN")
    assert renderer is not None


@pytest.mark.asyncio
async def test_api_basic_health(client: AsyncClient):
    """测试API基本健康状态"""
    # 测试健康检查
    response = await client.get("/api/v1/auth/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_multilang_user_preferences(client: AsyncClient, async_session: AsyncSession):
    """测试多语言用户偏好设置"""
    # 创建测试用户
    test_user = User(
        email="multilang_test@example.com",
        username="multilang_test",
        hashed_password="$2b$12$test_hash",
        is_active=True,
        is_verified=True,
        preferred_language="zh_CN"
    )

    try:
        async_session.add(test_user)
        await async_session.commit()
        await async_session.refresh(test_user)

        # 模拟登录并获取token（简化版本）
        # 这里主要验证用户偏好功能不报错
        from app.services.user_preferences import get_effective_language

        # 测试有效语言偏好
        effective_lang = get_effective_language(test_user, "zh_CN")
        assert effective_lang == "zh_CN"

        # 测试默认语言偏好
        default_lang = get_effective_language(test_user, None)
        assert default_lang == "zh_CN"

    finally:
        # 清理测试数据
        if test_user.id:
            await async_session.delete(test_user)
            await async_session.commit()


if __name__ == "__main__":
    # 可以单独运行此文件进行快速验证
    print("运行快速修复验证测试...")
    print("请使用: pdm run pytest tests/test_quick_fix_verification.py -v")