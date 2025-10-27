"""
测试SQL插入错误修复的单元测试

验证Word模型插入功能是否正常工作
"""
import pytest
import asyncio
from sqlalchemy import select

from app.models.word import Word
from app.models.word_converter import WordDataConverter


@pytest.mark.asyncio
async def test_word_model_insertion(test_db):
    """测试Word模型的基本插入功能"""

    # 测试数据
    test_data = {
        'word': 'testword',
        'phonetic': '/test/',
        'part_of_speech': 'noun',
        'core_game': 'test game content',
        'scenario_formal': 'formal scenario',
        'scenario_casual': 'casual scenario',
        'etymology_breakdown': 'test etymology',
        'common_mistakes': 'test mistakes',
        'memory_trick': 'test trick',
        'translation': '测试单词',
        'language_code': 'zh_CN',
        'core_game_new': {'content': 'test game content'},
        'game_boards': {
            'board_a_speculative': {
                'type': '棋盘A (思辨场)',
                'name': '思辨场景',
                'example': 'formal example'
            },
            'board_b_life': {
                'type': '棋盘B (生活场)',
                'name': '生活场景',
                'example': 'casual example'
            }
        },
        'etymology_new': {
            'breakdown': {
                'prefix': {'part': 'test', 'meaning': '测试'},
                'root': {'part': 'word', 'meaning': '单词'},
                'suffix': {'part': '', 'meaning': ''}
            },
            'story': 'Test word etymology story'
        },
        'common_mistakes_new': {
            'warning': 'Common mistakes warning',
            'avoidance': 'How to avoid mistakes'
        }
    }

    # 创建Word对象
    word = Word(**test_data)

    # 插入数据库
    test_db.add(word)
    await test_db.commit()
    await test_db.refresh(word)

    # 验证插入结果
    assert word.id is not None
    assert word.word == 'testword'
    assert word.language_code == 'zh_CN'
    assert word.translation == '测试单词'

    # 验证JSONB字段
    assert word.core_game_new == {'content': 'test game content'}
    assert word.game_boards['board_a_speculative']['type'] == '棋盘A (思辨场)'
    assert word.etymology_new['breakdown']['root']['part'] == 'word'
    assert word.common_mistakes_new['warning'] == 'Common mistakes warning'

    print(f"✅ Word inserted successfully: ID={word.id}")


@pytest.mark.asyncio
async def test_word_data_converter_insertion(test_db):
    """测试WordDataConverter的AI响应转换功能"""

    # 模拟AI响应
    ai_response = {
        'word': 'accommodation',
        'phonetic': '/əˌkɒməˈdeɪʃn/',
        'part_of_speech': 'noun',
        'core_game': {
            'content': 'Accommodation game content'
        },
        'game_boards': {
            'board_a_speculative': {
                'type': '棋盘A (思辨场)',
                'name': '思辨场景',
                'example': 'Hotel accommodation negotiation scenario'
            },
            'board_b_life': {
                'type': '棋盘B (生活场)',
                'name': '生活场景',
                'example': 'Finding accommodation for vacation'
            }
        },
        'etymology': {
            'breakdown': {
                'prefix': {'part': 'ac-', 'meaning': 'to, toward'},
                'root': {'part': 'commodare', 'meaning': 'to make convenient'},
                'suffix': {'part': '-ation', 'meaning': 'process or action'}
            },
            'story': 'The word accommodation comes from Latin commodare meaning "to make suitable".'
        },
        'common_mistakes': {
            'warning': 'Common spelling mistakes: accomodation (missing one c), acommodation (missing one c and one m)',
            'avoidance': 'Remember: 2 Cs, 2 Ms - "ACCOMMODATION"'
        },
        'memory_trick': 'Think of "ACCOMMODATE" with 2 Cs and 2 Ms',
        'translation': '住宿；住处；调解'
    }

    # 转换AI响应
    word_data = WordDataConverter.convert_ai_response_to_word(
        ai_response, language_code='zh_CN', source='ai'
    )

    # 创建Word对象并插入
    word = Word(**word_data)
    test_db.add(word)
    await test_db.commit()
    await test_db.refresh(word)

    # 验证转换和插入结果
    assert word.id is not None
    assert word.word == 'accommodation'
    assert word.language_code == 'zh_CN'
    assert word.source == 'ai'
    assert word.prompt_version == 'v2.0'
    assert not word.is_legacy_format

    # 验证传统字段（向后兼容）
    assert word.core_game == 'Accommodation game content'
    assert word.scenario_formal == 'Hotel accommodation negotiation scenario'
    assert word.scenario_casual == 'Finding accommodation for vacation'
    assert word.etymology_breakdown == 'commodare'
    assert word.etymology_story == 'The word accommodation comes from Latin commodare meaning "to make suitable".'
    assert word.common_mistakes == 'Common spelling mistakes: accomodation (missing one c), acommodation (missing one c and one m)'
    assert word.memory_trick == 'Think of "ACCOMMODATE" with 2 Cs and 2 Ms'
    assert word.translation == '住宿；住处；调解'

    # 验证JSONB字段
    assert word.core_game_new['content'] == 'Accommodation game content'
    assert word.game_boards['board_a_speculative']['name'] == '思辨场景'
    assert word.etymology_new['breakdown']['prefix']['meaning'] == 'to, toward'
    assert word.common_mistakes_new['avoidance'] == 'Remember: 2 Cs, 2 Ms - "ACCOMMODATION"'

    print(f"✅ AI response converted and inserted successfully: ID={word.id}")


