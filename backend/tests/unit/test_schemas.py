"""
Schema模块单元测试

测试Pydantic模型的验证功能
"""
import pytest
from pydantic import ValidationError

from app.schemas.user import UserRegisterRequest, UserLoginRequest
from app.schemas.common import ErrorDetail, ErrorResponse, SuccessResponse


class TestUserRegisterRequest:
    """用户注册请求schema测试"""

    def test_valid_register_request(self) -> None:
        """测试有效的注册请求"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123",
        }
        request = UserRegisterRequest(**data)

        assert request.email == "test@example.com"
        assert request.password == "SecurePass123"

    def test_invalid_email_format(self) -> None:
        """测试无效邮箱格式"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                email="invalid-email",
                password="SecurePass123",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert errors[0]["type"] == "value_error"
        assert "email" in str(errors[0]["loc"])

    def test_weak_password_too_short(self) -> None:
        """测试密码过短"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                email="test@example.com",
                password="short",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        # 密码验证错误消息在input字段
        assert "password" in str(errors[0]["loc"])

    def test_weak_password_no_letter(self) -> None:
        """测试密码不包含字母"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                email="test@example.com",
                password="12345678",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "password" in str(errors[0]["loc"])

    def test_weak_password_no_number(self) -> None:
        """测试密码不包含数字"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                email="test@example.com",
                password="OnlyLetters",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "password" in str(errors[0]["loc"])


class TestUserLoginRequest:
    """用户登录请求schema测试"""

    def test_valid_login_request(self) -> None:
        """测试有效的登录请求"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123",
        }
        request = UserLoginRequest(**data)

        assert request.email == "test@example.com"
        assert request.password == "SecurePass123"

    def test_invalid_email_format_in_login(self) -> None:
        """测试登录请求中的无效邮箱"""
        with pytest.raises(ValidationError) as exc_info:
            UserLoginRequest(
                email="not-an-email",
                password="SomePass123",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "email" in str(errors[0]["loc"])


class TestErrorResponse:
    """错误响应schema测试"""

    def test_error_response_creation(self) -> None:
        """测试错误响应创建"""
        error = ErrorDetail(
            code="TEST_ERROR",
            message="测试错误消息",
        )
        response = ErrorResponse(
            success=False,
            error=error,
        )

        assert response.success is False
        assert response.error.code == "TEST_ERROR"
        assert response.error.message == "测试错误消息"
        assert response.data is None

    def test_error_response_serialization(self) -> None:
        """测试错误响应序列化"""
        error = ErrorDetail(
            code="TEST_ERROR",
            message="测试错误",
        )
        response = ErrorResponse(
            success=False,
            error=error,
        )

        data = response.model_dump()
        assert data["success"] is False
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["error"]["message"] == "测试错误"
        assert data["data"] is None


class TestSuccessResponse:
    """成功响应schema测试"""

    def test_success_response_creation(self) -> None:
        """测试成功响应创建"""
        response = SuccessResponse(
            data={"user_id": 123, "username": "test"}
        )

        assert response.success is True
        assert response.data["user_id"] == 123
        assert response.data["username"] == "test"
        assert response.error is None

    def test_success_response_serialization(self) -> None:
        """测试成功响应序列化"""
        response = SuccessResponse(
            data={"message": "操作成功"}
        )

        data = response.model_dump()
        assert data["success"] is True
        assert data["data"]["message"] == "操作成功"
        assert data["error"] is None
