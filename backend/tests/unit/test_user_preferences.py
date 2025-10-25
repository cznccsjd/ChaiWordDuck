"""
用户偏好设置功能的单元测试

测试用户语言偏好的数据验证、模型操作等
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserPreferencesResponse, UserPreferencesUpdateRequest


class TestUserModel:
    """用户模型语言偏好相关测试"""

    async def test_user_model_with_preferred_language_default(self, test_db: AsyncSession):
        """测试用户模型默认语言偏好"""
        from app.core.security import get_password_hash

        user = User(
            email="test@example.com",
            password_hash=get_password_hash("TestPass123"),
            membership_tier="free",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # 检查默认值
        assert hasattr(user, 'preferred_language')
        assert user.preferred_language == "zh_CN"

    async def test_user_model_with_preferred_language_explicit(self, test_db: AsyncSession):
        """测试用户模型显式设置语言偏好"""
        from app.core.security import get_password_hash

        user = User(
            email="test2@example.com",
            password_hash=get_password_hash("TestPass123"),
            membership_tier="free",
            preferred_language="en_US",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        assert user.preferred_language == "en_US"

    async def test_user_model_invalid_language(self, test_db: AsyncSession):
        """测试用户模型无效语言代码"""
        from app.core.security import get_password_hash
        from sqlalchemy.exc import IntegrityError

        user = User(
            email="test3@example.com",
            password_hash=get_password_hash("TestPass123"),
            membership_tier="free",
            preferred_language="invalid_lang",  # 无效语言代码
        )
        test_db.add(user)

        with pytest.raises(IntegrityError):
            await test_db.commit()

    async def test_update_user_preferred_language(self, test_db: AsyncSession, created_user: User):
        """测试更新用户语言偏好"""
        # 更新语言偏好
        created_user.preferred_language = "en_US"
        created_user.updated_at = datetime.utcnow()
        await test_db.commit()
        await test_db.refresh(created_user)

        assert created_user.preferred_language == "en_US"


class TestUserPreferencesSchemas:
    """用户偏好相关的Pydantic Schema测试"""

    def test_user_preferences_response_valid_data(self):
        """测试用户偏好响应schema的有效数据"""
        data = {
            "id": 1,
            "email": "test@example.com",
            "membership_tier": "free",
            "email_verified": True,
            "preferred_language": "zh_CN",
            "created_at": "2024-01-01T00:00:00",
        }

        response = UserPreferencesResponse(**data)
        assert response.id == 1
        assert response.email == "test@example.com"
        assert response.preferred_language == "zh_CN"

    def test_user_preferences_update_request_valid(self):
        """测试用户偏好更新请求schema"""
        # 测试更新为中文
        request = UserPreferencesUpdateRequest(preferred_language="zh_CN")
        assert request.preferred_language == "zh_CN"

        # 测试更新为英文
        request = UserPreferencesUpdateRequest(preferred_language="en_US")
        assert request.preferred_language == "en_US"

    def test_user_preferences_update_request_invalid_language(self):
        """测试用户偏好更新请求无效语言代码"""
        with pytest.raises(ValueError, match="不支持的语言代码"):
            UserPreferencesUpdateRequest(preferred_language="invalid_lang")

    def test_user_preferences_update_request_empty_language(self):
        """测试用户偏好更新请求空语言代码"""
        with pytest.raises(ValueError, match="preferred_language不能为空"):
            UserPreferencesUpdateRequest(preferred_language="")

    @pytest.mark.parametrize("language", ["zh_CN", "en_US"])
    def test_user_preferences_supported_languages(self, language):
        """测试支持的语言代码"""
        request = UserPreferencesUpdateRequest(preferred_language=language)
        assert request.preferred_language == language


class TestUserPreferencesValidation:
    """用户偏好验证逻辑测试"""

    def test_is_supported_language_zh_cn(self):
        """测试中文语言代码验证"""
        from app.validators.user_preferences import is_supported_language

        assert is_supported_language("zh_CN") is True

    def test_is_supported_language_en_us(self):
        """测试英文语言代码验证"""
        from app.validators.user_preferences import is_supported_language

        assert is_supported_language("en_US") is True

    def test_is_supported_language_invalid(self):
        """测试无效语言代码验证"""
        from app.validators.user_preferences import is_supported_language

        assert is_supported_language("invalid") is False
        assert is_supported_language("zh") is False
        assert is_supported_language("en") is False
        assert is_supported_language("") is False

    def test_validate_preferred_language_valid(self):
        """测试有效语言偏好验证"""
        from app.validators.user_preferences import validate_preferred_language

        assert validate_preferred_language("zh_CN") == "zh_CN"
        assert validate_preferred_language("en_US") == "en_US"

    def test_validate_preferred_language_invalid(self):
        """测试无效语言偏好验证"""
        from app.validators.user_preferences import validate_preferred_language

        with pytest.raises(ValueError, match="不支持的语言代码"):
            validate_preferred_language("invalid")

    def test_get_default_language_for_new_user(self):
        """测试新用户默认语言获取"""
        from app.services.user_preferences import get_default_language_for_new_user

        default_lang = get_default_language_for_new_user()
        assert default_lang == "zh_CN"

    def test_get_user_language_preference_with_value(self, created_user: User):
        """测试获取用户语言偏好（有值的情况）"""
        # 需要先在模型中添加preferred_language字段
        # 这里只是测试逻辑，实际实现会在后续步骤
        from app.services.user_preferences import get_user_language_preference

        # 模拟用户有语言偏好设置
        if hasattr(created_user, 'preferred_language'):
            language = get_user_language_preference(created_user)
            assert language in ["zh_CN", "en_US"]

    def test_get_user_language_preference_fallback(self):
        """测试获取用户语言偏好（回退到默认值）"""
        from app.services.user_preferences import get_user_language_preference

        # 创建一个没有preferred_language属性的用户对象模拟
        class MockUser:
            pass

        user = MockUser()
        language = get_user_language_preference(user)
        assert language == "zh_CN"


class TestGuestLanguagePreferences:
    """游客语言偏好测试"""

    def test_get_language_from_accept_language_header(self):
        """测试从Accept-Language头部获取语言偏好"""
        from app.services.guest_preferences import get_language_from_accept_language

        # 测试中文优先
        language = get_language_from_accept_language("zh-CN,zh;q=0.9,en;q=0.8")
        assert language == "zh_CN"

        # 测试英文优先
        language = get_language_from_accept_language("en-US,en;q=0.9,zh;q=0.8")
        assert language == "en_US"

        # 测试没有头部
        language = get_language_from_accept_language(None)
        assert language == "zh_CN"

    def test_get_language_from_cookie(self):
        """测试从Cookie获取语言偏好"""
        from app.services.guest_preferences import get_language_from_cookie

        # 测试中文Cookie
        cookies = {"language": "zh_CN"}
        language = get_language_from_cookie(cookies)
        assert language == "zh_CN"

        # 测试英文Cookie
        cookies = {"language": "en_US"}
        language = get_language_from_cookie(cookies)
        assert language == "en_US"

        # 测试无效Cookie
        cookies = {"language": "invalid"}
        language = get_language_from_cookie(cookies)
        assert language == "zh_CN"

        # 测试没有Cookie
        language = get_language_from_cookie({})
        assert language == "zh_CN"

    def test_guest_language_preference_priority(self):
        """测试游客语言偏好优先级"""
        from app.services.guest_preferences import get_guest_language_preference

        # Cookie优先于Accept-Language
        headers = {"Accept-Language": "en-US,en;q=0.9"}
        cookies = {"language": "zh_CN"}
        language = get_guest_language_preference(headers, cookies)
        assert language == "zh_CN"

        # 没有Cookie时使用Accept-Language
        headers = {"Accept-Language": "en-US,en;q=0.9"}
        cookies = {}
        language = get_guest_language_preference(headers, cookies)
        assert language == "en_US"

        # 都没有时使用默认值
        language = get_guest_language_preference({}, {})
        assert language == "zh_CN"