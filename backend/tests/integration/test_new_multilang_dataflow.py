"""
新架构多语言数据流完整集成测试

测试新的多语言Prompt管理系统和嵌套JSON数据结构的完整集成
包含：
1. Prompt渲染 → AI服务 → 数据解析 → 数据存储 → API响应的完整数据流
2. 新旧数据格式向后兼容性测试
3. 多语言Prompt管理器集成测试
4. 数据库JSONB字段存储和查询测试
5. WordDataConverter格式转换测试
6. 错误处理和降级机制测试
7. 性能和并发测试
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.word import Word
from app.services.ai.base import (
    WordManualData, GameBoard, EtymologyBreakdown, Etymology,
    CoreGame, CommonMistakes, GameBoards
)
from app.models.word_converter import WordDataConverter
from app.prompts.enums import Language, AIProvider, PromptType


class TestNewArchitectureDataFlow:
    """新架构数据流完整集成测试"""

    @pytest.fixture
    def mock_new_format_word_data_chinese(self):
        """模拟新格式的中文单词数据（嵌套JSON结构）"""
        return WordManualData(
            word="accommodation",
            phonetic="[əˌkɒməˈdeɪʃ(ə)n]",
            translation="住宿，适应",
            part_of_speech="noun",
            core_game=CoreGame(
                content="这是一个关于'accommodation'的记忆游戏。想象你正在规划一次旅行，需要找到合适的住宿地点。游戏规则是：通过拆解这个单词，记住它的意思和用法。"
            ),
            game_boards=GameBoards(
                board_a_speculative=GameBoard(
                    type="棋盘A (思辨场)",
                    name="学术论坛",
                    example="The university needs to provide suitable accommodation for international students. (大学需要为国际学生提供合适的住宿。)"
                ),
                board_b_life=GameBoard(
                    type="棋盘B (生活场)",
                    name="旅行预订",
                    example="We found affordable accommodation near the beach. (我们在海滩附近找到了实惠的住宿。)"
                )
            ),
            etymology=Etymology(
                breakdown=EtymologyBreakdown(
                    prefix={'part': 'ac-', 'meaning': 'to, toward'},
                    root={'part': 'commodare', 'meaning': 'to make fit, convenient'},
                    suffix={'part': '-ation', 'meaning': 'process, action'}
                ),
                story="这个词源自拉丁语，意思是'使适应'或'使便利'。最初用来描述适应某人需求的行为，现在主要用于指代住宿的地方。"
            ),
            common_mistakes=CommonMistakes(
                warning="最容易犯的错误：忘记双写字母'cc'和'mm'。正确拼写是a-cc-o-mm-o-d-a-t-i-o-n，不是a-com-o-dation。",
                avoidance="记忆技巧：住宿(accommodation)需要两个床(mm)和两个房间(cc)，所以要双写！"
            ),
            memory_trick="通关秘籍：把accommodation拆解成：ac(去) + commod(便利) + ation(过程) = 去找便利的住宿过程"
        )

    @pytest.fixture
    def mock_new_format_word_data_english(self):
        """模拟新格式的英文单词数据（嵌套JSON结构）"""
        return WordManualData(
            word="accommodation",
            phonetic="[əˌkɒməˈdeɪʃ(ə)n]",
            translation="lodging, adaptation",
            part_of_speech="noun",
            core_game=CoreGame(
                content="This is a memory game about 'accommodation'. Imagine you're planning a trip and need to find suitable lodging. The game rule is: remember the meaning and usage by deconstructing this word."
            ),
            game_boards=GameBoards(
                board_a_speculative=GameBoard(
                    type="Board A (Academic)",
                    name="Academic Forum",
                    example="The university needs to provide suitable accommodation for international students."
                ),
                board_b_life=GameBoard(
                    type="Board B (Daily Life)",
                    name="Travel Booking",
                    example="We found affordable accommodation near the beach."
                )
            ),
            etymology=Etymology(
                breakdown=EtymologyBreakdown(
                    prefix={'part': 'ac-', 'meaning': 'to, toward'},
                    root={'part': 'commodare', 'meaning': 'to make fit, convenient'},
                    suffix={'part': '-ation', 'meaning': 'process, action'}
                ),
                story="This word comes from Latin, meaning 'to make fit' or 'convenient'. Originally described the act of adapting to someone's needs, now mainly refers to lodging places."
            ),
            common_mistakes=CommonMistakes(
                warning="Most common mistake: forgetting to double the letters 'cc' and 'mm'. Correct spelling is a-cc-o-mm-o-d-a-t-i-o-n, not a-com-o-dation.",
                avoidance="Memory trick: accommodation needs two beds(mm) and two rooms(cc), so double them!"
            ),
            memory_trick="Level clear secret: Break down accommodation into: ac(to) + commod(convenient) + ation(process) = the process of finding convenient lodging"
        )

    async def test_complete_new_format_dataflow_chinese(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession, mock_new_format_word_data_chinese
    ):
        """测试完整的新格式中文数据流：Prompt → AI → 数据库 → API"""

        # 1. 设置用户语言偏好为中文
        await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "zh_CN"},
            headers=auth_headers
        )

        # 2. Mock AI服务和相关服务
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_new_format_word_data_chinese
            mock_get_service.return_value = mock_service

            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 1, 10, "free")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 3. 查询单词（触发新格式生成）
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "accommodation"},
                        headers=auth_headers
                    )

                    # 4. 验证API响应
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    word_data = data["data"]

                    assert word_data["word"] == "accommodation"
                    assert word_data["translation"] == "住宿，适应"
                    assert "住宿" in word_data["coreGame"]

                    # 5. 验证AI服务调用参数
                    mock_service.generate_word_manual.assert_called_once_with("accommodation", language="zh_CN")

                    # 6. 验证数据库存储
                    result = await test_db.execute(
                        select(Word).where(Word.word == "accommodation")
                    )
                    db_word = result.scalar_one()

                    assert db_word.word == "accommodation"
                    assert db_word.translation == "住宿，适应"
                    assert db_word.language_code == "zh_CN"
                    assert db_word.is_legacy_format is False  # 确认是新格式
                    assert db_word.prompt_version == "v2.0"

                    # 7. 验证JSONB字段存储
                    assert db_word.core_game_new is not None
                    assert db_word.game_boards is not None
                    assert db_word.etymology_new is not None
                    assert db_word.common_mistakes_new is not None

                    # 验证嵌套结构
                    core_game = db_word.core_game_new
                    assert "content" in core_game
                    assert "记忆游戏" in core_game["content"]

                    game_boards = db_word.game_boards
                    assert "board_a_speculative" in game_boards
                    assert "board_b_life" in game_boards
                    assert game_boards["board_a_speculative"]["name"] == "学术论坛"

    async def test_complete_new_format_dataflow_english(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession, mock_new_format_word_data_english
    ):
        """测试完整的新格式英文数据流"""

        # 1. 设置用户语言偏好为英文
        await client.put(
            "/api/v1/users/preferences",
            json={"preferred_language": "en_US"},
            headers=auth_headers
        )

        # 2. Mock AI服务
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_new_format_word_data_english
            mock_get_service.return_value = mock_service

            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 1, 10, "free")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 3. 查询单词
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "accommodation"},
                        headers=auth_headers
                    )

                    # 4. 验证响应
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    word_data = data["data"]

                    assert word_data["word"] == "accommodation"
                    assert word_data["translation"] == "lodging, adaptation"

                    # 5. 验证AI服务调用
                    mock_service.generate_word_manual.assert_called_once_with("accommodation", language="en_US")

    async def test_new_format_prompt_manager_integration(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession, mock_new_format_word_data_chinese
    ):
        """测试新格式Prompt管理器集成"""

        # Mock AI服务，但保留真实的Prompt管理器
        with patch('app.services.ai.gemini_service.genai.Client') as mock_genai_client:
            # Mock Gemini客户端
            mock_client_instance = Mock()
            mock_genai_client.return_value = mock_client_instance

            # Mock API响应
            mock_response = Mock()
            mock_response.text = json.dumps({
                "word": "accommodation",
                "phonetic": "[əˌkɒməˈdeɪʃ(ə)n]",
                "translation": "住宿，适应",
                "part_of_speech": "noun",
                "core_game": {
                    "content": "记忆游戏内容"
                },
                "game_boards": {
                    "board_a_speculative": {
                        "type": "棋盘A (思辨场)",
                        "name": "学术论坛",
                        "example": "示例句子"
                    },
                    "board_b_life": {
                        "type": "棋盘B (生活场)",
                        "name": "旅行预订",
                        "example": "示例句子"
                    }
                },
                "etymology": {
                    "breakdown": {
                        "prefix": {"part": "ac-", "meaning": "to, toward"},
                        "root": {"part": "commodare", "meaning": "to make fit"},
                        "suffix": {"part": "-ation", "meaning": "process"}
                    },
                    "story": "词源故事"
                },
                "common_mistakes": {
                    "warning": "常见错误警告",
                    "avoidance": "避免错误的方法"
                },
                "memory_trick": "记忆技巧"
            })
            mock_client_instance.models.generate_content.return_value = mock_response

            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 1, 10, "free")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 2. 查询单词
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "accommodation"},
                        headers=auth_headers
                    )

                    # 3. 验证成功响应
                    assert response.status_code == 200

                    # 4. 验证Gemini API被调用
                    mock_client_instance.models.generate_content.assert_called_once()

                    # 5. 验证调用的参数
                    call_args = mock_client_instance.models.generate_content.call_args
                    assert call_args[1]['model'] is not None

                    # 验证system instruction和user prompt
                    config = call_args[1]['config']
                    assert config.system_instruction is not None
                    assert "application/json" in config.response_mime_type
                    assert config.response_schema is not None

    async def test_word_data_converter_new_format_integration(
        self, test_db: AsyncSession, mock_new_format_word_data_chinese
    ):
        """测试WordDataConverter新格式集成"""

        # 1. 创建新格式的Word对象
        word_data_dict = mock_new_format_word_data_chinese.model_dump()
        converted_data = WordDataConverter.convert_ai_response_to_word(
            word_data_dict,
            language_code="zh_CN",
            source="ai"
        )

        # 2. 验证转换结果
        assert converted_data["word"] == "accommodation"
        assert converted_data["translation"] == "住宿，适应"
        assert converted_data["language_code"] == "zh_CN"
        assert converted_data["prompt_version"] == "v2.0"
        assert converted_data["is_legacy_format"] is False

        # 3. 验证JSONB字段
        assert converted_data["core_game_new"] is not None
        assert converted_data["game_boards"] is not None
        assert converted_data["etymology_new"] is not None
        assert converted_data["common_mistakes_new"] is not None

        # 4. 创建数据库记录
        word = Word(**converted_data)
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        # 5. 验证数据库存储
        assert word.word == "accommodation"
        assert word.is_legacy_format is False
        assert word.core_game_new is not None

        # 6. 测试向后兼容方法
        display_data = word.get_display_data('auto')
        assert display_data["word"] == "accommodation"
        assert display_data["translation"] == "住宿，适应"
        assert display_data["is_legacy_format"] is False

        # 7. 测试新格式方法
        assert word.is_new_format() is True
        core_content = word.get_core_game_content()
        assert "记忆游戏" in core_content

        game_boards_data = word.get_game_boards_data()
        assert "board_a_speculative" in game_boards_data
        assert game_boards_data["board_a_speculative"]["name"] == "学术论坛"

    async def test_backward_compatibility_legacy_format_still_works(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试向后兼容性：旧格式数据仍然正常工作"""

        # 1. 手动创建旧格式的Word记录
        legacy_word = Word(
            word="legacy",
            phonetic="[ˈledʒəsi]",
            part_of_speech="noun",
            core_game="旧格式核心游戏内容",
            scenario_formal="旧格式正式场景",
            scenario_casual="旧格式日常场景",
            etymology_breakdown="旧格式词源拆解",
            etymology_story="旧格式词源故事",
            common_mistakes="旧格式常见错误",
            memory_trick="旧格式记忆技巧",
            is_golden=False,
            source="manual",
            is_legacy_format=True,  # 明确标记为旧格式
            language_code="en",
            prompt_version="v1.0"
        )
        test_db.add(legacy_word)
        await test_db.commit()
        await test_db.refresh(legacy_word)

        # 2. 查询旧格式单词
        response = await client.post(
            "/api/v1/words/query",
            json={"word": "legacy"},
            headers=auth_headers
        )

        # 3. 验证成功响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        word_data = data["data"]

        assert word_data["word"] == "legacy"
        assert word_data["coreGame"] == "旧格式核心游戏内容"
        assert word_data["scenarioFormal"] == "旧格式正式场景"
        assert word_data["scenarioCasual"] == "旧格式日常场景"

        # 4. 验证Word对象的向后兼容方法
        display_data = legacy_word.get_display_data('auto')
        assert display_data["is_legacy_format"] is True
        assert display_data["core_game"]["content"] == "旧格式核心游戏内容"

        # 5. 验证旧格式兼容方法
        assert legacy_word.is_new_format() is False
        core_content = legacy_word.get_core_game_content()
        assert core_content == "旧格式核心游戏内容"

        game_boards_data = legacy_word.get_game_boards_data()
        assert game_boards_data["board_a_speculative"]["example"] == "旧格式正式场景"
        assert game_boards_data["board_b_life"]["example"] == "旧格式日常场景"

    async def test_new_format_automatic_detection_and_storage(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession, mock_new_format_word_data_chinese
    ):
        """测试新格式自动检测和存储"""

        # 1. Mock AI服务返回新格式数据
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_new_format_word_data_chinese
            mock_get_service.return_value = mock_service

            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 1, 10, "free")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 2. 生成新格式单词
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "newformat"},
                        headers=auth_headers
                    )

                    assert response.status_code == 200

                    # 3. 验证数据库自动存储为新格式
                    result = await test_db.execute(
                        select(Word).where(Word.word == "newformat")
                    )
                    db_word = result.scalar_one()

                    # 验证新格式标识
                    assert db_word.is_legacy_format is False
                    assert db_word.prompt_version == "v2.0"
                    assert db_word.language_code == "zh_CN"

                    # 验证JSONB字段已填充
                    assert db_word.core_game_new is not None
                    assert db_word.game_boards is not None
                    assert db_word.etymology_new is not None
                    assert db_word.common_mistakes_new is not None

                    # 4. 验证兼容字段也有值（为了API响应兼容性）
                    assert db_word.core_game == mock_new_format_word_data_chinese.core_game.content
                    assert db_word.scenario_formal == mock_new_format_word_data_chinese.game_boards.board_a_speculative.example
                    assert db_word.scenario_casual == mock_new_format_word_data_chinese.game_boards.board_b_life.example

    async def test_database_query_performance_new_format(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession, mock_new_format_word_data_chinese
    ):
        """测试新格式的数据库查询性能"""

        # 1. 创建多个新格式单词记录
        words = []
        for i in range(10):
            word_data = WordDataConverter.convert_ai_response_to_word(
                mock_new_format_word_data_chinese.model_dump(),
                language_code="zh_CN",
                source="ai"
            )
            word_data["word"] = f"word{i}"
            word = Word(**word_data)
            test_db.add(word)
            words.append(word)

        await test_db.commit()

        # 2. 测试查询性能
        import time
        start_time = time.time()

        # 批量查询
        result = await test_db.execute(
            select(Word).where(Word.is_legacy_format == False)
        )
        new_format_words = result.scalars().all()

        end_time = time.time()
        query_time = end_time - start_time

        # 3. 验证查询结果和性能
        assert len(new_format_words) == 10
        assert query_time < 1.0  # 查询应该在1秒内完成

        # 4. 验证JSONB字段查询
        for word in new_format_words:
            assert word.core_game_new is not None
            assert isinstance(word.core_game_new, dict)
            assert "content" in word.core_game_new

    async def test_format_migration_functionality(
        self, test_db: AsyncSession
    ):
        """测试格式迁移功能"""

        # 1. 创建旧格式单词
        legacy_word = Word(
            word="migrate",
            phonetic="[maɪˈɡreɪt]",
            part_of_speech="verb",
            core_game="旧格式核心游戏",
            scenario_formal="旧格式正式场景",
            scenario_casual="旧格式日常场景",
            etymology_breakdown="旧格式词源",
            etymology_story="旧格式故事",
            common_mistakes="旧格式错误",
            memory_trick="旧格式技巧",
            is_golden=False,
            source="manual",
            is_legacy_format=True,
            language_code="en",
            prompt_version="v1.0"
        )
        test_db.add(legacy_word)
        await test_db.commit()
        await test_db.refresh(legacy_word)

        # 2. 执行迁移
        migrated_word = WordDataConverter.migrate_legacy_word(test_db, legacy_word.id)
        assert migrated_word is not None

        # 3. 验证迁移结果
        assert migrated_word.is_legacy_format is False
        assert migrated_word.prompt_version == "v1.0"  # 保持原版本
        assert migrated_word.core_game_new is not None
        assert migrated_word.game_boards is not None
        assert migrated_word.etymology_new is not None
        assert migrated_word.common_mistakes_new is not None

        # 4. 验证数据完整性
        display_data = migrated_word.get_display_data('auto')
        assert display_data["core_game"]["content"] == "旧格式核心游戏"
        assert display_data["game_boards"]["board_a_speculative"]["example"] == "旧格式正式场景"