@pytest.mark.asyncio
async def test_multilingual_word_insertion(test_db):
    """测试多语言单词插入功能"""

    # 测试多种语言的单词
    test_words = [
        {
            'ai_response': {
                'word': 'procrastination',
                'phonetic': '/prəˌkræstɪˈneɪʃn/',
                'translation': '拖延；拖延症'
            },
            'language_code': 'zh_CN',
            'expected_translation': '拖延；拖延症'
        },
        {
            'ai_response': {
                'word': 'embarrassment',
                'phonetic': '/ɪmˈbærəsmənt/',
                'translation': '尴尬；窘迫'
            },
            'language_code': 'zh_TW',
            'expected_translation': '尴尬；窘迫'
        }
    ]

    inserted_word_ids = []

    for test_word_data in test_words:
        # 转换AI响应
        word_data = WordDataConverter.convert_ai_response_to_word(
            test_word_data['ai_response'],
            language_code=test_word_data['language_code'],
            source='ai'
        )

        # 创建并插入Word对象
        word = Word(**word_data)
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        inserted_word_ids.append(word.id)

        # 验证多语言特性
        assert word.id is not None
        assert word.language_code == test_word_data['language_code']
        assert word.translation == test_word_data['expected_translation']
        assert word.is_multilingual() is True

        print(f"✅ Multilingual word inserted: {word.word} (lang: {word.language_code}, trans: {word.translation})")

    # 验证查询功能
    for word_id in inserted_word_ids:
        stmt = select(Word).where(Word.id == word_id)
        result = await test_db.execute(stmt)
        retrieved_word = result.scalar_one_or_none()

        assert retrieved_word is not None
        assert retrieved_word.id == word_id
        assert retrieved_word.is_multilingual() is True

        print(f"✅ Multilingual word retrieved successfully: ID={word_id}")


@pytest.mark.asyncio
async def test_jsonb_field_null_handling(test_db):
    """测试JSONB字段的null值处理"""

    # 测试JSONB字段为None的情况
    word_data = {
        'word': 'minimal_word',
        'core_game': 'minimal content',
        'scenario_formal': 'minimal formal',
        'scenario_casual': 'minimal casual',
        'etymology_breakdown': 'minimal etymology',
        'common_mistakes': 'minimal mistakes',
        'memory_trick': 'minimal trick',
        'language_code': 'en',
        'core_game_new': None,
        'game_boards': None,
        'etymology_new': None,
        'common_mistakes_new': None
    }

    word = Word(**word_data)
    test_db.add(word)
    await test_db.commit()
    await test_db.refresh(word)

    # 验证null值处理
    assert word.id is not None
    assert word.core_game_new is None
    assert word.game_boards is None
    assert word.etymology_new is None
    assert word.common_mistakes_new is None

    print(f"✅ Null JSONB fields handled correctly: ID={word.id}")


if __name__ == "__main__":
    print("Running SQL insertion fix verification tests...")
    asyncio.run(test_all_functions())
    print("All tests completed!")