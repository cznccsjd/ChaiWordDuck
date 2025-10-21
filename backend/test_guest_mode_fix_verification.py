#!/usr/bin/env python3
"""
游客模式认证修复验证脚本

手动验证游客模式认证修复是否成功
"""
import asyncio
import httpx
from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_guest_mode_fix():
    """测试游客模式认证修复"""
    print("游客模式认证修复验证")
    print("=" * 50)

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:

        print("\n测试场景1: 游客访问不存在的单词ID")
        print("-" * 40)
        response = await client.get("/api/v1/words/99999")
        print(f"状态码: {response.status_code}")
        if response.status_code == 404:
            print("正确返回404而不是401 (认证问题已修复)")
        else:
            print(f"错误: 期望404，实际返回{response.status_code}")

        print("\n测试场景2: 创建测试单词")
        print("-" * 40)
        # 先创建一个测试单词（通过查询API，这会触发AI生成或从缓存获取）
        try:
            query_response = await client.get("/api/v1/words/query/testguest")
            print(f"查询单词状态码: {query_response.status_code}")

            if query_response.status_code == 200:
                word_data = query_response.json()
                word_id = word_data["data"]["id"]
                print(f"成功创建/获取测试单词，ID: {word_id}")

                print("\n测试场景3: 游客通过ID获取单词详情")
                print("-" * 40)
                detail_response = await client.get(f"/api/v1/words/{word_id}")
                print(f"状态码: {detail_response.status_code}")

                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print("游客成功获取单词详情!")
                    print(f"   单词: {detail_data['data']['word']}")
                    print(f"   核心游戏: {detail_data['data']['coreGame']}")
                    print(f"   音标: {detail_data['data'].get('phonetic', 'N/A')}")
                else:
                    print(f"错误: 期望200，实际返回{detail_response.status_code}")
                    print(f"   响应: {detail_response.text}")
            else:
                print(f"创建测试单词失败: {query_response.status_code}")
                print(f"   响应: {query_response.text}")

        except Exception as e:
            print(f"创建测试单词时出现异常: {str(e)}")

        print("\n测试场景4: 使用无效token访问")
        print("-" * 40)
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        try:
            invalid_response = await client.get("/api/v1/words/1", headers=invalid_headers)
            print(f"状态码: {invalid_response.status_code}")

            if invalid_response.status_code == 200:
                print("无效token正确降级为游客模式")
            elif invalid_response.status_code == 404:
                print("无效token正确降级为游客模式 (单词不存在，返回404)")
            else:
                print(f"错误: 无效token应该降级为游客模式，实际返回{invalid_response.status_code}")

        except Exception as e:
            print(f"无效token测试时出现异常: {str(e)}")

    print("\n" + "=" * 50)
    print("游客模式认证修复验证完成!")
    print("\n修复总结:")
    print("1. 将 /api/v1/words/{word_id} 端点从强制认证改为可选认证")
    print("2. 使用 get_optional_user 替代 get_current_active_user")
    print("3. 修复日志记录以支持游客模式")
    print("4. 保持与 /api/v1/words/query/{word} 端点的一致性")


if __name__ == "__main__":
    asyncio.run(test_guest_mode_fix())