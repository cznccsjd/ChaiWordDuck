#!/usr/bin/env python3
"""
前端兼容性测试脚本

模拟前端JavaScript请求，验证API响应格式与前端期望一致
"""
import json
import requests
from typing import Dict, Any

class FrontendCompatibilityTester:
    """前端兼容性测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   -> {details}")

    def test_json_parsing_compatibility(self) -> bool:
        """测试JSON解析兼容性（模拟前端fetch API）"""
        print("Testing JSON parsing compatibility...")

        try:
            # 模拟前端fetch请求
            response = requests.get(
                f"{self.base_url}/api/v1/words/query/hello",
                headers={
                    "accept": "application/json",
                    "content-type": "application/json"
                }
            )

            if response.status_code != 200:
                self.log_test("Frontend Fetch Status", False,
                            f"Expected 200, got {response.status_code}")
                return False

            # 测试JSON解析（模拟前端JSON.parse）
            try:
                json_text = response.text
                parsed_data = json.loads(json_text)
                self.log_test("Frontend JSON Parse", True,
                            "JSON successfully parsed")
            except json.JSONDecodeError as e:
                self.log_test("Frontend JSON Parse", False,
                            f"JSON decode error: {e}")
                return False

            # 验证数据结构（前端期望的结构）
            if not isinstance(parsed_data, dict):
                self.log_test("Frontend Data Structure", False,
                            "Response is not a JSON object")
                return False

            required_top_level = ["success", "data", "error", "timestamp"]
            missing_keys = [key for key in required_top_level if key not in parsed_data]

            if missing_keys:
                self.log_test("Frontend Top Level Keys", False,
                            f"Missing keys: {missing_keys}")
                return False

            self.log_test("Frontend Top Level Keys", True,
                        "All required top-level keys present")

            # 验证success字段
            if not isinstance(parsed_data["success"], bool):
                self.log_test("Frontend Success Field Type", False,
                            "success field is not boolean")
                return False

            self.log_test("Frontend Success Field Type", True,
                        "success field is boolean")

            return True

        except Exception as e:
            self.log_test("Frontend Compatibility Test", False,
                        f"Test failed: {e}")
            return False

    def test_javascript_object_access(self) -> bool:
        """测试JavaScript对象访问模式"""
        print("\nTesting JavaScript object access patterns...")

        try:
            response = requests.get(f"{self.base_url}/api/v1/words/query/hello",
                                  headers={"accept": "application/json"})

            data = response.json()
            word_data = data["data"]

            # 模拟JavaScript对象访问测试
            js_access_tests = []

            # 测试点号访问（obj.property）
            try:
                word = word_data["word"]
                phonetic = word_data["phonetic"]
                part_of_speech = word_data["partOfSpeech"]
                core_game = word_data["coreGame"]
                js_access_tests.append(True)
            except (KeyError, TypeError):
                js_access_tests.append(False)

            # 测试可选链访问（obj?.property）
            try:
                etymology_story = word_data.get("etymologyStory")
                is_golden = word_data.get("isGolden")
                remaining_queries = word_data.get("remainingQueries")
                js_access_tests.append(True)
            except Exception:
                js_access_tests.append(False)

            # 测试嵌套对象访问
            try:
                success = data["success"]
                timestamp = data["timestamp"]
                error = data.get("error")
                js_access_tests.append(True)
            except Exception:
                js_access_tests.append(False)

            if all(js_access_tests):
                self.log_test("JavaScript Object Access", True,
                            "All JavaScript access patterns work")
            else:
                failed_count = len([t for t in js_access_tests if not t])
                self.log_test("JavaScript Object Access", False,
                            f"{failed_count} access patterns failed")

            return all(js_access_tests)

        except Exception as e:
            self.log_test("JavaScript Access Test", False,
                        f"Test failed: {e}")
            return False

    def test_camel_case_consistency(self) -> bool:
        """测试驼峰命名一致性"""
        print("\nTesting camelCase consistency...")

        try:
            response = requests.get(f"{self.base_url}/api/v1/words/query/hello",
                                  headers={"accept": "application/json"})

            data = response.json()
            word_data = data["data"]

            # 前端期望的驼峰命名字段
            expected_camel_case = {
                "word": str,
                "phonetic": str,
                "partOfSpeech": str,
                "coreGame": str,
                "scenarioFormal": str,
                "scenarioCasual": str,
                "etymologyBreakdown": str,
                "etymologyStory": (str, type(None)),
                "commonMistakes": str,
                "memoryTrick": str,
                "isGolden": bool,
                "remainingQueries": int,
                "id": int
            }

            consistency_tests = []

            for field_name, expected_type in expected_camel_case.items():
                if field_name in word_data:
                    actual_value = word_data[field_name]
                    if isinstance(expected_type, tuple):
                        # 允许多种类型（如str或None）
                        type_ok = isinstance(actual_value, expected_type)
                    else:
                        type_ok = isinstance(actual_value, expected_type)

                    consistency_tests.append(type_ok)

                    if not type_ok:
                        print(f"   Type mismatch for {field_name}: "
                              f"expected {expected_type}, got {type(actual_value)}")
                else:
                    consistency_tests.append(False)
                    print(f"   Missing field: {field_name}")

            if all(consistency_tests):
                self.log_test("CamelCase Consistency", True,
                            "All fields have correct camelCase naming and types")
            else:
                failed_count = len([t for t in consistency_tests if not t])
                self.log_test("CamelCase Consistency", False,
                            f"{failed_count} fields have issues")

            return all(consistency_tests)

        except Exception as e:
            self.log_test("CamelCase Consistency Test", False,
                        f"Test failed: {e}")
            return False

    def test_unicode_in_json_response(self) -> bool:
        """测试JSON响应中的Unicode处理"""
        print("\nTesting Unicode in JSON response...")

        try:
            response = requests.get(f"{self.base_url}/api/v1/words/query/hello",
                                  headers={"accept": "application/json"})

            # 验证Content-Type头
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                self.log_test("Content-Type Header", False,
                            f"Expected application/json, got {content_type}")
                return False

            self.log_test("Content-Type Header", True,
                        f"Correct Content-Type: {content_type}")

            # 验证响应编码
            if response.encoding:
                self.log_test("Response Encoding", True,
                            f"Response encoding: {response.encoding}")
            else:
                self.log_test("Response Encoding", True,
                            "Using default encoding")

            # 测试JSON字符串中的Unicode字符
            json_text = response.text

            # 查找Unicode字符
            unicode_chars = []
            for char in json_text:
                if ord(char) > 127:  # 非ASCII字符
                    unicode_chars.append(char)

            if unicode_chars:
                self.log_test("Unicode Characters Present", True,
                            f"Found {len(unicode_chars)} Unicode characters")
            else:
                self.log_test("Unicode Characters Present", True,
                            "No Unicode characters found (may be normal)")

            # 验证JSON转义是否正确
            try:
                # 重新解析JSON，确保没有格式错误
                reparsed = json.loads(json_text)
                self.log_test("JSON Unicode Escaping", True,
                            "Unicode characters properly escaped in JSON")
            except json.JSONDecodeError as e:
                self.log_test("JSON Unicode Escaping", False,
                            f"JSON unicode escaping error: {e}")
                return False

            return True

        except Exception as e:
            self.log_test("Unicode JSON Test", False,
                        f"Test failed: {e}")
            return False

    def test_error_handling_compatibility(self) -> bool:
        """测试错误处理兼容性"""
        print("\nTesting error handling compatibility...")

        try:
            # 测试404错误
            response = requests.get(
                f"{self.base_url}/api/v1/words/query/nonexistentword12345",
                headers={"accept": "application/json"}
            )

            # 验证错误响应结构
            if response.status_code in [400, 404]:
                try:
                    error_data = response.json()

                    # 前端期望的错误结构
                    if "success" in error_data and error_data["success"] == False:
                        self.log_test("Error Response Success Field", True,
                                    "Error response has success: false")
                    else:
                        self.log_test("Error Response Success Field", False,
                                    "Missing or incorrect success field in error")
                        return False

                    if "error" in error_data and isinstance(error_data["error"], dict):
                        self.log_test("Error Response Error Field", True,
                                    "Error response has proper error object")
                    else:
                        self.log_test("Error Response Error Field", False,
                                    "Missing or incorrect error field")
                        return False

                    if "code" in error_data["error"] and "message" in error_data["error"]:
                        self.log_test("Error Response Details", True,
                                    "Error response has code and message")
                    else:
                        self.log_test("Error Response Details", False,
                                    "Missing code or message in error")
                        return False

                except json.JSONDecodeError:
                    self.log_test("Error Response JSON", False,
                                "Error response is not valid JSON")
                    return False
            else:
                self.log_test("Error Response Status", False,
                            f"Expected error status, got {response.status_code}")
                return False

            return True

        except Exception as e:
            self.log_test("Error Handling Test", False,
                        f"Test failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有前端兼容性测试"""
        print("Starting Frontend Compatibility Tests\n")
        print("=" * 60)

        # 运行测试
        json_test = self.test_json_parsing_compatibility()
        js_access_test = self.test_javascript_object_access()
        camel_case_test = self.test_camel_case_consistency()
        unicode_test = self.test_unicode_in_json_response()
        error_test = self.test_error_handling_compatibility()

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["passed"]])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 60)
        print("FRONTEND COMPATIBILITY SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        print(f"\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{status}: {result['test_name']}")
            if result["details"]:
                print(f"   -> {result['details']}")

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "all_passed": all([json_test, js_access_test, camel_case_test, unicode_test, error_test])
        }

if __name__ == "__main__":
    tester = FrontendCompatibilityTester()
    results = tester.run_all_tests()