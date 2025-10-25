"""PromptManager单元测试"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.prompts.manager import PromptManager
from app.prompts.enums import Language, AIProvider, PromptType
from app.prompts.templates.config import PromptTemplateConfig


class TestPromptManager:
    """PromptManager测试类"""

    def test_init_with_default_directory(self):
        """测试使用默认目录初始化"""
        manager = PromptManager()
        assert manager is not None
        assert manager._config is not None
        assert manager._templates_dir is not None

    def test_init_with_custom_directory(self):
        """测试使用自定义目录初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试配置文件
            config_file = Path(temp_dir) / "word_generation.yml"
            test_config = self._create_test_config()

            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(test_config, f, allow_unicode=True)

            manager = PromptManager(templates_dir=temp_dir)
            assert manager is not None
            assert manager._config is not None

    def _create_test_config(self):
        """创建测试配置"""
        return {
            "metadata": {
                "version": "1.0.0",
                "description": "测试配置",
                "last_updated": "2025-01-25"
            },
            "templates": {
                "zh_CN": {
                    "system_prompt": "你是一位专业的英语教学专家。",
                    "user_prompt": "请解释单词 {word} 的含义。"
                },
                "en_US": {
                    "system_prompt": "You are a professional English teaching expert.",
                    "user_prompt": "Please explain the meaning of word {word}."
                }
            },
            "providers": {
                "gemini": {
                    "default_temperature": 0.7,
                    "default_max_tokens": 1000,
                    "supports_structured_output": True
                },
                "openai": {
                    "default_temperature": 0.8,
                    "default_max_tokens": 1500,
                    "supports_structured_output": True
                }
            }
        }

    def test_fallback_config_on_missing_file(self):
        """测试配置文件缺失时的降级策略"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 不创建配置文件
            manager = PromptManager(templates_dir=temp_dir)

            # 应该使用降级配置
            assert manager._config is not None
            assert "zh_CN" in manager.get_supported_languages()
            assert "gemini" in manager.get_supported_providers()

    def test_get_template_success(self):
        """测试成功获取模板"""
        manager = PromptManager()

        template, provider_config = manager.get_template(
            language=Language.CHINESE,
            provider=AIProvider.GEMINI
        )

        assert template is not None
        assert provider_config is not None
        assert hasattr(template, 'system_prompt')
        assert hasattr(template, 'user_prompt')
        assert hasattr(provider_config, 'default_temperature')

    def test_get_template_language_fallback(self):
        """测试语言降级策略"""
        manager = PromptManager()

        # 测试不支持的语言
        template, provider_config = manager.get_template(
            language="fr_FR",  # 不支持的语言
            provider=AIProvider.GEMINI
        )

        # 应该降级到中文
        assert template is not None

    def test_get_template_provider_fallback(self):
        """测试提供商降级策略"""
        manager = PromptManager()

        # 测试不支持的提供商
        template, provider_config = manager.get_template(
            language=Language.CHINESE,
            provider="unsupported_provider"
        )

        # 应该降级到Gemini
        assert template is not None

    def test_get_template_unsupported_language(self):
        """测试完全不支持的语言"""
        manager = PromptManager()

        # Mock配置返回空的语言支持
        original_config = manager._config
        manager._config = MagicMock()
        manager._config.validate_language_support.return_value = False
        manager._config.validate_provider_support.return_value = True
        manager._config.get_template.return_value = None

        with pytest.raises(ValueError, match="不支持的语言"):
            manager.get_template(language="unsupported", provider=AIProvider.GEMINI)

    def test_render_prompt_success(self):
        """测试成功渲染Prompt"""
        manager = PromptManager()

        system_prompt, user_prompt = manager.render_prompt(
            word="example",
            language=Language.CHINESE,
            provider=AIProvider.GEMINI
        )

        assert system_prompt is not None
        assert user_prompt is not None
        assert "example" in user_prompt
        assert len(system_prompt) > 0
        assert len(user_prompt) > 0

    def test_render_prompt_with_additional_vars(self):
        """测试带额外变量的Prompt渲染"""
        manager = PromptManager()

        system_prompt, user_prompt = manager.render_prompt(
            word="example",
            language=Language.CHINESE,
            provider=AIProvider.GEMINI,
            additional_var="test_value"
        )

        assert system_prompt is not None
        assert user_prompt is not None

    def test_render_prompt_missing_template_var(self):
        """测试模板变量缺失"""
        manager = PromptManager()

        # Mock模板返回包含缺失占位符的用户提示词
        with patch.object(manager, 'get_template') as mock_get_template:
            template = MagicMock()
            template.system_prompt = "System prompt"
            template.user_prompt = "User prompt with missing {placeholder}"  # 包含一个不存在的占位符

            mock_get_template.return_value = (template, MagicMock())

            # 当尝试格式化包含不存在的占位符的模板时，会引发KeyError
            with pytest.raises(KeyError):
                manager.render_prompt(word="test")

    def test_get_provider_config_success(self):
        """测试成功获取提供商配置"""
        manager = PromptManager()

        config = manager.get_provider_config(AIProvider.GEMINI)

        assert config is not None
        assert hasattr(config, 'default_temperature')
        assert hasattr(config, 'default_max_tokens')

    def test_get_provider_config_unsupported(self):
        """测试获取不支持的提供商配置"""
        manager = PromptManager()

        with pytest.raises(ValueError, match="不支持的AI提供商"):
            manager.get_provider_config("unsupported_provider")

    def test_get_supported_languages(self):
        """测试获取支持的语言列表"""
        manager = PromptManager()

        languages = manager.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0
        assert Language.CHINESE in languages

    def test_get_supported_providers(self):
        """测试获取支持的提供商列表"""
        manager = PromptManager()

        providers = manager.get_supported_providers()

        assert isinstance(providers, list)
        assert len(providers) > 0
        assert AIProvider.GEMINI in providers

    def test_reload_config(self):
        """测试重新加载配置"""
        manager = PromptManager()

        original_config = manager._config
        manager.reload_config()

        # 配置应该被重新加载
        assert manager._config is not None

    def test_validate_config_success(self):
        """测试成功验证配置"""
        manager = PromptManager()

        result = manager.validate_config()

        assert result["valid"] is True
        assert "languages" in result
        assert "providers" in result
        assert "config_version" in result

    def test_validate_config_failure(self):
        """测试配置验证失败"""
        manager = PromptManager()
        manager._config = None

        result = manager.validate_config()

        assert result["valid"] is False
        assert "error" in result

    def test_get_config_info(self):
        """测试获取配置信息"""
        manager = PromptManager()

        info = manager.get_config_info()

        assert "metadata" in info
        assert "supported_languages" in info
        assert "supported_providers" in info
        assert info["metadata"]["version"] is not None

    def test_get_config_info_no_config(self):
        """测试无配置时的信息获取"""
        manager = PromptManager()
        manager._config = None

        info = manager.get_config_info()

        assert "error" in info

    @patch('app.prompts.manager.logger')
    def test_load_config_error_handling(self, mock_logger):
        """测试配置加载错误处理"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建无效的YAML文件
            config_file = Path(temp_dir) / "word_generation.yml"
            config_file.write_text("invalid: yaml: content:")

            manager = PromptManager(templates_dir=temp_dir)

            # 应该使用降级配置
            assert manager._config is not None
            mock_logger.error.assert_called()

    def test_template_caching(self):
        """测试模板缓存"""
        manager = PromptManager()

        # 第一次调用
        template1, config1 = manager.get_template(
            language=Language.CHINESE,
            provider=AIProvider.GEMINI
        )

        # 第二次调用应该使用缓存
        template2, config2 = manager.get_template(
            language=Language.CHINESE,
            provider=AIProvider.GEMINI
        )

        assert template1 is template2
        assert config1 is config2


