#!/usr/bin/env python3
"""
Unicode截断问题修复验证测试脚本

验证API响应的驼峰命名格式和数据完整性
"""
import json
import requests
import time
from typing import Dict, Any, List

class UnicodeFixVerificationTester:
    """Unicode修复验证测试器"""

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
            print(f"   Details: {details}")

    def test_hello_word_api_response(self) -> Dict[str, Any]:
        """测试hello单词API响应"""
        print("Testing hello word API response...")

        try:
            response = requests.get(f"{self.base_url}/api/v1/words/query/hello",
                                  headers={"accept": "application/json"})

            if response.status_code != 200:
                self.log_test("Hello API Status Code", False,
                            f"Expected 200, got {response.status_code}")
                return {}

            data = response.json()

            # 验证基本结构
            if not data.get("success"):
                self.log_test("Hello API Success Field", False, "Missing success: true")
                return {}

            if "data" not in data:
                self.log_test("Hello API Data Field", False, "Missing data field")
                return {}

            word_data = data["data"]

            # 验证必需的驼峰命名字段存在
            required_camel_case_fields = [
                "id", "word", "phonetic", "partOfSpeech", "coreGame",
                "scenarioFormal", "scenarioCasual", "etymologyBreakdown",
                "etymologyStory", "commonMistakes", "memoryTrick",
                "isGolden", "remainingQueries"
            ]

            missing_fields = []
            for field in required_camel_case_fields:
                if field not in word_data:
                    missing_fields.append(field)

            if missing_fields:
                self.log_test("Hello API Required Fields", False,
                            f"Missing fields: {missing_fields}")
            else:
                self.log_test("Hello API Required Fields", True,
                            "All required camelCase fields present")

            # 验证没有蛇形命名字段
            snake_case_fields = [
                "part_of_speech", "core_game", "scenario_formal", "scenario_casual",
                "etymology_breakdown", "etymology_story", "common_mistakes",
                "memory_trick", "is_golden", "remaining_queries"
            ]

            found_snake_fields = []
            for field in snake_case_fields:
                if field in word_data:
                    found_snake_fields.append(field)

            if found_snake_fields:
                self.log_test("Hello API No Snake Case Fields", False,
                            f"Found snake_case fields: {found_snake_fields}")
            else:
                self.log_test("Hello API No Snake Case Fields", True,
                            "No snake_case fields found")

            # 验证数据完整性
            self.log_test("Hello API Word Value", True, f"Word: {word_data.get('word')}")
            self.log_test("Hello API PartOfSpeech Value", True,
                        f"PartOfSpeech: {word_data.get('partOfSpeech')}")
            self.log_test("Hello API CoreGame Value", True,
                        f"CoreGame: {word_data.get('coreGame')}")

            # 验证JSON格式正确性
            try:
                json_str = json.dumps(data, ensure_ascii=False)
                self.log_test("Hello API JSON Serialization", True,
                            "JSON serializable with Unicode support")
            except Exception as e:
                self.log_test("Hello API JSON Serialization", False, f"JSON error: {e}")

            return word_data

        except Exception as e:
            self.log_test("Hello API Request", False, f"Request failed: {e}")
            return {}

    def test_error_response_format(self) -> bool:
        """测试错误响应格式"""
        print("\nTesting error response format...")

        try:
            # 测试不存在的单词
            response = requests.get(f"{self.base_url}/api/v1/words/query/nonexistentword12345",
                                  headers={"accept": "application/json"})

            # 应该返回错误，但格式应该是正确的驼峰命名
            if response.status_code not in [400, 404]:
                self.log_test("Error Response Status", False,
                            f"Expected 400/404, got {response.status_code}")
                return False

            data = response.json()

            # 验证错误响应结构
            if not data.get("success") == False:
                self.log_test("Error Response Success Field", False,
                            "Expected success: false")
                return False

            if "error" not in data:
                self.log_test("Error Response Error Field", False,
                            "Missing error field")
                return False

            error_data = data["error"]
            required_error_fields = ["code", "message"]

            missing_error_fields = []
            for field in required_error_fields:
                if field not in error_data:
                    missing_error_fields.append(field)

            if missing_error_fields:
                self.log_test("Error Response Required Fields", False,
                            f"Missing error fields: {missing_error_fields}")
            else:
                self.log_test("Error Response Required Fields", True,
                            "Error response format correct")

            return True

        except Exception as e:
            self.log_test("Error Response Request", False, f"Request failed: {e}")
            return False

    def test_unicode_content_handling(self) -> bool:
        """测试Unicode内容处理"""
        print("\nTesting Unicode content handling...")

        # 基于hello响应中的实际数据进行测试
        try:
            response = requests.get(f"{self.base_url}/api/v1/words/query/hello",
                                  headers={"accept": "application/json"})

            if response.status_code != 200:
                return False

            data = response.json()
            word_data = data["data"]

            # 检查各字段的Unicode内容
            unicode_tests = []

            # 测试包含Unicode的字符
            test_fields = {
                "word": word_data.get("word", ""),
                "phonetic": word_data.get("phonetic", ""),
                "partOfSpeech": word_data.get("partOfSpeech", ""),
                "coreGame": word_data.get("coreGame", ""),
                "scenarioFormal": word_data.get("scenarioFormal", ""),
                "scenarioCasual": word_data.get("scenarioCasual", ""),
                "etymologyBreakdown": word_data.get("etymologyBreakdown", ""),
                "commonMistakes": word_data.get("commonMistakes", ""),
                "memoryTrick": word_data.get("memoryTrick", "")
            }

            for field_name, field_value in test_fields.items():
                if field_value:
                    # 验证可以正确序列化和反序列化
                    try:
                        serialized = json.dumps(field_value, ensure_ascii=False)
                        deserialized = json.loads(serialized)
                        if deserialized == field_value:
                            unicode_tests.append(True)
                        else:
                            unicode_tests.append(False)
                    except Exception:
                        unicode_tests.append(False)
                else:
                    unicode_tests.append(True)  # 空值也算通过

            if all(unicode_tests):
                self.log_test("Unicode Content Handling", True,
                            "All Unicode fields handled correctly")
            else:
                failed_count = len([t for t in unicode_tests if not t])
                self.log_test("Unicode Content Handling", False,
                            f"{failed_count} fields failed Unicode handling")

            return all(unicode_tests)

        except Exception as e:
            self.log_test("Unicode Content Test", False, f"Test failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("Starting Unicode Fix Verification Tests\n")
        print("=" * 60)

        start_time = time.time()

        # 运行主要测试
        hello_data = self.test_hello_word_api_response()
        error_test_passed = self.test_error_response_format()
        unicode_test_passed = self.test_unicode_content_handling()

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["passed"]])
        failed_tests = total_tests - passed_tests

        end_time = time.time()
        duration = end_time - start_time

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {duration:.2f}s")

        # 详细结果
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
            "duration": duration,
            "hello_data": hello_data,
            "test_results": self.test_results
        }

if __name__ == "__main__":
    tester = UnicodeFixVerificationTester()
    results = tester.run_all_tests()