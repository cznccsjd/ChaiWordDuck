"""
用户认证API测试

测试用户注册、登录、密码找回功能
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class TestUserRegister:
    """用户注册测试"""

    async def test_register_success(self, client: AsyncClient) -> None:
        """测试用户注册成功"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "newuser@example.com"
        assert data["data"]["membership_tier"] == "free"
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        created_user: User,
    ) -> None:
        """测试注册重复邮箱"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": created_user.email,
                "password": "AnotherPass123",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        """测试注册无效邮箱"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    async def test_register_weak_password(self, client: AsyncClient) -> None:
        """测试注册弱密码（少于8位）"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "weak",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    async def test_register_password_without_letter(self, client: AsyncClient) -> None:
        """测试注册密码不包含字母"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "12345678",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "字母" in data["error"]["message"]

    async def test_register_password_without_number(self, client: AsyncClient) -> None:
        """测试注册密码不包含数字"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "OnlyLetters",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "数字" in data["error"]["message"]


class TestUserLogin:
    """用户登录测试"""

    async def test_login_success(
        self,
        client: AsyncClient,
        created_user: User,
        test_user_data: dict,
    ) -> None:
        """测试登录成功"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["user"]["email"] == test_user_data["email"]

    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        created_user: User,
    ) -> None:
        """测试登录错误密码"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": created_user.email,
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_user_not_found(self, client: AsyncClient) -> None:
        """测试登录不存在的用户"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_invalid_email_format(self, client: AsyncClient) -> None:
        """测试登录无效邮箱格式"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "invalid-email",
                "password": "SomePass123",
            },
        )

        assert response.status_code == 422


class TestGetCurrentUser:
    """获取当前用户测试"""

    async def test_get_current_user_success(
        self,
        client: AsyncClient,
        created_user: User,
        auth_headers: dict,
    ) -> None:
        """测试获取当前用户成功"""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == created_user.email
        assert data["data"]["id"] == created_user.id

    async def test_get_current_user_no_token(self, client: AsyncClient) -> None:
        """测试获取当前用户无token"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # HTTPBearer返回403

    async def test_get_current_user_invalid_token(self, client: AsyncClient) -> None:
        """测试获取当前用户无效token"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


class TestPasswordReset:
    """密码找回测试"""

    async def test_password_reset_request_success(
        self,
        client: AsyncClient,
        created_user: User,
    ) -> None:
        """测试密码找回请求成功"""
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": created_user.email},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "邮件已发送" in data["data"]["message"]

    async def test_password_reset_request_user_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        """测试密码找回请求用户不存在（安全考虑，返回成功）"""
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": "nonexistent@example.com"},
        )

        # 安全考虑：不泄露用户是否存在，也返回成功
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.skip(reason="需要实际邮件服务，暂时跳过集成测试")
    async def test_password_reset_confirm_success(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        created_user: User,
    ) -> None:
        """测试密码重置确认成功"""
        # 创建密码重置token
        from datetime import datetime, timedelta
        from app.models import PasswordResetToken
        import secrets

        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=created_user.id,
            email=created_user.email,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        test_db.add(reset_token)
        await test_db.commit()

        # 重置密码
        response = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "token": token,
                "new_password": "NewSecurePass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证可以使用新密码登录
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": created_user.email,
                "password": "NewSecurePass123",
            },
        )
        assert login_response.status_code == 200
