import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_root_endpoint():
    """Главная страница (HTML) доступна"""
    async with _client() as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with _client() as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_signup():
    """Test user registration"""
    async with _client() as client:
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "test@example.com",
                "full_name": "Test User",
                "password": "testpass123",
                "tfa_enabled": False,
            },
        )
        assert response.status_code in [200, 400]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials (нужен PostgreSQL)"""
    async with _client() as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "wrongpass",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_docs_available():
    """Test Swagger docs are available"""
    async with _client() as client:
        response = await client.get("/docs")
        assert response.status_code == 200
