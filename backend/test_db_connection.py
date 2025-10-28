#!/usr/bin/env python3
"""
简单的数据库连接测试脚本
"""
import asyncio
import asyncpg
import sys

async def test_database_connection():
    """测试数据库连接"""
    try:
        # 使用.env中的数据库URL
        database_url = "postgresql://postgres:password@localhost:5432/chaiword_duck"
        print(f"正在连接数据库: {database_url}")

        conn = await asyncpg.connect(database_url)
        print("✅ 数据库连接成功!")

        # 测试一个简单查询
        result = await conn.fetchval("SELECT version()")
        print(f"📊 PostgreSQL版本: {result}")

        await conn.close()
        print("✅ 数据库连接已关闭")
        return True

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    sys.exit(0 if success else 1)