#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试真实API调用，找出422错误的根本原因
"""
import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ai.gemini_service import GeminiService
from app.services.ai.base import AIParseError, AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

async def debug_gemini_call():
    """调试真实的Gemini API调用"""
    print("=" * 60)
    print("开始调试真实Gemini API调用")
    print("=" * 60)

    # 获取环境变量
    api_key = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")
    print(f"API Key configured: {bool(api_key and api_key != 'your-gemini-api-key-here')}")
    if api_key == "your-gemini-api-key-here":
        print("错误: GEMINI_API_KEY未配置")
        print("请设置环境变量 GEMINI_API_KEY")
        return

    try:
        # 创建Gemini服务
        print("初始化Gemini服务...")
        service = GeminiService(
            api_key=api_key,
            model="gemini-1.5-flash",
            timeout=30
        )
        print("Gemini服务初始化成功")

        # 测试简单的词汇
        test_words = ["hello", "world", "cat", "dog"]

        for word in test_words:
            print(f"\n测试词汇: {word}")
            print("-" * 40)

            try:
                result = await service.generate_word_manual(word)
                print(f"成功生成 {word}")
                print(f"   核心游戏: {result.core_game[:50]}...")

            except AIParseError as e:
                print(f"AIParseError: {e}")
                print(f"   错误类型: 内容解析错误")
                print(f"   这会导致422状态码")

            except AIServiceError as e:
                print(f"AIServiceError: {e}")
                print(f"   错误类型: AI服务错误")

            except Exception as e:
                print(f"未知错误: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_gemini_call())