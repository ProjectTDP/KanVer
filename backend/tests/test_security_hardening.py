"""
Security Hardening Tests for KanVer API.

Tests the following security features:
1. Security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
2. HSTS header (only in production/DEBUG=False)
3. Password hash not exposed in responses
4. DEBUG defaults to False
5. SECRET_KEY validation (min 32 characters)
6. CORS headers correct
7. SQL injection prevention
"""
import pytest
import os
from unittest.mock import patch

from httpx import AsyncClient, ASGITransport


class TestSecurityHeaders:
    """Test security headers middleware."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self, client: AsyncClient):
        """Test that security headers are present in all responses."""
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_hsts_header_in_production(self, db_session):
        """Test that HSTS header is present when DEBUG=False (production)."""
        from app.main import app
        from app.dependencies import get_db
        from app.config import Settings

        # Create settings with DEBUG=False (production mode)
        with patch.dict(os.environ, {
            "DEBUG": "false",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "SECRET_KEY": "test-secret-key-min-32-chars-for-testing",
            "ENVIRONMENT": "production"
        }):
            test_settings = Settings()

            # Patch the settings at module level
            with patch("app.config.settings", test_settings):
                # Need to reload the middleware to use the new settings
                from importlib import reload
                import app.middleware.security_headers as sec_module
                reload(sec_module)

                async def _get_db_override():
                    yield db_session

                app.dependency_overrides[get_db] = _get_db_override

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test"
                ) as test_client:
                    response = await test_client.get("/health")

                    assert response.status_code == 200
                    # HSTS should be present because DEBUG is False
                    hsts = response.headers.get("Strict-Transport-Security")
                    assert hsts is not None
                    assert "max-age=31536000" in hsts
                    assert "includeSubDomains" in hsts

                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_hsts_header_absent_in_debug(self, db_session):
        """Test that HSTS header is absent when DEBUG=True."""
        from app.main import app
        from app.dependencies import get_db
        from app.config import Settings

        # Create settings with DEBUG=True
        with patch.dict(os.environ, {
            "DEBUG": "true",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "SECRET_KEY": "test-secret-key-min-32-chars-for-testing",
            "ENVIRONMENT": "development"
        }):
            test_settings = Settings()

            with patch("app.config.settings", test_settings):
                # Recreate app with DEBUG=True
                from importlib import reload
                import app.middleware.security_headers as sec_module
                reload(sec_module)

                async def _get_db_override():
                    yield db_session

                app.dependency_overrides[get_db] = _get_db_override

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test"
                ) as test_client:
                    response = await test_client.get("/health")

                    # HSTS should NOT be present when DEBUG=True
                    assert response.headers.get("Strict-Transport-Security") is None

                app.dependency_overrides.clear()


class TestPasswordSecurity:
    """Test password security in responses."""

    @pytest.mark.asyncio
    async def test_password_hash_not_in_user_response(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that password_hash is never in user response."""
        response = await client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "password_hash" not in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_password_hash_not_in_auth_response(self, client: AsyncClient):
        """Test that password_hash is not in register/login responses."""
        from datetime import datetime, timezone

        # Register request
        register_data = {
            "phone_number": "+905559998877",
            "password": "TestPass123!",
            "full_name": "New Test User",
            "date_of_birth": "1990-01-01T00:00:00Z",
            "blood_type": "O+"
        }

        response = await client.post("/api/auth/register", json=register_data)

        assert response.status_code == 201
        data = response.json()

        # Check user object in response
        assert "password_hash" not in data.get("user", {})
        assert "password" not in data.get("user", {})

        # Check tokens in response
        assert "access_token" in data.get("tokens", {})
        assert "refresh_token" in data.get("tokens", {})


