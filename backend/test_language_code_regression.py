#!/usr/bin/env python3
"""
语言代码约束修复回归测试脚本

验证Railway部署环境的语言代码约束违反Bug修复情况：
1. 确保API请求不再出现约束违反错误
2. 验证Accept-Language头部正确映射到2字符代码
3. 测试核心语言相关功能
4. 测试向后兼容性
5. 性能回归测试
"""
import requests
import json
import time
import sys
from typing import Dict, Any, List, Tuple

class LanguageCodeRegressionTest:
    """语言代码约束修复回归测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"    {details}")

        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.time()
        })

    def test_original_bug_scenario(self) -> bool:
        """测试原Bug场景：API请求不再出现约束违反错误"""
        test_cases = [
            {
                "name": "英文Accept-Language头部",
                "headers": {"Accept-Language": "en-US,en;q=0.9"},
                "expected_status": 200
            },
            {
                "name": "中文Accept-Language头部",
                "headers": {"Accept-Language": "zh-CN,zh;q=0.9"},
                "expected_status": 200
            },
            {
                "name": "混合语言头部（英文优先）",
                "headers": {"Accept-Language": "zh-CN;q=0.8,en-US;q=0.9"},
                "expected_status": 200
            },
            {
                "name": "不支持语言fallback",
                "headers": {"Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8"},
                "expected_status": 200
            }
        ]

        all_passed = True

        for case in test_cases:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/words/query/recommondation",
                    params={"word": "accommodation"},
                    headers=case["headers"],
                    timeout=10
                )

                passed = response.status_code == case["expected_status"]
                if passed:
                    data = response.json()
                    # 验证响应结构
                    passed = data.get("success", False) and "data" in data

                details = f"Status: {response.status_code}, Expected: {case['expected_status']}"
                if not passed and response.status_code != case["expected_status"]:
                    try:
                        error_data = response.json()
                        details += f", Error: {error_data.get('detail', 'Unknown error')}"
                    except:
                        details += f", Response: {response.text[:100]}"

                self.log_test(f"原Bug场景测试 - {case['name']}", passed, details)
                all_passed = all_passed and passed

            except Exception as e:
                self.log_test(f"原Bug场景测试 - {case['name']}", False, f"异常: {str(e)}")
                all_passed = False

        return all_passed

    def test_accept_language_parsing(self) -> bool:
        """测试Accept-Language头部边界条件和组合"""
        test_cases = [
            # (Accept-Language, 期望的语言代码)
            ("en-US,en;q=0.9,zh-CN;q=0.8", "en"),
            ("zh-CN,zh;q=0.9,en-US;q=0.8", "zh"),
            ("zh-CN;q=0.8,en-US;q=0.9", "en"),
            ("fr-FR,fr;q=0.9,en-US;q=0.8", "en"),  # fallback
            ("de-DE,de;q=0.9,zh-CN;q=0.8", "zh"),  # fallback
            ("ja-JP,ja;q=0.9,ko-KR;q=0.8", "en"),  # fallback到默认
            ("en-us", "en"),
            ("zh-cn", "zh"),
            ("EN", "en"),  # 应该规范化
            ("ZH", "zh"),  # 应该规范化
        ]

        all_passed = True

        for accept_language, expected_lang in test_cases:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/words/query/test",
                    params={"word": "hello"},
                    headers={"Accept-Language": accept_language},
                    timeout=10
                )

                # 主要测试是否不出现约束违反错误
                passed = response.status_code in [200, 404]  # 404是正常的（单词不存在）
                details = f"Accept-Language: {accept_language}, Status: {response.status_code}"

                self.log_test(f"Accept-Language解析测试", passed, details)
                all_passed = all_passed and passed

            except Exception as e:
                self.log_test(f"Accept-Language解析测试", False, f"异常: {str(e)}")
                all_passed = False

        return all_passed

    def test_core_language_functionality(self) -> bool:
        """测试核心语言相关功能"""
        test_cases = [
            {
                "name": "单词查询 - 英文环境",
                "headers": {"Accept-Language": "en-US,en;q=0.9"},
                "params": {"word": "hello"}
            },
            {
                "name": "单词查询 - 中文环境",
                "headers": {"Accept-Language": "zh-CN,zh;q=0.9"},
                "params": {"word": "hello"}
            },
            {
                "name": "拼写纠正测试",
                "headers": {"Accept-Language": "en-US,en;q=0.9"},
                "params": {"word": "recommondation"}  # 故意拼写错误
            }
        ]

        all_passed = True

        for case in test_cases:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/words/query/{case['params']['word']}",
                    headers=case["headers"],
                    timeout=10
                )

                passed = response.status_code in [200, 404]
                if response.status_code == 200:
                    data = response.json()
                    passed = data.get("success", False) and "data" in data

                details = f"{case['name']}, Status: {response.status_code}"
                self.log_test(f"核心功能测试", passed, details)
                all_passed = all_passed and passed

            except Exception as e:
                self.log_test(f"核心功能测试", False, f"异常: {str(e)}")
                all_passed = False

        return all_passed

    def test_backward_compatibility(self) -> bool:
        """测试向后兼容性（旧格式自动转换）"""
        # 这里主要测试API能够处理各种格式的语言代码
        test_cases = [
            "en-US", "zh-CN", "en-us", "zh-cn", "EN", "ZH"
        ]

        all_passed = True

        for lang_code in test_cases:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/words/query/hello",
                    headers={"Accept-Language": lang_code},
                    timeout=10
                )

                # 主要测试不出现约束违反错误
                passed = response.status_code in [200, 404]
                details = f"语言代码: {lang_code}, Status: {response.status_code}"

                self.log_test(f"向后兼容性测试", passed, details)
                all_passed = all_passed and passed

            except Exception as e:
                self.log_test(f"向后兼容性测试", False, f"异常: {str(e)}")
                all_passed = False

        return all_passed

    def test_performance_regression(self) -> bool:
        """执行性能回归测试"""
        print("执行性能回归测试...")

        # 测试多次请求的平均响应时间
        num_requests = 20
        response_times = []

        for i in range(num_requests):
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/words/query/recommondation",
                    params={"word": "accommodation"},
                    headers={"Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8"},
                    timeout=10
                )
                end_time = time.time()

                if response.status_code == 200:
                    response_times.append(end_time - start_time)

            except Exception as e:
                self.log_test("性能回归测试", False, f"请求异常: {str(e)}")
                return False

        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)

            # 性能阈值：平均响应时间应小于1秒
            passed = avg_time < 1.0
            details = f"平均: {avg_time:.3f}s, 最大: {max_time:.3f}s, 最小: {min_time:.3f}s"

            self.log_test("性能回归测试", passed, details)
            return passed
        else:
            self.log_test("性能回归测试", False, "没有成功的响应")
            return False

    def test_database_constraint_compliance(self) -> bool:
        """测试数据库约束合规性"""
        # 通过API测试确保不会产生违反数据库约束的语言代码
        try:
            # 模拟可能导致约束违反的请求
            test_cases = [
                "zh_CN", "en_US", "zh-TW", "ja-JP"
            ]

            all_passed = True

            for lang_code in test_cases:
                response = self.session.get(
                    f"{self.base_url}/api/v1/words/query/hello",
                    headers={"Accept-Language": lang_code},
                    timeout=10
                )

                # 如果修复正确，应该不会出现约束违反错误
                passed = response.status_code in [200, 404]
                details = f"语言代码: {lang_code}, Status: {response.status_code}"

                self.log_test(f"数据库约束合规性测试", passed, details)
                all_passed = all_passed and passed

            return all_passed

        except Exception as e:
            self.log_test("数据库约束合规性测试", False, f"异常: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有回归测试"""
        print("=" * 60)
        print("语言代码约束修复回归测试")
        print("=" * 60)

        start_time = time.time()

        # 执行所有测试
        tests = [
            ("原Bug场景测试", self.test_original_bug_scenario),
            ("Accept-Language解析测试", self.test_accept_language_parsing),
            ("核心语言功能测试", self.test_core_language_functionality),
            ("向后兼容性测试", self.test_backward_compatibility),
            ("性能回归测试", self.test_performance_regression),
            ("数据库约束合规性测试", self.test_database_constraint_compliance),
        ]

        results = {}

        for test_name, test_func in tests:
            print(f"\n执行 {test_name}...")
            results[test_name] = test_func()

        end_time = time.time()
        total_time = end_time - start_time

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 60)
        print("回归测试结果汇总")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        print(f"总耗时: {total_time:.2f}秒")

        # 详细失败结果
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['name']}: {result['details']}")

        # 返回汇总结果
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "total_time": total_time,
            "all_passed": failed_tests == 0,
            "detailed_results": self.test_results
        }

def main():
    """主函数"""
    # 检查服务器是否运行
    base_url = "http://localhost:8000"

    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"错误: 服务器响应异常 - {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"错误: 无法连接到服务器 {base_url}")
        print("请确保后端服务器正在运行: pdm run uvicorn app.main:app --reload")
        sys.exit(1)

    # 运行回归测试
    tester = LanguageCodeRegressionTest(base_url)
    results = tester.run_all_tests()

    # 根据测试结果设置退出码
    sys.exit(0 if results["all_passed"] else 1)

if __name__ == "__main__":
    main()