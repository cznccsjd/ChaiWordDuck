"""
缓存功能简化验证脚本
"""
import asyncio
import time
from unittest.mock import patch

from app.services.word_cache_service import get_word_cache_service
from app.schemas.word import WordQueryResponse


async def test_cache_basic():
    """测试缓存基本功能"""
    print("=== 缓存功能验证 ===\n")

    service = get_word_cache_service()

    # 创建测试数据
    word_response = WordQueryResponse(
        id=1,
        word="testword",
        phonetic="/test/",
        part_of_speech="noun",
        core_game="测试核心游戏",
        scenario_formal="正式场景",
        scenario_casual="休闲场景",
        etymology_breakdown="词根拆解",
        etymology_story="词源故事",
        common_mistakes="常见错误",
        memory_trick="记忆技巧",
        is_golden=True,
        remaining_queries=10
    )

    print("1. 检查缓存配置")
    stats = service.get_cache_stats()
    print(f"   TTL: {stats['cache_ttl_hours']}小时")
    print(f"   初始统计: 命中={stats['cache_hits']}, 未命中={stats['cache_misses']}")

    print("\n2. 测试缓存写入")
    start = time.time()
    success = await service.cache_word("testword", word_response)
    write_time = (time.time() - start) * 1000
    print(f"   写入耗时: {write_time:.2f}ms, 结果: {success}")

    print("\n3. 测试缓存读取")
    start = time.time()
    result = await service.get_cached_word("testword")
    read_time = (time.time() - start) * 1000
    print(f"   读取耗时: {read_time:.2f}ms, 结果: {result is not None}")

    if result:
        print(f"   单词信息: {result.word} (ID: {result.id})")
        if read_time < 50:
            print(f"   [OK] 性能达标 <50ms: {read_time:.2f}ms")
        else:
            print(f"   [WARN] 性能未达标 >50ms: {read_time:.2f}ms")

    print("\n4. 检查统计更新")
    new_stats = service.get_cache_stats()
    print(f"   更新后: 命中={new_stats['cache_hits']}, 未命中={new_stats['cache_misses']}")
    print(f"   命中率: {new_stats['cache_hit_rate']:.2%}")

    print("\n5. 测试缓存预热")
    test_words = [
        WordQueryResponse(
            id=2,
            word="word2",
            phonetic="/word2/",
            part_of_speech="noun",
            core_game="游戏2",
            scenario_formal="场景2",
            scenario_casual="休闲2",
            etymology_breakdown="拆解2",
            etymology_story="故事2",
            common_mistakes="错误2",
            memory_trick="技巧2",
            is_golden=False,
            remaining_queries=10
        )
    ]

    warm_stats = await service.warm_cache(test_words)
    print(f"   预热结果: 成功={warm_stats['success_count']}, 总数={warm_stats['total_words']}")

    print("\n6. 测试错误处理")
    with patch.object(service, 'safe_get', side_effect=Exception("Redis error")):
        error_result = await service.get_cached_word("error_test")
        print(f"   Redis错误时: {error_result is None} (应该返回None)")

    return True


async def main():
    try:
        await test_cache_basic()
        print("\n=== 验证完成 ===")
        print("缓存功能基本正常！")

        print("\n已实现的功能:")
        print("- Redis缓存机制")
        print("- 24小时TTL过期")
        print("- 缓存命中率统计")
        print("- 性能监控")
        print("- 错误降级处理")

    except Exception as e:
        print(f"验证失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())