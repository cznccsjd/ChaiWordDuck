"""
游客语言检测完整测试

测试游客模式下的语言自动检测功能，包括：
- Accept-Language头部解析
- Cookie语言偏好读取
- 语言降级机制
- 优先级处理
- 边界情况和错误处理
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.ai.base import WordManualData
from app.services.guest_preferences import (
    get_guest_language_preference,
    get_effective_language_for_guest,
    get_language_from_accept_language,
    get_language_from_cookie,
    normalize_accept_language_code
)


class TestGuestLanguageDetection:
    """游客语言检测测试"""

    @pytest.fixture
    def mock_word_data_chinese(self):
        """模拟中文单词数据"""
        return WordManualData(
            word="welcome",
            phonetic="[ˈwelkəm]",
            part_of_speech="interjection",
            core_game="欢迎游戏：通过欢迎仪式学习英语问候",
            scenario_formal="正式场景：Welcome to our company. 欢迎来到我们公司。",
            scenario_casual="日常场景：Welcome! Come on in. 欢迎！快进来。",
            etymology_breakdown="词源拆解：welcome来自will + come",
            etymology_story="词源故事：welcome表示希望某人到来",
            memory_trick="记忆技巧：well(好) + come(来) = 欢迎",
            common_mistakes="常见错误：注意不要写成welcom"
        )

    @pytest.fixture
    def mock_word_data_english(self):
        """模拟英文单词数据"""
        return WordManualData(
            word="welcome",
            phonetic="[ˈwelkəm]",
            part_of_speech="interjection",
            core_game="Welcome game: Learn greetings through welcoming rituals",
            scenario_formal="Formal scenario: Welcome to our company.",
            scenario_casual="Casual scenario: Welcome! Come on in.",
            etymology_breakdown="Etymology: welcome from will + come",
            etymology_story="Etymology story: welcome expresses hope for someone's arrival",
            memory_trick="Memory trick: well(good) + come(arrive) = welcome",
            common_mistakes="Common mistakes: don't write welcom"
        )

    async def test_guest_language_detection_accept_language_priority(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_english
    ):
        """测试游客通过Accept-Language头部检测语言的优先级"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_english
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 测试英文优先级
                    headers = {"Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8"}
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome"},
                        headers=headers
                    )
                    assert response.status_code == 200
                    assert "Welcome game" in response.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("welcome", language="en_US")

    async def test_guest_language_detection_chinese_priority(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_chinese
    ):
        """测试游客中文语言检测"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_chinese
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 测试中文优先级
                    headers = {"Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8"}
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome"},
                        headers=headers
                    )
                    assert response.status_code == 200
                    assert "欢迎游戏" in response.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("welcome", language="zh_CN")

    async def test_guest_language_detection_cookie_override(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_chinese
    ):
        """测试Cookie语言设置覆盖Accept-Language"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_chinese
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # Cookie设置为中文，Accept-Language设置为英文
                    headers = {"Accept-Language": "en-US,en;q=0.9"}
                    cookies = {"language": "zh_CN"}
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome"},
                        headers=headers,
                        cookies=cookies
                    )
                    assert response.status_code == 200
                    assert "欢迎游戏" in response.json()["data"]["coreGame"]
                    # Cookie应该优先于Accept-Language
                    mock_service.generate_word_manual.assert_called_with("welcome", language="zh_CN")

    async def test_guest_language_detection_explicit_parameter_priority(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_english
    ):
        """测试显式语言参数的最高优先级"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_english
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 显式参数为英文，Cookie为中文，Accept-Language为中文
                    headers = {"Accept-Language": "zh-CN,zh;q=0.9"}
                    cookies = {"language": "zh_CN"}
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome", "language": "en_US"},
                        headers=headers,
                        cookies=cookies
                    )
                    assert response.status_code == 200
                    assert "Welcome game" in response.json()["data"]["coreGame"]
                    # 显式参数应该优先级最高
                    mock_service.generate_word_manual.assert_called_with("welcome", language="en_US")

    async def test_guest_language_detection_fallback_to_default(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_chinese
    ):
        """测试游客语言检测降级到默认语言"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_chinese
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 没有任何语言信息，应降级到默认语言
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome"}
                    )
                    assert response.status_code == 200
                    # 默认语言应该是中文
                    assert "欢迎游戏" in response.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("welcome", language="zh_CN")

    async def test_guest_language_detection_complex_accept_language(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_english
    ):
        """测试复杂的Accept-Language头部解析"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_english
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 复杂的Accept-Language头部
                    complex_headers = {
                        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6"
                    }
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome"},
                        headers=complex_headers
                    )
                    assert response.status_code == 200
                    # 应该选择英文（en-US），因为法文不支持
                    assert "Welcome game" in response.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("welcome", language="en_US")

    async def test_guest_language_detection_service_layer_functions(self):
        """测试游客语言检测服务层函数"""
        # 1. 测试Accept-Language解析
        en_lang = get_language_from_accept_language("en-US,en;q=0.9")
        assert en_lang == "en_US"

        zh_lang = get_language_from_accept_language("zh-CN,zh;q=0.9")
        assert zh_lang == "zh_CN"

        default_lang = get_language_from_accept_language("")
        assert default_lang in ["zh_CN", "en_US"]  # 默认语言

        # 2. 测试Cookie语言解析
        cookie_en = get_language_from_cookie({"language": "en_US"})
        assert cookie_en == "en_US"

        cookie_empty = get_language_from_cookie({})
        assert cookie_empty in ["zh_CN", "en_US"]  # 默认语言

        # 3. 测试有效语言获取
        headers = {"Accept-Language": "en-US,en;q=0.9"}
        cookies = {"language": "zh_CN"}

        # 优先级测试
        explicit_lang = get_effective_language_for_guest(
            headers=headers, cookies=cookies, explicit_language="en_US"
        )
        assert explicit_lang == "en_US"

        cookie_lang = get_effective_language_for_guest(
            headers=headers, cookies=cookies, explicit_language=None
        )
        assert cookie_lang == "zh_CN"

        header_lang = get_effective_language_for_guest(
            headers=headers, cookies={}, explicit_language=None
        )
        assert header_lang == "en_US"

    async def test_guest_language_detection_normalize_functions(self):
        """测试语言代码标准化函数"""
        # 测试Accept-Language代码标准化
        assert normalize_accept_language_code("zh-cn") == "zh_CN"
        assert normalize_accept_language_code("zh") == "zh_CN"
        assert normalize_accept_language_code("en-us") == "en_US"
        assert normalize_accept_language_code("en") == "en_US"
        assert normalize_accept_language_code("zh-CN") == "zh_CN"
        assert normalize_accept_language_code("en-US") == "en_US"

        # 测试不支持的语言
        assert normalize_accept_language_code("fr") is None
        assert normalize_accept_language_code("de") is None
        assert normalize_accept_language_code("") is None
        assert normalize_accept_language_code("invalid") is None

    async def test_guest_language_detection_edge_cases(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_chinese
    ):
        """测试游客语言检测的边界情况"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_chinese
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 测试各种边界情况
                    edge_cases = [
                        # 格式错误的Accept-Language
                        {"Accept-Language": ""},
                        {"Accept-Language": "invalid"},
                        {"Accept-Language": "zh;q=abc"},
                        {"Accept-Language": "zh;q=2.0"},

                        # 特殊字符和编码
                        {"Accept-Language": "zh-CN;q=0.9,"},
                        {"Accept-Language": ",en-US;q=0.8"},
                        {"Accept-Language": "  en-US  "},

                        # Cookie边界情况
                        {},  # 无Cookie
                        {"language": ""},  # 空Cookie值
                        {"language": "invalid"},  # 无效语言
                        {"other_cookie": "value"},  # 其他Cookie
                    ]

                    for headers in edge_cases:
                        response = await client.post(
                            "/api/v1/words/query",
                            json={"word": "welcome"},
                            headers=headers
                        )
                        # 所有情况都应该成功，并降级到默认语言
                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True

    async def test_guest_language_detection_quality_values(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_chinese, mock_word_data_english
    ):
        """测试Accept-Language质量值处理"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 测试质量值排序：英文q=0.9，中文q=0.8
                    mock_service.generate_word_manual.return_value = mock_word_data_english
                    headers = {"Accept-Language": "zh-CN;q=0.8,en-US;q=0.9"}
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome"},
                        headers=headers
                    )
                    assert response.status_code == 200
                    assert "Welcome game" in response.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("welcome", language="en_US")

                    # 测试质量值排序：中文q=0.9，英文q=0.8
                    mock_service.generate_word_manual.return_value = mock_word_data_chinese
                    headers = {"Accept-Language": "zh-CN;q=0.9,en-US;q=0.8"}
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "welcome"},
                        headers=headers
                    )
                    assert response.status_code == 200
                    assert "欢迎游戏" in response.json()["data"]["coreGame"]
                    mock_service.generate_word_manual.assert_called_with("welcome", language="zh_CN")

    async def test_guest_language_detection_case_insensitivity(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_english
    ):
        """测试语言代码大小写不敏感"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_english
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 测试不同大小写
                    case_variations = [
                        {"Accept-Language": "EN-US,en;q=0.9"},
                        {"Accept-Language": "en-us,en;q=0.9"},
                        {"Accept-Language": "En_Us,en;q=0.9"},
                        {"Accept-Language": "eN_uS,en;q=0.9"},
                    ]

                    for headers in case_variations:
                        response = await client.post(
                            "/api/v1/words/query",
                            json={"word": "welcome"},
                            headers=headers
                        )
                        assert response.status_code == 200
                        assert "Welcome game" in response.json()["data"]["coreGame"]

    async def test_guest_language_detection_concurrent_requests(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_chinese, mock_word_data_english
    ):
        """测试游客语言检测的并发请求处理"""
        import asyncio

        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 准备并发请求
                    async def make_request(headers, cookies, expected_data):
                        mock_service.generate_word_manual.return_value = expected_data
                        response = await client.post(
                            "/api/v1/words/query",
                            json={"word": "welcome"},
                            headers=headers,
                            cookies=cookies
                        )
                        return response

                    tasks = [
                        # 英文Accept-Language
                        make_request(
                            {"Accept-Language": "en-US,en;q=0.9"},
                            {},
                            mock_word_data_english
                        ),
                        # 中文Cookie
                        make_request(
                            {},
                            {"language": "zh_CN"},
                            mock_word_data_chinese
                        ),
                        # 显式英文参数
                        make_request(
                            {"Accept-Language": "zh-CN,zh;q=0.9"},
                            {"language": "zh_CN"},
                            mock_word_data_english
                        ),
                        # 默认语言
                        make_request(
                            {},
                            {},
                            mock_word_data_chinese
                        ),
                    ]

                    responses = await asyncio.gather(*tasks)

                    # 验证所有请求都成功
                    for response in responses:
                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True

    async def test_guest_language_detection_unsupported_languages(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_chinese
    ):
        """测试游客不支持的语言降级"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_chinese
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 测试不支持的语言
                    unsupported_languages = [
                        "fr-FR,fr;q=0.9",  # 法文
                        "de-DE,de;q=0.9",  # 德文
                        "ja-JP,ja;q=0.9",  # 日文
                        "ko-KR,ko;q=0.9",  # 韩文
                        "es-ES,es;q=0.9",  # 西班牙文
                    ]

                    for accept_lang in unsupported_languages:
                        headers = {"Accept-Language": accept_lang}
                        response = await client.post(
                            "/api/v1/words/query",
                            json={"word": "welcome"},
                            headers=headers
                        )
                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True
                        # 应该降级到默认语言（中文）
                        assert "欢迎游戏" in data["data"]["coreGame"]

    async def test_guest_language_detection_persistence_across_requests(
        self, client: AsyncClient, test_db: AsyncSession, mock_word_data_english
    ):
        """测试游客语言检测在多个请求间的一致性"""
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_word_data_english
            mock_get_service.return_value = mock_service

            # Mock rate limiter and AI generation service
            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 5, 10, "guest")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 使用相同的Accept-Language头部进行多次请求
                    headers = {"Accept-Language": "en-US,en;q=0.9"}

                    for i in range(3):
                        response = await client.post(
                            "/api/v1/words/query",
                            json={"word": f"welcome{i}"},
                            headers=headers
                        )
                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True
                        assert "Welcome game" in data["data"]["coreGame"]

                    # 验证每次调用都使用了正确的语言
                    assert mock_service.generate_word_manual.call_count == 3
                    for call in mock_service.generate_word_manual.call_args_list:
                        args, kwargs = call
                        assert kwargs.get("language") == "en_US"