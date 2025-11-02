"""
Prompt版本控制集成测试

验证修复后的系统在实际API调用中使用正确的prompt版本
"""
import asyncio
from app.core.config import settings
from app.models.word_converter import WordDataConverter

def test_integration():
    """集成测试：验证修复效果"""

    print("=== Prompt版本控制集成测试 ===")

    # 1. 验证配置
    print(f"[OK] 配置文件中的prompt_version: {settings.prompt_version}")
    assert settings.prompt_version == "v2.0"

    # 2. 验证WordDataConverter使用配置版本
    ai_response = {
        'word': 'test',
        'phonetic': '/test/',
        'core_game': {'content': 'test game'},
        'game_boards': {},
        'etymology': {},
        'common_mistakes': {}
    }

    result = WordDataConverter.convert_ai_response_to_word(ai_response)
    print(f"[OK] WordDataConverter返回的prompt_version: {result['prompt_version']}")
    assert result['prompt_version'] == settings.prompt_version

    # 3. 验证旧数据转换保持原有版本
    class MockWord:
        def __init__(self):
            self.id = 1
            self.prompt_version = "v1.0"
            self.is_legacy_format = True
            self.word = "test"
            self.phonetic = "/test/"
            self.translation = "测试"
            self.part_of_speech = "n."
            self.core_game = "test game"
            self.scenario_formal = "formal scenario"
            self.scenario_casual = "casual scenario"
            self.etymology_breakdown = "test"
            self.etymology_story = "test story"
            self.common_mistakes = "common mistake"
            self.memory_trick = "memory trick"
            self.is_golden = False
            self.source = "legacy"
            self.created_at = None
            self.updated_at = None

    mock_word = MockWord()
    legacy_result = WordDataConverter.legacy_to_new_format(mock_word)
    print(f"[OK] 旧数据转换保持原版本: {legacy_result['prompt_version']}")
    assert legacy_result['prompt_version'] == "v1.0"

    print("\n=== 所有集成测试通过！ ===")
    print("[OK] 新生成的单词将使用v2.0版本")
    print("[OK] 旧数据转换保持原有版本不变")
    print("[OK] 系统成功修复prompt版本硬编码问题")

if __name__ == "__main__":
    test_integration()