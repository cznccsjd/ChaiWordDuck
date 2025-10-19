#!/usr/bin/env python3
"""
Gemini API连接测试脚本 - 简化版
"""
import asyncio
import os
import sys
import time
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions
    print("Google Generative AI package imported successfully")
except ImportError as e:
    print(f"Failed to import Google Generative AI: {e}")
    sys.exit(1)

def test_gemini_api():
    """测试Gemini API连接"""

    # 从环境变量获取API密钥
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyD3LABpAbmDqFaDVFpAi-yPt_33Swq-mmI')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    timeout = int(os.getenv('GEMINI_TIMEOUT', '30'))

    print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"Model: {model_name}")
    print(f"Timeout: {timeout}s")

    if not api_key or api_key == "your-gemini-api-key-here":
        print("ERROR: API key not configured or invalid")
        return False

    try:
        print("\nConfiguring Gemini...")
        genai.configure(api_key=api_key)

        print("Creating model...")
        model = genai.GenerativeModel(model_name)

        # 测试简单的生成请求
        test_prompt = "What is 1+1? Just answer with a number."
        print(f"Sending test request: {test_prompt}")

        start_time = time.time()

        print("Waiting for API response...")
        response = model.generate_content(
            test_prompt,
            request_options={"timeout": timeout}
        )

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"SUCCESS: API call completed in {elapsed_time:.2f}s")
        print(f"Response: {response.text}")

        return True

    except google_exceptions.DeadlineExceeded as e:
        print(f"TIMEOUT: API call timed out: {e}")
        return False

    except google_exceptions.PermissionDenied as e:
        print(f"PERMISSION ERROR: Invalid API key or insufficient permissions: {e}")
        return False

    except google_exceptions.ResourceExhausted as e:
        print(f"QUOTA ERROR: API quota exhausted: {e}")
        return False

    except Exception as e:
        print(f"UNKNOWN ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("Starting Gemini API diagnostic test\n")

    # 测试API调用
    success = test_gemini_api()

    if success:
        print("\nAll tests passed! Gemini API is working correctly.")
    else:
        print("\nTest failed! Need to investigate further.")

    return success

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest script error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)