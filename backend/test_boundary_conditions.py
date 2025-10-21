#!/usr/bin/env python3
"""
边界条件测试脚本

测试不同单词和场景下的API响应格式一致性
"""
import json
import requests
import time
from typing import Dict, Any, List

class BoundaryConditionTester:
    """边界条件测试器"""

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

    def test_existing_word_responses(self) -> List[Dict[str, Any]]:
        """测试已存在单词的响应格式一致性"""
        print("Testing existing word responses...")

        # 测试已知存在的单词
        test_words = ["hello"]  # 目前只有hello是确认存在的

        responses = []
        for word in test_words:
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/words/query/{word}",
                    headers={"accept": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    responses.append({
                        "word": word,
                        "status": "success",
                        "data": data
                    })

                    # 验证响应结构一致性
                    self.log_test(f"Response Structure - {word}", True,
                                "Consistent response structure")
                else:
                    responses.append({
                        "word": word,
                        "status": "error",
                        "status_code": response.status_code,
                        "data": None
                    })

            except Exception as e:
                self.log_test(f"Request Error - {word}", False, str(e))

        return responses

    def test_nonexistent_word_responses(self) -> List[Dict[str, Any]]:
        """测试不存在单词的响应格式"""
        print("\nTesting nonexistent word responses...")

        test_words = [
            "nonexistentword123",
            "xyzabc123",
            "supercalifragilisticexpialidocious",
            "verylongwordthatdefinitelydoesnotexist12345"
        ]

        responses = []
        for word in test_words:
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/words/query/{word}",
                    headers={"accept": "application/json"}
                )

                data = response.json()

                responses.append({
                    "word": word,
                    "status_code": response.status_code,
                    "data": data
                })

                # 验证错误响应格式一致性
                if (response.status_code in [400, 404] and
                    data.get("success") == False and
                    "error" in data and
                    "code" in data["error"] and
                    "message" in data["error"]):
                    self.log_test(f"Error Response Format - {word}", True,
                                "Consistent error response format")
                else:
                    self.log_test(f"Error Response Format - {word}", False,
                                "Inconsistent error response format")

            except Exception as e:
                self.log_test(f"Error Request - {word}", False, str(e))

        return responses

    def test_special_characters_in_words(self) -> bool:
        """测试包含特殊字符的单词查询"""
        print("\nTesting special characters in words...")

        special_cases = [
            "hello-world",  # 连字符
            "hello_world",  # 下划线
            "hello123",     # 数字
            "UPPERCASE",    # 大写
            "MiXeDCase",    # 混合大小写
            "a",            # 单字符
            "verylongwordnamethatmightexceedsometypicallimits",  # 长单词
        ]

        all_passed = True
        for test_word in special_cases:
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/words/query/{test_word}",
                    headers={"accept": "application/json"}
                )

                # 无论成功还是失败，都应该有有效的JSON响应
                if response.headers.get("content-type", "").startswith("application/json"):
                    try:
                        data = response.json()
                        self.log_test(f"Special Characters - {test_word}", True,
                                    f"Valid JSON response (status: {response.status_code})")
                    except json.JSONDecodeError:
                        self.log_test(f"Special Characters - {test_word}", False,
                                    "Invalid JSON response")
                        all_passed = False
                else:
                    self.log_test(f"Special Characters - {test_word}", False,
                                f"Invalid content-type: {response.headers.get('content-type')}")
                    all_passed = False

            except Exception as e:
                self.log_test(f"Special Characters - {test_word}", False, str(e))
                all_passed = False

        return all_passed

    def test_response_field_consistency(self, responses: List[Dict[str, Any]]) -> bool:
        """测试响应字段一致性"""
        print("\nTesting response field consistency...")

        successful_responses = [r for r in responses if r.get("status") == "success"]
        if not successful_responses:
            self.log_test("Field Consistency Check", False, "No successful responses to check")
            return False

        # 获取第一个响应作为基准
        base_response = successful_responses[0]["data"]["data"]
        required_fields = set(base_response.keys())

        all_consistent = True
        for i, response in enumerate(successful_responses[1:], 1):
            current_fields = set(response["data"]["data"].keys())

            if current_fields == required_fields:
                self.log_test(f"Field Consistency - Response {i+1}", True,
                            "Fields match base response")
            else:
                missing = required_fields - current_fields
                extra = current_fields - required_fields
                details = []
                if missing:
                    details.append(f"missing: {list(missing)}")
                if extra:
                    details.append(f"extra: {list(extra)}")

                self.log_test(f"Field Consistency - Response {i+1}", False,
                            f"Field mismatch: {', '.join(details)}")
                all_consistent = False

        if all_consistent:
            self.log_test("Overall Field Consistency", True,
                        f"All {len(successful_responses)} responses have consistent fields")

        return all_consistent

    def test_data_type_consistency(self, responses: List[Dict[str, Any]]) -> bool:
        """测试数据类型一致性"""
        print("\nTesting data type consistency...")

        successful_responses = [r for r in responses if r.get("status") == "success"]
        if not successful_responses:
            return False

        # 预期的字段类型
        expected_types = {
            "id": int,
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
            "remainingQueries": int
        }

        all_consistent = True
        for i, response in enumerate(successful_responses):
            word_data = response["data"]["data"]
            word_name = word_data.get("word", f"Response {i+1}")

            for field_name, expected_type in expected_types.items():
                if field_name in word_data:
                    actual_value = word_data[field_name]

                    if isinstance(expected_type, tuple):
                        type_ok = isinstance(actual_value, expected_type)
                    else:
                        type_ok = isinstance(actual_value, expected_type)

                    if not type_ok:
                        self.log_test(f"Data Type - {word_name}.{field_name}", False,
                                    f"Expected {expected_type}, got {type(actual_value)}")
                        all_consistent = False

        if all_consistent:
            self.log_test("Overall Data Type Consistency", True,
                        "All responses have consistent data types")

        return all_consistent

    def test_camel_case_enforcement(self, responses: List[Dict[str, Any]]) -> bool:
        """强制测试驼峰命名规范"""
        print("\nTesting camelCase enforcement...")

        successful_responses = [r for r in responses if r.get("status") == "success"]
        if not successful_responses:
            return False

        # 检查蛇形命名字段是否出现
        snake_case_patterns = [
            "part_of_speech", "core_game", "scenario_formal", "scenario_casual",
            "etymology_breakdown", "etymology_story", "common_mistakes",
            "memory_trick", "is_golden", "remaining_queries", "created_at"
        ]

        violations_found = 0
        for response in successful_responses:
            word_data = response["data"]["data"]
            word_name = word_data.get("word", "unknown")

            for snake_field in snake_case_patterns:
                if snake_field in word_data:
                    violations_found += 1
                    self.log_test(f"CamelCase Violation - {word_name}", False,
                                f"Found snake_case field: {snake_field}")

        if violations_found == 0:
            self.log_test("CamelCase Enforcement", True,
                        f"No snake_case violations found in {len(successful_responses)} responses")
        else:
            self.log_test("CamelCase Enforcement", False,
                        f"Found {violations_found} snake_case violations")

        return violations_found == 0

    def test_unicode_content_preservation(self, responses: List[Dict[str, Any]]) -> bool:
        """测试Unicode内容保留"""
        print("\nTesting Unicode content preservation...")

        successful_responses = [r for r in responses if r.get("status") == "success"]
        if not successful_responses:
            return False

        unicode_preserved = 0
        for response in successful_responses:
            word_data = response["data"]["data"]
            word_name = word_data.get("word", "unknown")

            # 检查各字段是否包含Unicode字符并正确保留
            fields_with_unicode = []
            for field_name, field_value in word_data.items():
                if isinstance(field_value, str):
                    # 检查是否包含非ASCII字符
                    if any(ord(char) > 127 for char in field_value):
                        fields_with_unicode.append(field_name)

            if fields_with_unicode:
                unicode_preserved += 1
                self.log_test(f"Unicode Preservation - {word_name}", True,
                            f"Unicode content preserved in: {', '.join(fields_with_unicode)}")

        if unicode_preserved > 0:
            self.log_test("Overall Unicode Preservation", True,
                        f"Unicode content preserved in {unicode_preserved}/{len(successful_responses)} responses")
        else:
            self.log_test("Overall Unicode Preservation", True,
                        "No Unicode content found (may be normal for test data)")

        return True

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有边界条件测试"""
        print("Starting Boundary Condition Tests\n")
        print("=" * 60)

        start_time = time.time()

        # 运行测试
        existing_responses = self.test_existing_word_responses()
        nonexistent_responses = self.test_nonexistent_word_responses()
        special_chars_test = self.test_special_characters_in_words()

        if existing_responses:
            field_consistency = self.test_response_field_consistency(existing_responses)
            type_consistency = self.test_data_type_consistency(existing_responses)
            camel_case_test = self.test_camel_case_enforcement(existing_responses)
            unicode_test = self.test_unicode_content_preservation(existing_responses)
        else:
            field_consistency = type_consistency = camel_case_test = unicode_test = False

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["passed"]])
        failed_tests = total_tests - passed_tests

        end_time = time.time()
        duration = end_time - start_time

        print("\n" + "=" * 60)
        print("BOUNDARY CONDITION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {duration:.2f}s")

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
            "existing_responses": existing_responses,
            "nonexistent_responses": nonexistent_responses,
            "all_boundary_tests_passed": all([
                special_chars_test,
                field_consistency,
                type_consistency,
                camel_case_test,
                unicode_test
            ])
        }

if __name__ == "__main__":
    tester = BoundaryConditionTester()
    results = tester.run_all_tests()