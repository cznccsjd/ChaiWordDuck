#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Gemini服务修复效果
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ai.gemini_service import GeminiService
from app.services.ai.base import AIParseError, AIServiceError

async def test_gemini_fix():
    """测试Gemini服务修复效果"""
    print("=" * 60)
    print("测试Gemini服务修复效果")
    print("=" * 60)

    import os
    api_key = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")

    if api_key == "your-gemini-api-key-here":
        print("错误: GEMINI_API_KEY未配置")
        return False

    try:
        # 创建Gemini服务
        print("初始化Gemini服务...")
        service = GeminiService(
            api_key=api_key,
            model="gemini-1.5-flash",
            timeout=30
        )
        print("✅ Gemini服务初始化成功")

        # 测试简单的词汇
        test_words = ["hello", "world", "cat", "dog", "test"]
        success_count = 0
        error_count = 0

        for word in test_words:
            print(f"\n🧪 测试词汇: {word}")
            print("-" * 40)

            try:
                result = await service.generate_word_manual(word)
                print(f"✅ 成功生成 {word}")
                print(f"   核心游戏: {result.core_game[:50]}...")
                print(f"   记忆技巧: {result.memory_trick[:50]}...")
                success_count += 1

            except AIParseError as e:
                print(f"⚠️ AIParseError: {e}")
                error_count += 1
                # 检查是否是真正的安全过滤器问题
                if "安全过滤器" in str(e):
                    print("   -> 这是真正的安全过滤器问题")
                else:
                    print("   -> 这可能是解析问题，需要进一步调试")

            except AIServiceError as e:
                print(f"❌ AIServiceError: {e}")
                error_count += 1

            except Exception as e:
                print(f"❌ 未知错误: {type(e).__name__}: {e}")
                error_count += 1

        print(f"\n{'='*60}")
        print(f"测试结果汇总:")
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失败: {error_count}")
        print(f"📊 成功率: {success_count/(success_count+error_count)*100:.1f}%")

        if success_count >= len(test_words) * 0.8:
            print("🎉 修复效果良好！大部分请求都成功了。")
            return True
        else:
            print("⚠️ 修复效果不佳，仍需进一步调试。")
            return False

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_gemini_fix())
    sys.exit(0 if result else 1)