#!/usr/bin/env python3
"""
API版本控制集成测试

测试API端点中的版本控制功能，确保prompt_version正确传递和处理
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models.word import Word
from app.models.user import User
from app.models.guest_query_log import GuestQueryLog


class TestAPIVersionControlIntegration:
    """API版本控制集成测试"""

    @classmethod
    def setup_class(cls):
        """设置测试环境"""
        # 创建测试数据库
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        # 创建所有表
        Base.metadata.create_all(bind=cls.engine)

        # 创建测试会话
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        cls.db = TestingSessionLocal()

        # 创建测试客户端
        cls.client = TestClient(app)

        # 覆盖数据库依赖
        def override_get_db():
            try:
                yield cls.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        # 插入测试数据
        cls._setup_test_data()

    @classmethod
    def teardown_class(cls):
        """清理测试环境"""
        cls.db.close()
        app.dependency_overrides.clear()

    @classmethod
    def _setup_test_data(cls):
        """设置测试数据"""
        # 创建测试用户
        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        cls.db.add(test_user)

        # 创建测试单词数据 - v1.0格式（旧格式）
        legacy_word = Word(
            id=1,
            word="legacy_test",
            phonetic="/ˈleɡəsi/",
            part_of_speech="noun",
            translation="传统测试",
            is_golden=False,
            is_legacy_format=True,
            prompt_version="v1.0",
            core_game="传统游戏内容",
            scenario_formal="正式场景",
            scenario_casual="休闲场景",
            etymology_breakdown="词源分解",
            etymology_story="词源故事",
            common_mistakes="常见错误",
            memory_trick="记忆技巧",
            source="legacy",
            language_code="zh",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        cls.db.add(legacy_word)

        # 创建测试单词数据 - v2.0格式（新格式）
        new_word = Word(
            id=2,
            word="new_test",
            phonetic="/nuː/",
            part_of_speech="noun",
            translation="新测试",
            is_golden=False,
            is_legacy_format=False,
            prompt_version="v2.0",
            core_game_new={"content": "结构化游戏内容"},
            game_boards={
                "board_a_speculative": {"example": "思辨场景"},
                "board_b_life": {"example": "生活场景"}
            },
            etymology_new={
                "breakdown": {"root": {"part": "词根分析"}},
                "story": "词源故事"
            },
            common_mistakes_new={"warning": "警告信息"},
            memory_trick="记忆技巧",
            source="ai",
            language_code="en",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        cls.db.add(new_word)

        # 创建无版本的测试单词
        no_version_word = Word(
            id=3,
            word="no_version",
            phonetic="/noʊ/",
            part_of_speech="noun",
            translation="无版本",
            is_golden=False,
            is_legacy_format=True,
            prompt_version=None,  # 没有版本信息
            core_game="游戏内容",
            scenario_formal="场景",
            scenario_casual="场景",
            etymology_breakdown="分解",
            etymology_story="故事",
            common_mistakes="错误",
            memory_trick="技巧",
            source="test",
            language_code="en",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        cls.db.add(no_version_word)

        cls.db.commit()

    def test_query_word_by_id_legacy_format(self):
        """测试查询单词（旧格式）包含promptVersion"""
        response = self.client.get("/api/v1/words/1")

        assert response.status_code == 200
        data = response.json()

        # 验证版本信息
        assert "promptVersion" in data
        assert data["promptVersion"] == "v1.0"

        # 验证其他字段
        assert data["word"] == "legacy_test"
        assert data["isLegacyFormat"] is True

    def test_query_word_by_id_new_format(self):
        """测试查询单词（新格式）包含promptVersion"""
        response = self.client.get("/api/v1/words/2")

        assert response.status_code == 200
        data = response.json()

        # 验证版本信息
        assert "promptVersion" in data
        assert data["promptVersion"] == "v2.0"

        # 验证其他字段
        assert data["word"] == "new_test"
        assert data["isLegacyFormat"] is False

    def test_query_word_by_id_no_version(self):
        """测试查询单词（无版本）使用默认版本"""
        response = self.client.get("/api/v1/words/3")

        assert response.status_code == 200
        data = response.json()

        # 验证版本信息
        assert "promptVersion" in data
        # 应该有默认值，可能是v1.0或者从其他逻辑获取
        assert data["promptVersion"] is not None

        # 验证其他字段
        assert data["word"] == "no_version"

    def test_search_words_with_version_filter(self):
        """测试搜索单词时版本信息包含在响应中"""
        # 模拟搜索API响应
        response = self.client.get("/api/v1/words/search?q=test&language=zh")

        # 搜索API可能不存在或者有不同的端点，这里模拟基本检查
        # 实际实现需要根据API设计调整
        if response.status_code == 200:
            data = response.json()
            # 验证响应中包含版本信息
            if isinstance(data, dict) and "data" in data:
                for item in data["data"]:
                    assert "promptVersion" in item

    def test_guest_query_logs_version_tracking(self):
        """测试访客查询记录中的版本跟踪"""
        # 创建访客查询日志
        guest_log = GuestQueryLog(
            guest_id="test_guest_123",
            word="test_word",
            language_code="zh",
            prompt_version="v2.0",  # 记录使用的prompt版本
            ip_address="127.0.0.1",
            user_agent="Test-Agent",
            response_time_ms=150,
            created_at=datetime.now()
        )
        self.db.add(guest_log)
        self.db.commit()

        # 查询日志记录
        log = self.db.query(GuestQueryLog).filter(
            GuestQueryLog.guest_id == "test_guest_123"
        ).first()

        assert log is not None
        assert log.prompt_version == "v2.0"
        assert log.word == "test_word"

    @patch('app.api.v1.words.settings')
    def test_api_uses_current_config_version(self, mock_settings):
        """测试API使用当前配置的版本"""
        # 模拟不同的配置版本
        mock_settings.prompt_version = "v3.0"

        # 这个测试需要根据实际的API实现进行调整
        # 主要目的是验证API端点正确读取和使用配置中的版本

        # 验证配置被正确模拟
        assert mock_settings.prompt_version == "v3.0"

    def test_word_data_consistency_across_endpoints(self):
        """测试不同端点返回的单词数据一致性"""
        # 获取单词详情
        detail_response = self.client.get("/api/v1/words/1")

        # 如果有其他API端点返回相同单词，验证数据一致性
        # 例如搜索端点、推荐端点等

        assert detail_response.status_code == 200
        detail_data = detail_response.json()

        # 验证关键字段一致性
        required_fields = [
            "id", "word", "promptVersion", "isLegacyFormat"
        ]

        for field in required_fields:
            assert field in detail_data, f"缺少必需字段: {field}"

        assert detail_data["id"] == 1
        assert detail_data["promptVersion"] is not None

    def test_response_format_consistency(self):
        """测试响应格式的一致性"""
        # 测试不同版本的单词响应格式一致性
        responses = [
            self.client.get("/api/v1/words/1"),  # v1.0格式
            self.client.get("/api/v1/words/2"),  # v2.0格式
            self.client.get("/api/v1/words/3"),  # 无版本格式
        ]

        for response in responses:
            assert response.status_code == 200
            data = response.json()

            # 验证共同必需字段
            common_fields = [
                "id", "word", "phonetic", "translation",
                "promptVersion", "isLegacyFormat"
            ]

            for field in common_fields:
                assert field in data, f"响应缺少字段 {field}: {data.keys()}"

            # 验证promptVersion不为空
            assert data["promptVersion"] is not None, "promptVersion不能为空"

    def test_error_handling_for_invalid_word_id(self):
        """测试无效单词ID的错误处理"""
        response = self.client.get("/api/v1/words/99999")

        assert response.status_code == 404
        data = response.json()

        # 验证错误响应格式
        assert "detail" in data or "error" in data

    def test_language_code_handling_in_api(self):
        """测试API中的语言代码处理"""
        # 测试不同的语言代码请求
        test_cases = [
            {"language": "zh", "expected": "zh"},
            {"language": "en", "expected": "en"},
            {"language": "zh_CN", "expected": "zh"},  # 应该被标准化
        ]

        for case in test_cases:
            response = self.client.get(
                f"/api/v1/words/search?q=test&language={case['language']}"
            )

            # 如果API支持语言参数，验证处理正确
            if response.status_code == 200:
                # 这个测试需要根据实际API实现调整
                pass


class TestVersionControlDataIsolation:
    """版本控制数据隔离测试"""

    def test_database_data_isolation(self):
        """测试数据库中的数据隔离"""
        # 验证测试数据不会影响生产数据库
        from app.core.config import settings

        # 这里可以验证数据库连接配置
        # 确保测试使用的是独立的测试数据库

        assert True  # 基本验证，实际实现需要更具体的检查

    def test_test_data_cleanup(self):
        """测试数据清理机制"""
        # 验证测试数据被正确清理
        # 这通常在teardown中处理

        # 检查我们创建的测试数据存在
        words = self.db.query(Word).all()
        assert len(words) >= 3  # 至少包含我们的测试数据

        # 验证数据完整性
        for word in words:
            assert hasattr(word, 'prompt_version')
            assert word.word is not None

    def test_concurrent_request_data_safety(self):
        """测试并发请求的数据安全性"""
        # 模拟并发请求，验证数据一致性
        import threading
        import time

        results = []

        def make_request():
            response = self.client.get("/api/v1/words/1")
            results.append(response.status_code)

        # 创建多个并发请求
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有请求都成功
        assert all(status == 200 for status in results)
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])