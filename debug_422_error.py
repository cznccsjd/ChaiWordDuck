#!/usr/bin/env python3
"""
调试422错误问题的测试脚本

用于分析为什么所有单词（包括"hello"）都报422错误
"""

import asyncio
import sys
import os

# 添加后端路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai.factory import AIServiceFactory
from app.services.ai.base import AIParseError
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_word_generation():
    """测试单词生成，观察具体的错误情况"""

    # 初始化AI服务
    try:
        ai_service = AIServiceFactory.get_service()
        logger.info("AI服务初始化成功")
    except Exception as e:
        logger.error(f"AI服务初始化失败: {e}")
        return

    # 测试词汇列表（包括简单词汇）
    test_words = ["hello", "world", "cat", "dog", "book"]

    for word in test_words:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试词汇: {word}")
        logger.info(f"{'='*50}")

        try:
            # 调用AI生成
            result = await ai_service.generate_word_manual(word)
            logger.info(f"✅ {word} 生成成功")
            logger.info(f"   核心游戏: {result.core_game[:50]}...")

        except AIParseError as e:
            logger.error(f"❌ {word} 生成失败 - AIParseError: {e}")
            # 检查是否被误判为安全过滤器问题
            error_msg = str(e)
            if "安全过滤器" in error_msg or "safety filter" in error_msg.lower():
                logger.error(f"   🚨 被误判为安全过滤器问题！")
            else:
                logger.error(f"   ℹ️  其他解析错误")

        except Exception as e:
            logger.error(f"❌ {word} 生成失败 - 其他错误: {type(e).__name__}: {e}")

async def analyze_finish_reason_behavior():
    """分析finish_reason的行为模式"""

    logger.info(f"\n{'='*60}")
    logger.info("分析Gemini API finish_reason行为")
    logger.info(f"{'='*60}")

    # 这里我们需要更底层的Gemini API调用
    try:
        import google.generativeai as genai

        # 检查API配置
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY环境变量未设置")
            return

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 测试简单请求
        logger.info("测试简单文本生成...")
        response = model.generate_content("Say hello")

        if response.candidates:
            candidate = response.candidates[0]
            logger.info(f"finish_reason: {candidate.finish_reason}")
            logger.info(f"content type: {type(candidate.content)}")

            if hasattr(candidate.content, 'parts'):
                logger.info(f"parts count: {len(candidate.content.parts)}")
                for i, part in enumerate(candidate.content.parts):
                    logger.info(f"part {i}: {type(part)} - {part.text[:50] if hasattr(part, 'text') else 'no text'}")

        # 测试单词生成请求
        logger.info("\n测试单词生成请求...")
        from app.prompts.word_generation import get_word_generation_prompt
        prompt = get_word_generation_prompt("hello")

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )

        if response.candidates:
            candidate = response.candidates[0]
            logger.info(f"finish_reason: {candidate.finish_reason}")
            logger.info(f"content type: {type(candidate.content)}")

            # 尝试获取内容
            content = ""
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        content += part.text
            elif hasattr(candidate.content, 'text'):
                content = candidate.content.text

            logger.info(f"content length: {len(content)}")
            logger.info(f"content preview: {content[:200]}...")

    except ImportError:
        logger.error("google.generativeai未安装")
    except Exception as e:
        logger.error(f"底层测试失败: {e}")

async def main():
    """主函数"""
    logger.info("开始调试422错误问题...")

    # 分析finish_reason行为
    await analyze_finish_reason_behavior()

    # 测试单词生成
    await test_word_generation()

    logger.info("\n调试完成")

if __name__ == "__main__":
    asyncio.run(main())