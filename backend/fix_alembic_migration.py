#!/usr/bin/env python3
"""
Alembic迁移修复脚本

用于修复数据库迁移中的版本号长度限制问题
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[0]
sys.path.append(str(project_root))

import asyncio
from sqlalchemy import create_engine, text
from app.core.config import settings


async def check_database_connection():
    """检查数据库连接"""
    try:
        engine = create_engine(settings.database_url.replace("postgresql+asyncpg://", "postgresql://"))
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()")).scalar()
            print(f"✅ 数据库连接成功: {result}")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


async def get_current_version():
    """获取当前数据库版本"""
    try:
        engine = create_engine(settings.database_url.replace("postgresql+asyncpg://", "postgresql://"))
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            print(f"📍 当前数据库版本: {result}")
            return result
    except Exception as e:
        print(f"❌ 获取版本失败: {e}")
        return None


async def check_version_num_length():
    """检查版本号字段长度"""
    try:
        engine = create_engine(settings.database_url.replace("postgresql+asyncpg://", "postgresql://"))
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'alembic_version'
                AND column_name = 'version_num'
            """)).scalar()
            print(f"📏 alembic_version.version_num 字段长度: {result}")
            return result
    except Exception as e:
        print(f"❌ 检查字段长度失败: {e}")
        return None


async def run_alembic_commands():
    """运行Alembic命令"""
    import subprocess

    print("\n🔧 开始修复流程...")

    # 步骤1: 应用修复迁移
    print("\n📝 步骤1: 应用版本号长度修复迁移...")
    result = subprocess.run([
        "pdm", "run", "alembic", "upgrade", "fix_alembic_version_length"
    ], capture_output=True, text=True, cwd=project_root)

    if result.returncode != 0:
        print(f"❌ 修复迁移失败:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False

    print("✅ 版本号长度修复完成")

    # 步骤2: 应用006迁移
    print("\n📝 步骤2: 应用单词语言约束迁移...")
    result = subprocess.run([
        "pdm", "run", "alembic", "upgrade", "006_add_word_language_unique_constraint"
    ], capture_output=True, text=True, cwd=project_root)

    if result.returncode != 0:
        print(f"❌ 006迁移失败:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False

    print("✅ 006迁移完成")

    return True


async def main():
    """主函数"""
    print("🚀 Alembic迁移修复工具")
    print("=" * 50)

    # 检查数据库连接
    if not await check_database_connection():
        print("\n❌ 请检查数据库连接配置后重试")
        return

    # 获取当前版本
    current_version = await get_current_version()
    if not current_version:
        print("\n❌ 无法获取当前数据库版本")
        return

    # 检查字段长度
    current_length = await check_version_num_length()
    if not current_length:
        print("\n❌ 无法检查版本号字段长度")
        return

    print(f"\n📊 当前状态:")
    print(f"   数据库版本: {current_version}")
    print(f"   版本号字段长度: {current_length}")

    # 判断修复方案
    if current_version == '005_add_multilang_prompt_support' and current_length == 32:
        print(f"\n✅ 检测到需要修复的情况")
        print(f"   - 当前版本: 005_add_multilang_prompt_support")
        print(f"   - 字段长度: 32 (需要扩展)")

        # 确认执行
        response = input(f"\n❓ 是否立即执行修复? (y/N): ")
        if response.lower() == 'y':
            success = await run_alembic_commands()
            if success:
                print(f"\n🎉 修复完成! 现在可以正常使用Alembic迁移了")
            else:
                print(f"\n❌ 修复失败，请检查错误信息")
        else:
            print(f"\n🚫 用户取消修复")

    elif current_version == 'fix_alembic_version_length':
        print(f"\n📝 检测到版本号长度已修复，继续应用006迁移...")

        response = input(f"\n❓ 是否继续应用006迁移? (y/N): ")
        if response.lower() == 'y':
            import subprocess
            result = subprocess.run([
                "pdm", "run", "alembic", "upgrade", "006_add_word_language_unique_constraint"
            ], capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                print(f"\n🎉 006迁移应用成功!")
            else:
                print(f"\n❌ 006迁移失败:")
                print(f"STDERR: {result.stderr}")
        else:
            print(f"\n🚫 用户取消操作")

    elif current_version == '006_add_word_language_unique_constraint':
        print(f"\n✅ 所有迁移已经完成，无需修复")

    else:
        print(f"\n⚠️  当前状态不预期:")
        print(f"   版本: {current_version}")
        print(f"   字段长度: {current_length}")
        print(f"   请手动检查数据库状态")


if __name__ == "__main__":
    asyncio.run(main())