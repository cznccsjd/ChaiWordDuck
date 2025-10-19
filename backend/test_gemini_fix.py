#!/usr/bin/env python3
"""
Gemini修复验证脚本
验证修复后的Gemini API是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_gemini_service():
    """测试修复后的Gemini服务"""
    try:
        from app.services.ai.factory import AIServiceFactory
        from app.services.ai.base import AIServiceError, AITimeoutError, AIRateLimitError

        print("Testing Gemini service after fixes...")

        # 重置服务实例以重新初始化
        AIServiceFactory.reset_instance()

        # 获取AI服务
        ai_service = AIServiceFactory.get_service()
        print(f"AI Service initialized with provider: {AIServiceFactory.get_current_provider()}")

        # 测试单词生成
        test_word = "contribution"
        print(f"Testing word generation for: {test_word}")

        result = await ai_service.generate_word_manual(test_word)

        print(f"SUCCESS: Word manual generated for '{result.word}'")
        print(f"Phonetic: {result.phonetic}")
        print(f"Core game: {result.core_game[:50]}...")

        return True

    except AITimeoutError as e:
        print(f"TIMEOUT ERROR: {e}")
        return False
    except AIRateLimitError as e:
        print(f"RATE LIMIT ERROR: {e}")
        return False
    except AIServiceError as e:
        print(f"AI SERVICE ERROR: {e}")
        return False
    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("Gemini Service Fix Verification")
    print("=" * 40)

    success = await test_gemini_service()

    if success:
        print("\n✓ All tests passed! The fix is working correctly.")
    else:
        print("\n✗ Tests failed. Further investigation needed.")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)