class TestNewArchitectureErrorHandling:
    """新架构错误处理测试"""

    async def test_new_format_parsing_error_handling(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试新格式解析错误的处理"""

        # Mock AI服务返回无效的嵌套结构
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()

            # 创建缺少必要字段的无效数据
            invalid_data = WordManualData(
                word="test",
                phonetic="[test]",
                translation="测试",
                part_of_speech="noun",
                core_game=CoreGame(content=""),
                game_boards=GameBoards(
                    board_a_speculative=GameBoard(
                        type="Board A",
                        name="Test",
                        example=""
                    ),
                    board_b_life=GameBoard(
                        type="Board B",
                        name="Test",
                        example=""
                    )
                ),
                etymology=Etymology(
                    breakdown=EtymologyBreakdown(
                        prefix={'part': '', 'meaning': ''},
                        root={'part': '', 'meaning': ''},
                        suffix={'part': '', 'meaning': ''}
                    ),
                    story=""
                ),
                common_mistakes=CommonMistakes(
                    warning="",
                    avoidance=""
                ),
                memory_trick=""
            )
            mock_service.generate_word_manual.return_value = invalid_data
            mock_get_service.return_value = mock_service

            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 1, 10, "free")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 2. 查询应该成功但处理空值
                    response = await client.post(
                        "/api/v1/words/query",
                        json={"word": "test"},
                        headers=auth_headers
                    )

                    # 3. 应该能处理空值而不崩溃
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True

    async def test_prompt_manager_fallback_mechanism(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession
    ):
        """测试Prompt管理器降级机制"""

        # 1. Mock Prompt管理器配置失败
        with patch('app.prompts.manager.PromptManager._load_config') as mock_load:
            mock_load.side_effect = Exception("Config load failed")

            # 2. 重新获取Prompt管理器（应该使用降级配置）
            from app.prompts.manager import PromptManager
            prompt_manager = PromptManager()

            # 3. 验证降级配置工作
            config_info = prompt_manager.get_config_info()
            assert "fallback" in config_info["metadata"]["version"]

            # 4. 测试降级情况下的Prompt渲染
            system_prompt, user_prompt = prompt_manager.render_prompt("test", "zh_CN")
            assert system_prompt is not None
            assert user_prompt is not None
            assert "test" in user_prompt

    async def test_concurrent_new_format_generation(
        self, client: AsyncClient, created_user: User, auth_headers: dict,
        test_db: AsyncSession, mock_new_format_word_data_chinese
    ):
        """测试并发新格式生成"""

        # Mock AI服务
        with patch('app.services.ai.factory.AIServiceFactory.get_service') as mock_get_service:
            mock_service = Mock()
            mock_service.generate_word_manual.return_value = mock_new_format_word_data_chinese
            mock_get_service.return_value = mock_service

            with patch('app.api.v1.words.RateLimitService') as mock_rate_limiter:
                mock_rate_limiter_instance = Mock()
                mock_rate_limiter_instance.check_and_record_query = AsyncMock(
                    return_value=(True, 1, 10, "free")
                )
                mock_rate_limiter.return_value = mock_rate_limiter_instance

                with patch('app.api.v1.words.AIGenerationService') as mock_ai_gen:
                    mock_ai_gen.check_generation_limit = AsyncMock(return_value=None)
                    mock_ai_gen.log_generation = AsyncMock()

                    # 2. 并发查询多个不同单词
                    async def query_word(word_name: str):
                        response = await client.post(
                            "/api/v1/words/query",
                            json={"word": word_name},
                            headers=auth_headers
                        )
                        return response

                    tasks = [
                        query_word(f"word{i}")
                        for i in range(5)
                    ]

                    responses = await asyncio.gather(*tasks)

                    # 3. 验证所有请求都成功
                    for i, response in enumerate(responses):
                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True
                        assert data["data"]["word"] == f"word{i}"

                    # 4. 验证数据库中有正确数量的记录
                    result = await test_db.execute(
                        select(Word).where(Word.word.like("word%"))
                    )
                    db_words = result.scalars().all()
                    assert len(db_words) == 5

                    # 5. 验证所有记录都是新格式
                    new_format_count = sum(1 for word in db_words if not word.is_legacy_format)
                    assert new_format_count == 5


class TestNewArchitectureDataValidation:
    """新架构数据验证测试"""

    async def test_jsonb_data_structure_validation(
        self, test_db: AsyncSession, mock_new_format_word_data_chinese
    ):
        """测试JSONB数据结构验证"""

        # 1. 转换并存储新格式数据
        word_data = WordDataConverter.convert_ai_response_to_word(
            mock_new_format_word_data_chinese.model_dump(),
            language_code="zh_CN",
            source="ai"
        )

        word = Word(**word_data)
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        # 2. 验证JSONB字段结构
        assert isinstance(word.core_game_new, dict)
        assert "content" in word.core_game_new
        assert len(word.core_game_new["content"]) > 0

        assert isinstance(word.game_boards, dict)
        assert "board_a_speculative" in word.game_boards
        assert "board_b_life" in word.game_boards

        # 验证棋盘结构
        board_a = word.game_boards["board_a_speculative"]
        assert "type" in board_a
        assert "name" in board_a
        assert "example" in board_a

        assert isinstance(word.etymology_new, dict)
        assert "breakdown" in word.etymology_new
        assert "story" in word.etymology_new

        # 验证词源拆解结构
        breakdown = word.etymology_new["breakdown"]
        assert "prefix" in breakdown
        assert "root" in breakdown
        assert "suffix" in breakdown

        assert isinstance(word.common_mistakes_new, dict)
        assert "warning" in word.common_mistakes_new
        assert "avoidance" in word.common_mistakes_new

    async def test_data_integrity_across_formats(
        self, test_db: AsyncSession, mock_new_format_word_data_chinese
    ):
        """测试跨格式的数据完整性"""

        # 1. 创建新格式单词
        new_word_data = WordDataConverter.convert_ai_response_to_word(
            mock_new_format_word_data_chinese.model_dump(),
            language_code="zh_CN",
            source="ai"
        )
        new_word = Word(**new_word_data)
        test_db.add(new_word)
        await test_db.commit()
        await test_db.refresh(new_word)

        # 2. 验证新格式数据完整性
        new_display = new_word.get_display_data('new')
        assert new_display["word"] == "accommodation"
        assert new_display["translation"] == "住宿，适应"
        assert new_display["core_game"]["content"] == new_word.core_game_new["content"]

        # 3. 验证兼容字段完整性
        assert new_word.core_game == new_word.core_game_new["content"]
        assert new_word.scenario_formal == new_word.game_boards["board_a_speculative"]["example"]
        assert new_word.scenario_casual == new_word.game_boards["board_b_life"]["example"]

        # 4. 测试API字典格式
        api_dict = new_word.to_api_dict(include_legacy_fields=True)
        assert "id" in api_dict
        assert "word" in api_dict
        assert "translation" in api_dict
        assert "core_game" in api_dict
        assert "game_boards" in api_dict
        assert "etymology" in api_dict
        assert "common_mistakes" in api_dict

        # 5. 测试新格式API响应（不含兼容字段）
        new_api_dict = new_word.to_api_dict(include_legacy_fields=False)
        assert "coreGame" not in new_api_dict  # 旧格式字段不应存在
        assert "scenarioFormal" not in new_api_dict
        assert "core_game" in new_api_dict  # 新格式字段应存在