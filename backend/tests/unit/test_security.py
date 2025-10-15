"""
安全模块单元测试

测试密码加密、JWT token生成和验证功能
"""
import pytest
from datetime import timedelta
from jose import JWTError

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """密码哈希测试"""

    def test_get_password_hash(self) -> None:
        """测试密码哈希生成"""
        password = "SecurePass123"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_verify_password_correct(self) -> None:
        """测试正确密码验证"""
        password = "SecurePass123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """测试错误密码验证"""
        password = "SecurePass123"
        wrong_password = "WrongPass456"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_hash_different_each_time(self) -> None:
        """测试相同密码每次哈希结果不同（salt随机性）"""
        password = "SecurePass123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """JWT token测试"""

    def test_create_access_token(self) -> None:
        """测试JWT token创建"""
        data = {"sub": "123"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self) -> None:
        """测试自定义过期时间的JWT token"""
        data = {"sub": "123"}
        expires_delta = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=expires_delta)

        assert token is not None
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "123"

    def test_decode_access_token(self) -> None:
        """测试JWT token解码"""
        data = {"sub": "123", "username": "testuser"}
        token = create_access_token(data)

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["username"] == "testuser"
        assert "exp" in payload  # 包含过期时间

    def test_decode_invalid_token(self) -> None:
        """测试无效JWT token解码"""
        invalid_token = "invalid.token.here"

        # 现在应该抛出JWTError而不是返回None
        with pytest.raises(JWTError):
            decode_access_token(invalid_token)

    def test_decode_token_with_invalid_signature(self) -> None:
        """测试签名错误的JWT token"""
        # 创建正常token，然后修改最后几位（破坏签名）
        data = {"sub": "123"}
        token = create_access_token(data)
        tampered_token = token[:-10] + "AAAAAAAAAA"

        # 现在应该抛出JWTError而不是返回None
        with pytest.raises(JWTError):
            decode_access_token(tampered_token)