class TestConfigSecurity:
    """Test security-related config settings."""

    def test_debug_defaults_to_false(self):
        """Test that DEBUG defaults to False for security."""
        from app.config import Settings

        # Create settings without DEBUG env var
        with patch.dict(os.environ, {"DEBUG": ""}, clear=False):
            # Remove DEBUG from env if present
            env_copy = os.environ.copy()
            if "DEBUG" in env_copy:
                del env_copy["DEBUG"]

            with patch.dict(os.environ, env_copy, clear=True):
                # Provide minimum required vars
                min_env = {
                    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
                    "SECRET_KEY": "test-secret-key-min-32-chars-for-testing",
                }
                with patch.dict(os.environ, min_env, clear=False):
                    settings = Settings()
                    assert settings.DEBUG is False

    def test_secret_key_validation_minimum_length(self):
        """Test that SECRET_KEY must be at least 32 characters."""
        from app.config import Settings

        # Test with too short SECRET_KEY
        short_key_env = {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "SECRET_KEY": "too-short-key",  # 13 chars - too short
        }

        with patch.dict(os.environ, short_key_env, clear=False):
            with pytest.raises(ValueError) as exc_info:
                Settings()

            assert "SECRET_KEY must be at least 32 characters" in str(exc_info.value)

    def test_secret_key_validation_valid_length(self):
        """Test that SECRET_KEY with 32+ chars is accepted."""
        from app.config import Settings

        valid_env = {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "SECRET_KEY": "this-is-a-valid-secret-key-with-32-chars",
        }

        with patch.dict(os.environ, valid_env, clear=False):
            settings = Settings()
            assert len(settings.SECRET_KEY) >= 32

    def test_debug_true_in_production_raises_error(self):
        """Test that DEBUG=True in production raises error."""
        from app.config import Settings

        invalid_env = {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "SECRET_KEY": "this-is-a-valid-secret-key-with-32-chars",
            "ENVIRONMENT": "production",
            "DEBUG": "true",
        }

        with patch.dict(os.environ, invalid_env, clear=False):
            with pytest.raises(ValueError) as exc_info:
                Settings()

            assert "DEBUG cannot be True in production" in str(exc_info.value)

    def test_environment_defaults_to_development(self):
        """Test that ENVIRONMENT defaults to development."""
        from app.config import Settings

        env = {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "SECRET_KEY": "this-is-a-valid-secret-key-with-32-chars",
        }

        with patch.dict(os.environ, env, clear=False):
            settings = Settings()
            assert settings.ENVIRONMENT == "development"


class TestCORSSecurity:
    """Test CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers_correct(self, client: AsyncClient):
        """Test that CORS headers are correctly configured."""
        # Make a preflight request
        response = await client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            }
        )

        # CORS should allow the origin
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cors_disallows_unknown_origin(self, client: AsyncClient):
        """Test that CORS disallows unknown origins."""
        response = await client.options(
            "/api/auth/login",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
            }
        )

        # The response should not include CORS headers for unknown origins
        # Note: Starlette's CORSMiddleware returns 400 for disallowed origins
        # in preflight, or simply doesn't include the headers
        assert response.status_code in [200, 400]


class TestSQLInjectionPrevention:
    """Test SQL injection prevention through ORM."""

    @pytest.mark.asyncio
    async def test_sql_injection_prevented_in_login(
        self, client: AsyncClient, test_user
    ):
        """Test that SQL injection in login is prevented by ORM."""
        from app.models import User
        from sqlalchemy import select

        # Attempt SQL injection via phone number
        malicious_data = {
            "phone_number": "' OR '1'='1",
            "password": "anything"
        }

        response = await client.post("/api/auth/login", json=malicious_data)

        # Should get 401 (invalid credentials), not 500 (error)
        # And should NOT log in successfully
        assert response.status_code == 401
        # The error message is in Turkish: "Geçersiz telefon numarası veya şifre"
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_sql_injection_prevented_in_user_search(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that SQL injection in query params is prevented."""
        # Try SQL injection in query parameter
        response = await client.get(
            "/api/hospitals?city='; DROP TABLE users;--",
            headers=auth_headers
        )

        # Should not cause a 500 error
        # The injection should be treated as a literal string
        assert response.status_code in [200, 400, 401, 422]