#!/usr/bin/env python3
"""
Gemini API连接测试脚本
用于诊断API调用问题
"""
import asyncio
import os
import sys
import time
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('APP_ENV', 'development')

try:
    # import google as genai
    # 官方推荐的 SDK 主模块导入方式
    from google.genai import Client
    from google.genai import types
    from google.api_core import exceptions as google_exceptions
    print("Google Generative AI包导入成功")
except ImportError as e:
    print(f"❌ Google Generative AI包导入失败: {e}")
    sys.exit(1)

async def test_gemini_api():
    """测试Gemini API连接"""

    # 从环境变量获取API密钥
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyD3LABpAbmDqFaDVFpAi-yPt_33Swq-mmI')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    timeout = int(os.getenv('GEMINI_TIMEOUT', '30'))

    print(f"🔑 API密钥: {api_key[:20]}...{api_key[-10:]}")
    print(f"🤖 模型: {model_name}")
    print(f"⏱️ 超时: {timeout}秒")

    if not api_key or api_key == "your-gemini-api-key-here":
        print("❌ API密钥未配置或无效")
        return False

    try:
        # print("\n📡 正在配置Gemini...")
        # genai.configure(api_key=api_key)

        # print("📡 正在创建模型...")
        # model = genai.Client(model_name)

        print("\n📡 正在创建Gemini客户端...")
        # 修正 1 & 2: 使用 http_options 设置超时
        http_config = types.HttpOptions(timeout=timeout)
        # 实例化 Client，它会自动查找 GEMINI_API_KEY 环境变量。
        # 如果您想显式传递，可以这样做：client = Client(api_key=api_key)
        # 但我们使用 env 变量，所以直接实例化即可
        client = Client(api_key=api_key,http_options=http_config)



        # 测试简单的生成请求
        test_prompt = "请回答：1+1等于几？只需要回答数字。"
        # print(f"📝 发送测试请求: {test_prompt}")
        print(f"📝 发送测试请求: {test_prompt} 到模型: {model_name}")

        start_time = time.time()

        print("⏳ 等待API响应...")
        # response = model.generate_content(
        #     test_prompt,
        #     request_options={"timeout": timeout}
        # )
        # 正确的调用方式：通过 client.models 或 client 直接调用
        response = client.models.generate_content(
            model=model_name,  # 传入从 .env 读取的 "gemini-2.5-flash"
            contents=test_prompt
            # request_options={"timeout": timeout}
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"✅ API调用成功！耗时: {elapsed_time:.2f}秒")
        print(f"📄 响应内容: {response.text}")

        return True

    except google_exceptions.DeadlineExceeded as e:
        print(f"❌ API调用超时: {e}")
        return False

    except google_exceptions.PermissionDenied as e:
        print(f"❌ API密钥无效或权限不足: {e}")
        return False

    except google_exceptions.ResourceExhausted as e:
        print(f"❌ API配额用尽: {e}")
        return False

    except Exception as e:
        print(f"❌ 未知错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_network_connectivity():
    """测试网络连接性"""
    import aiohttp

    urls_to_test = [
        "https://generativelanguage.googleapis.com",
        "https://www.googleapis.com",
        "https://google.com"
    ]

    print("\n🌐 测试网络连接性...")

    async with aiohttp.ClientSession() as session:
        for url in urls_to_test:
            try:
                print(f"🔗 测试连接: {url}")
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(f"✅ {url} - 状态码: {response.status}")
            except Exception as e:
                print(f"❌ {url} - 连接失败: {e}")

async def main():
    """主函数"""
    print("🚀 开始Gemini API诊断测试\n")

    # 测试网络连接
    try:
        await test_network_connectivity()
    except Exception as e:
        print(f"⚠️ 网络连接测试失败: {e}")

    # 测试API调用
    success = await test_gemini_api()

    if success:
        print("\n🎉 所有测试通过！Gemini API工作正常。")
    else:
        print("\n💥 测试失败！需要进一步排查问题。")

    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试脚本出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)