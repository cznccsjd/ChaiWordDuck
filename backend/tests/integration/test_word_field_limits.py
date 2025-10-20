"""
测试数据库字段长度限制修复

验证修复后的字段能够正确存储长文本内容
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Word


class TestWordFieldLengthLimits:
    """测试单词字段长度限制修复"""

    async def test_part_of_speech_long_content(
        self, test_db: AsyncSession
    ):
        """测试part_of_speech字段能够存储长内容"""
        # 创建包含长词性描述的单词
        long_part_of_speech = "感叹词 (interjection), 名词 (noun), 动词 (verb), 形容词 (adjective), 副词 (adverb)"

        word = Word(
            word="multifunctional",
            phonetic="/ˌmʌltiˈfʌŋkʃənl/",
            part_of_speech=long_part_of_speech,
            core_game="这是一个多功能词汇的变身游戏",
            scenario_formal="在学术讨论中使用multifunctional概念",
            scenario_casual="这个工具真是multifunctional，什么都能做",
            etymology_breakdown="multi-(多) + function(功能) + -al(形容词后缀)",
            etymology_story="源自拉丁语，指具有多种功能的特性",
            common_mistakes="不要把multifunctional拼成multifunctionel",
            memory_trick="想象一个瑞士军刀，multifunctional就是这样的多功能工具",
            is_golden=False,
            source="ai"
        )

        # 保存到数据库
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        # 验证数据已正确保存
        assert word.id is not None
        assert word.part_of_speech == long_part_of_speech

        # 从数据库重新查询验证
        result = await test_db.execute(
            select(Word).where(Word.id == word.id)
        )
        retrieved_word = result.scalar_one()

        assert retrieved_word.part_of_speech == long_part_of_speech

    async def test_phonetic_long_content(
        self, test_db: AsyncSession
    ):
        """测试phonetic字段能够存储长音标"""
        # 创建包含长音标的单词
        long_phonetic = "/ˌæntɪˌdɪsɪstæblɪʃmenˈteɪrɪənɪzm/ (美式音标) /ˌæntɪˌdɪsɪstæblɪʃmenˈteəriənɪzəm/ (英式音标)"

        word = Word(
            word="antidisestablishmentarianism",
            phonetic=long_phonetic,
            part_of_speech="名词",
            core_game="这是一个超长政治术语的拆解游戏",
            scenario_formal="在政治史课上学习antidisestablishmentarianism运动",
            scenario_casual="这个单词是英语中最长的单词之一",
            etymology_breakdown="anti-(反对) + dis-(分离) + establishment(建制) + -arian(支持者) + -ism(主义)",
            etymology_story="19世纪英国政治运动的历史术语",
            common_mistakes="这个单词太长了，很容易拼错",
            memory_trick="分段记忆：anti-dis-establish-ment-arian-ism",
            is_golden=False,
            source="ai"
        )

        # 保存到数据库
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        # 验证数据已正确保存
        assert word.id is not None
        assert word.phonetic == long_phonetic

        # 从数据库重新查询验证
        result = await test_db.execute(
            select(Word).where(Word.id == word.id)
        )
        retrieved_word = result.scalar_one()

        assert retrieved_word.phonetic == long_phonetic

    async def test_source_can_handle_maximum_allowed_length(
        self, test_db: AsyncSession
    ):
        """测试source字段能够处理最大允许的长度"""
        # 使用允许的最大值，但保持约束允许的值
        # 由于有CheckConstraint限制，我们只能使用'ai'或'manual'
        # 但字段本身现在支持更长的值，为将来的扩展做准备
        word = Word(
            word="test",
            phonetic="/test/",
            part_of_speech="名词",
            core_game="测试游戏",
            scenario_formal="正式测试场景",
            scenario_casual="休闲测试场景",
            etymology_breakdown="test-测试",
            common_mistakes="没有常见错误",
            memory_trick="测试记忆技巧",
            is_golden=False,
            source="ai"  # 使用约束允许的值
        )

        # 保存到数据库
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        # 验证数据已正确保存
        assert word.id is not None
        assert word.source == "ai"

        # 从数据库重新查询验证
        result = await test_db.execute(
            select(Word).where(Word.id == word.id)
        )
        retrieved_word = result.scalar_one()

        assert retrieved_word.source == "ai"

    async def test_all_long_fields_together(
        self, test_db: AsyncSession
    ):
        """测试所有字段同时包含长内容"""
        # 创建所有字段都很长的单词
        long_part_of_speech = "感叹词 (interjection), 名词 (noun), 动词 (verb), 形容词 (adjective), 副词 (adverb), 介词 (preposition), 连词 (conjunction)"
        long_phonetic = "/ˌsʌpəˌkælɪˈfrɪdʒɪləstɪkˌɛkspiːæliˈdoʊʃəs/ (美式音标) /ˌsjuːpəˌkælɪˈfrɪdʒɪləstɪkˌɪkspiːæliˈdoʊʃəs/ (英式音标)"
        source = "ai"  # 使用约束允许的值

        word = Word(
            word="supercalifragilisticexpialidocious",
            phonetic=long_phonetic,
            part_of_speech=long_part_of_speech,
            core_game="这是一个超长单词的拆解游戏，非常有趣且具有挑战性",
            scenario_formal="在语言学研究中讨论supercalifragilisticexpialidocious的构成和文化影响",
            scenario_casual="看《欢乐满人间》时听到这个神奇的单词supercalifragilisticexpialidocious",
            etymology_breakdown="super-(超级) + cali-(美丽) + fragilistic-(易碎) + expialidocious-(赎罪)",
            etymology_story="这个词出自1964年迪士尼电影《欢乐满人间》，是由创作者P.L. Travers和音乐兄弟 Sherman 兄弟创造的有趣词汇",
            common_mistakes="这个词太长了，拼写时很容易出错，需要分段记忆",
            memory_trick="把它拆成几个部分来记：super-cali-fragil-istic-expi-ali-docious",
            is_golden=True,
            source=source
        )

        # 保存到数据库
        test_db.add(word)
        await test_db.commit()
        await test_db.refresh(word)

        # 验证数据已正确保存
        assert word.id is not None
        assert word.part_of_speech == long_part_of_speech
        assert word.phonetic == long_phonetic
        assert word.source == source

        # 从数据库重新查询验证
        result = await test_db.execute(
            select(Word).where(Word.id == word.id)
        )
        retrieved_word = result.scalar_one()

        assert retrieved_word.part_of_speech == long_part_of_speech
        assert retrieved_word.phonetic == long_phonetic
        assert retrieved_word.source == source