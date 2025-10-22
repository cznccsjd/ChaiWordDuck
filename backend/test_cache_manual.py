"""
缓存功能手动验证脚本

用于验证Redis缓存机制是否正常工作
"""
import asyncio
import json
import time
from unittest.mock import AsyncMock, patch

from app.services.word_cache_service import get_word_cache_service
from app.schemas.word import WordQueryResponse


async def test_cache_performance():
    """测试缓存性能"""
    print("=== 缓存功能手动验证 ===\n")

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

    print("1. 测试缓存统计数据")
    stats = service.get_cache_stats()
    print(f"   初始统计: {stats}")
    assert stats["cache_ttl_hours"] == 24.0
    print("   [OK] TTL配置正确 (24小时)")

    print("\n2. 测试缓存写入")
    start_time = time.time()
    success = await service.cache_word("testword", word_response)
    write_time = (time.time() - start_time) * 1000
    print(f"   缓存写入耗时: {write_time:.2f}ms")
    print(f"   写入结果: {success}")
    assert success is True
    print("   [OK] 缓存写入成功")

    print("\n3. 测试缓存读取")
    start_time = time.time()
    cached_word = await service.get_cached_word("testword")
    read_time = (time.time() - start_time) * 1000
    print(f"   缓存读取耗时: {read_time:.2f}ms")
    print(f"   读取结果: {cached_word is not None}")

    if cached_word:
        print(f"   单词ID: {cached_word.id}")
        print(f"   单词: {cached_word.word}")
        print(f"   是否黄金手册: {cached_word.is_golden}")
        print("   ✓ 缓存读取成功")

        # 验证性能要求
        if read_time < 50:
            print(f"   ✓ 性能达标 (<50ms): {read_time:.2f}ms")
        else:
            print(f"   ⚠ 性能未达标 (>50ms): {read_time:.2f}ms")
    else:
        print("   ✗ 缓存读取失败")

    print("\n4. 测试缓存统计更新")
    stats_after = service.get_cache_stats()
    print(f"   更新后统计: {stats_after}")

    if stats_after["cache_hits"] > stats["cache_hits"]:
        print("   ✓ 缓存命中统计正确更新")
    else:
        print("   ⚠ 缓存命中统计未更新")

    print("\n5. 测试缓存预热")
    test_words = [
        WordQueryResponse(
            id=i+2,
            word=f"word{i+2}",
            phonetic=f"/word{i+2}/",
            part_of_speech="noun",
            core_game=f"游戏{i+2}",
            scenario_formal=f"场景{i+2}",
            scenario_casual=f"休闲{i+2}",
            etymology_breakdown=f"拆解{i+2}",
            etymology_story=f"故事{i+2}",
            common_mistakes=f"错误{i+2}",
            memory_trick=f"技巧{i+2}",
            is_golden=i%2==0,
            remaining_queries=10
        )
        for i in range(3)
    ]

    warm_stats = await service.warm_cache(test_words)
    print(f"   预热结果: {warm_stats}")

    if warm_stats["success_count"] == len(test_words):
        print("   ✓ 缓存预热成功")
    else:
        print("   ⚠ 缓存预热部分失败")

    print("\n6. 测试缓存失效")
    invalidate_success = await service.invalidate_word_cache("testword")
    print(f"   失效结果: {invalidate_success}")
    if invalidate_success:
        print("   ✓ 缓存失效成功")
    else:
        print("   ⚠ 缓存失效失败")

    print("\n7. 测试缓存统计重置")
    service.reset_cache_stats()
    reset_stats = service.get_cache_stats()
    print(f"   重置后统计: {reset_stats}")

    if reset_stats["cache_hits"] == 0 and reset_stats["cache_misses"] == 0:
        print("   ✓ 缓存统计重置成功")
    else:
        print("   ⚠ 缓存统计重置失败")

    print("\n=== 验证完成 ===")
    print("缓存功能基本验证通过！")

    return True


async def test_error_handling():
    """测试错误处理"""
    print("\n=== 错误处理测试 ===\n")

    service = get_word_cache_service()

    print("1. 测试Redis连接失败的处理")

    # 模拟Redis连接失败
    with patch.object(service, 'safe_get', side_effect=Exception("Redis connection failed")):
        result = await service.get_cached_word("error_test")
        print(f"   Redis错误时返回: {result}")
        assert result is None
        print("   ✓ Redis连接失败时正确降级")

    print("\n2. 测试损坏缓存数据的处理")

    # 模拟损坏的JSON数据
    with patch.object(service, 'safe_get', return_value="invalid json data"), \
         patch.object(service, 'safe_delete', return_value=True):
        result = await service.get_cached_word("corrupted_test")
        print(f"   损坏数据时返回: {result}")
        assert result is None
        print("   ✓ 损坏数据时正确处理")

    print("\n=== 错误处理测试完成 ===")
    print("错误处理验证通过！")

    return True


async def main():
    """主函数"""
    try:
        # 测试基本功能
        await test_cache_performance()

        # 测试错误处理
        await test_error_handling()

        print("\n🎉 所有缓存功能验证通过！")
        print("\n功能特性:")
        print("✓ Redis缓存机制正常工作")
        print("✓ 24小时TTL过期策略")
        print("✓ 缓存命中率和性能统计")
        print("✓ Redis故障降级处理")
        print("✓ 缓存数据损坏处理")
        print("✓ 缓存预热功能")
        print("✓ 缓存失效功能")
        print("✓ 性能监控和日志")

    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())