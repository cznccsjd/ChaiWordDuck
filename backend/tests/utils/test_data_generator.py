"""
测试数据生成器

提供动态、唯一的测试数据生成功能，解决硬编码和数据冲突问题
确保每个测试用例都有独立的测试数据，避免测试间相互影响
"""
import uuid
import random
import string
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib

from app.services.ai.base import WordManualData
from app.prompts.enums import Language


@dataclass
class TestWordData:
    """测试单词数据容器"""
    word: str
    language: str
    phonetic: str
    part_of_speech: str
    mock_data: WordManualData
    unique_id: str


class TestDataGenerator:
    """测试数据生成器

    提供动态、唯一的测试数据生成，确保：
    1. 每个测试用例使用唯一的测试数据
    2. 支持多语言测试数据生成
    3. 避免硬编码和数据冲突
    4. 提供可预测的随机数据
    """

    # 测试用词库（按语言分类）
    WORD_BANKS = {
        "zh_CN": [
            "学习", "工作", "生活", "朋友", "家庭", "健康", "快乐", "成功",
            "梦想", "希望", "勇气", "智慧", "知识", "创新", "进步", "团结",
            "友谊", "爱情", "和平", "自由", "责任", "荣誉", "诚信", "勤奋"
        ],
        "en_US": [
            "learning", "working", "living", "friend", "family", "health", "happy", "success",
            "dream", "hope", "courage", "wisdom", "knowledge", "innovation", "progress", "unity",
            "friendship", "love", "peace", "freedom", "responsibility", "honor", "integrity", "diligence"
        ]
    }

    # 词性列表
    PARTS_OF_SPEECH = ["noun", "verb", "adjective", "adverb", "preposition", "conjunction", "interjection"]

    # 音标模板
    PHONETIC_TEMPLATES = [
        "[{word}]", "[{word}ɪŋ]", "[ˈ{word}]", "[{word}ɪd]",
            "['{word}]", "[{word}əd]", "[{word}t]", "[{word}d]"
    ]

    def __init__(self, test_name: str = ""):
        """初始化测试数据生成器

        Args:
            test_name: 测试名称，用于生成可预测的随机数据
        """
        self.test_name = test_name
        self.test_timestamp = datetime.now().isoformat()
        self.generated_words: Dict[str, TestWordData] = {}
        self._random_seed = self._generate_seed()

        # 设置随机种子确保可重现性
        random.seed(self._random_seed)

    def _generate_seed(self) -> int:
        """生成基于测试名称的随机种子"""
        seed_string = f"{self.test_name}_{self.test_timestamp}"
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)

    def _generate_unique_word_base(self, language: str) -> str:
        """生成唯一的单词基础词"""
        word_bank = self.WORD_BANKS.get(language, self.WORD_BANKS["en_US"])
        base_word = random.choice(word_bank)

        # 添加唯一性后缀
        unique_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        return f"{base_word}_{unique_suffix}"

    def _generate_phonetic(self, word: str) -> str:
        """生成音标"""
        template = random.choice(self.PHONETIC_TEMPLATES)
        return template.format(word=word[:3])  # 使用前3个字符生成音标

    def _generate_mock_data(self, word: str, language: str) -> WordManualData:
        """生成模拟的单词手册数据"""
        if language == "zh_CN":
            return self._generate_chinese_mock_data(word)
        else:
            return self._generate_english_mock_data(word)

    def _generate_chinese_mock_data(self, word: str) -> WordManualData:
        """生成中文模拟数据"""
        base_word = word.split('_')[0] if '_' in word else word
        return WordManualData(
            word=word,
            phonetic=self._generate_phonetic(word),
            part_of_speech=random.choice(self.PARTS_OF_SPEECH),
            core_game=f"中文游戏内容：通过游戏方式学习'{base_word}'这个单词",
            scenario_formal=f"正式场景：在正式场合使用'{base_word}'的例句",
            scenario_casual=f"日常场景：在日常对话中使用'{base_word}'的表达方式",
            etymology_breakdown=f"词源拆解：'{base_word}'的来源和构成分析",
            etymology_story=f"词源故事：关于'{base_word}'的历史故事和背景",
            memory_trick=f"记忆技巧：巧记'{base_word}'的方法和技巧",
            common_mistakes=f"常见错误：使用'{base_word}'时容易犯的错误"
        )

    def _generate_english_mock_data(self, word: str) -> WordManualData:
        """生成英文模拟数据"""
        base_word = word.split('_')[0] if '_' in word else word
        return WordManualData(
            word=word,
            phonetic=self._generate_phonetic(word),
            part_of_speech=random.choice(self.PARTS_OF_SPEECH),
            core_game=f"English game content: Learn '{base_word}' through interactive games",
            scenario_formal=f"Formal scenario: Using '{base_word}' in formal contexts",
            scenario_casual=f"Casual scenario: Everyday usage of '{base_word}' in conversation",
            etymology_breakdown=f"Etymology: Analysis of '{base_word}' origins and structure",
            etymology_story=f"Etymology story: Historical background of '{base_word}'",
            memory_trick=f"Memory trick: Creative ways to remember '{base_word}'",
            common_mistakes=f"Common mistakes: Frequent errors when using '{base_word}'"
        )

    def generate_unique_word(self, language: str = "en_US") -> TestWordData:
        """生成唯一的测试单词数据

        Args:
            language: 目标语言

        Returns:
            TestWordData: 包含唯一单词和模拟数据的对象
        """
        unique_id = str(uuid.uuid4())
        word = self._generate_unique_word_base(language)
        phonetic = self._generate_phonetic(word)
        part_of_speech = random.choice(self.PARTS_OF_SPEECH)
        mock_data = self._generate_mock_data(word, language)

        test_word_data = TestWordData(
            word=word,
            language=language,
            phonetic=phonetic,
            part_of_speech=part_of_speech,
            mock_data=mock_data,
            unique_id=unique_id
        )

        # 存储生成的数据以便追踪
        self.generated_words[unique_id] = test_word_data

        return test_word_data

    def generate_multiple_unique_words(self, count: int, language: str = "en_US") -> List[TestWordData]:
        """生成多个唯一的测试单词数据

        Args:
            count: 生成的单词数量
            language: 目标语言

        Returns:
            List[TestWordData]: 唯一单词数据列表
        """
        return [self.generate_unique_word(language) for _ in range(count)]

    def generate_multilang_word_pair(self) -> Tuple[TestWordData, TestWordData]:
        """生成中英文单词对

        Returns:
            Tuple[TestWordData, TestWordData]: (中文数据, 英文数据)
        """
        # 生成相同基础词的中英文版本
        base_word = random.choice(self.WORD_BANKS["zh_CN"])
        unique_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))

        chinese_word = f"{base_word}_{unique_suffix}"
        english_word = f"{self.WORD_BANKS['en_US'][self.WORD_BANKS['zh_CN'].index(base_word)]}_{unique_suffix}"

        chinese_data = TestWordData(
            word=chinese_word,
            language="zh_CN",
            phonetic=self._generate_phonetic(chinese_word),
            part_of_speech=random.choice(self.PARTS_OF_SPEECH),
            mock_data=self._generate_chinese_mock_data(chinese_word),
            unique_id=str(uuid.uuid4())
        )

        english_data = TestWordData(
            word=english_word,
            language="en_US",
            phonetic=self._generate_phonetic(english_word),
            part_of_speech=chinese_data.part_of_speech,  # 保持词性一致
            mock_data=self._generate_english_mock_data(english_word),
            unique_id=str(uuid.uuid4())
        )

        self.generated_words[chinese_data.unique_id] = chinese_data
        self.generated_words[english_data.unique_id] = english_data

        return chinese_data, english_data

    def get_word_by_id(self, unique_id: str) -> Optional[TestWordData]:
        """根据唯一ID获取已生成的单词数据"""
        return self.generated_words.get(unique_id)

    def get_all_generated_words(self) -> Dict[str, TestWordData]:
        """获取所有已生成的单词数据"""
        return self.generated_words.copy()

    def generate_test_user_data(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """生成测试用户数据"""
        unique_id = user_id or random.randint(1000, 9999)
        return {
            "email": f"testuser{unique_id}@example.com",
            "password": "TestPass123!",
            "preferred_language": random.choice(["zh_CN", "en_US"]),
            "membership_tier": random.choice(["free", "premium"]),
            "username": f"testuser_{unique_id}"
        }

    def generate_invalid_language_codes(self) -> List[str]:
        """生成无效的语言代码用于测试降级机制"""
        return [
            "invalid_lang",
            "zh-XX",
            "en-YY",
            "fr-FR",  # 不支持的语言
            "de-DE",
            "ja-JP",
            "",
            "invalid",
            "zh;q=abc",
            "zh;q=2.0",
            "very-long-language-code-that-does-not-exist-and-should-cause-fallback"
        ]

    def generate_malformed_accept_language_headers(self) -> List[Dict[str, str]]:
        """生成格式错误的Accept-Language头部"""
        return [
            {"Accept-Language": ""},
            {"Accept-Language": "invalid"},
            {"Accept-Language": "zh;q=abc"},
            {"Accept-Language": "zh;q=2.0"},
            {"Accept-Language": "very-long-language-code-that-does-not-exist"},
            {"Accept-Language": "zh-CN;q=0.9,"},
            {"Accept-Language": ",en-US;q=0.8"},
            {"Accept-Language": "  en-US  "},
        ]

    def get_test_summary(self) -> Dict[str, Any]:
        """获取测试数据生成摘要"""
        return {
            "test_name": self.test_name,
            "timestamp": self.test_timestamp,
            "random_seed": self._random_seed,
            "total_words_generated": len(self.generated_words),
            "generated_languages": {
                lang: len([w for w in self.generated_words.values() if w.language == lang])
                for lang in ["zh_CN", "en_US"]
            },
            "unique_ids": list(self.generated_words.keys())
        }


class TestDataFactory:
    """测试数据工厂

    提供全局测试数据生成管理
    """

    _generators: Dict[str, TestDataGenerator] = {}

    @classmethod
    def get_generator(cls, test_name: str) -> TestDataGenerator:
        """获取或创建测试数据生成器"""
        if test_name not in cls._generators:
            cls._generators[test_name] = TestDataGenerator(test_name)
        return cls._generators[test_name]

    @classmethod
    def cleanup_generator(cls, test_name: str):
        """清理指定测试的生成器数据"""
        if test_name in cls._generators:
            del cls._generators[test_name]

    @classmethod
    def cleanup_all(cls):
        """清理所有生成器数据"""
        cls._generators.clear()

    @classmethod
    def get_all_summaries(cls) -> List[Dict[str, Any]]:
        """获取所有生成器的摘要信息"""
        return [generator.get_test_summary() for generator in cls._generators.values()]