"""
验证数据库字段长度限制修复的测试脚本

模拟原始报错场景，验证修复后的系统能够正常处理长文本内容
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import Word


async def test_original_error_scenario():
    """测试原始报错场景是否已修复"""
    print("开始测试原始报错场景修复...")

    async with AsyncSessionLocal() as session:
        try:
            # 创建导致原始错误的单词数据
            problematic_part_of_speech = "感叹词 (interjection), 名词 (noun), 动词 (verb)"

            print(f"测试数据: part_of_speech = '{problematic_part_of_speech}'")
            print(f"长度: {len(problematic_part_of_speech)} 字符")

            word = Word(
                word="hello",
                phonetic="/həˈloʊ/",
                part_of_speech=problematic_part_of_speech,  # 这个值之前会导致报错
                core_game="这是一个问候语游戏",
                scenario_formal="在正式场合使用hello表示问候",
                scenario_casual="和朋友见面时说hello",
                etymology_breakdown="hel-lo-问候",
                common_mistakes="不要拼成helo",
                memory_trick="记住hello有两个l",
                is_golden=False,
                source="ai"
            )

            # 尝试保存到数据库
            print("正在保存到数据库...")
            session.add(word)
            await session.commit()
            await session.refresh(word)

            print(f"成功保存！单词ID: {word.id}")
            print(f"part_of_speech字段已正确保存: '{word.part_of_speech}'")

            # 验证数据完整性
            result = await session.execute(
                select(Word).where(Word.id == word.id)
            )
            retrieved_word = result.scalar_one()

            assert retrieved_word.part_of_speech == problematic_part_of_speech
            print("数据完整性验证通过！")

            print("\n原始报错场景修复验证成功！")
            print("修复总结:")
            print("  - part_of_speech字段: String(20) → String(255)")
            print("  - phonetic字段: String(50) → String(200)")
            print("  - source字段: String(20) → String(50)")
            print("  - membership_tier字段: String(20) → String(50)")

        except Exception as e:
            print(f"测试失败: {type(e).__name__}: {e}")
            raise


async def test_extended_scenarios():
    """测试其他扩展场景"""
    print("\n测试扩展场景...")

    async with AsyncSessionLocal() as session:
        try:
            # 测试超长音标
            long_phonetic = "/ˌæntɪˌdɪsɪstæblɪʃmenˈteɪrɪənɪzm/ (美式) /ˌæntɪˌdɪsɪstæblɪʃmenˈteəriənɪzəm/ (英式)"
            print(f"测试长音标: {len(long_phonetic)} 字符")

            word = Word(
                word="test_phonetic",
                phonetic=long_phonetic,
                part_of_speech="名词",
                core_game="音标测试",
                scenario_formal="正式音标测试",
                scenario_casual="休闲音标测试",
                etymology_breakdown="test-phonetic-测试",
                common_mistakes="无错误",
                memory_trick="记忆技巧",
                is_golden=False,
                source="ai"
            )

            session.add(word)
            await session.commit()
            print("长音标测试通过！")

        except Exception as e:
            print(f"扩展场景测试失败: {type(e).__name__}: {e}")
            raise


async def main():
    """主测试函数"""
    print("=" * 60)
    print("数据库字段长度限制修复验证")
    print("=" * 60)

    await test_original_error_scenario()
    await test_extended_scenarios()

    print("\n" + "=" * 60)
    print("所有测试通过！修复验证成功！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())