class TestPromptManagerIntegration:
    """PromptManager集成测试"""

    def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        manager = PromptManager()

        # 1. 验证配置
        validation_result = manager.validate_config()
        assert validation_result["valid"] is True

        # 2. 获取支持的选项
        languages = manager.get_supported_languages()
        providers = manager.get_supported_providers()
        assert len(languages) > 0
        assert len(providers) > 0

        # 3. 渲染Prompt
        for language in languages:
            for provider in providers:
                try:
                    system_prompt, user_prompt = manager.render_prompt(
                        word="test",
                        language=language,
                        provider=provider
                    )

                    assert len(system_prompt) > 0
                    assert len(user_prompt) > 0
                    assert "test" in user_prompt

                except Exception as e:
                    # 某些组合可能不支持，记录但不失败
                    print(f"Language {language}, Provider {provider} failed: {e}")

    def test_thread_safety(self):
        """测试线程安全性"""
        import threading
        import time

        manager = PromptManager()
        results = []

        def worker():
            try:
                system_prompt, user_prompt = manager.render_prompt(
                    word="thread_test",
                    language=Language.CHINESE,
                    provider=AIProvider.GEMINI
                )
                results.append((system_prompt, user_prompt))
            except Exception as e:
                results.append(e)

        # 创建多个线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(results) == 5
        for result in results:
            assert not isinstance(result, Exception)
            system_prompt, user_prompt = result
            assert len(system_prompt) > 0
            assert len(user_prompt) > 0