import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns API information."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "KanVer API"
    assert data["version"] == "0.1.0"
    assert "description" in data
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "kanver-backend"


@pytest.mark.asyncio
async def test_detailed_health_endpoint(client: AsyncClient):
    """Test detailed health check endpoint with database status."""
    response = await client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["service"] == "kanver-backend"
    assert "database" in data
    # Database is now a dict with 'connected' and 'postgis_enabled' keys
    assert isinstance(data["database"], dict)
    assert "connected" in data["database"]
    assert "postgis_enabled" in data["database"]
    # Database may be connected or disconnected in test environment
    assert data["database"]["connected"] in [True, False]
    assert data["database"]["postgis_enabled"] in [True, False]


@pytest.mark.asyncio
async def test_docs_endpoint_redirect(client: AsyncClient):
    """Test that /docs redirects to Swagger UI."""
    response = await client.get("/docs", follow_redirects=False)
    # FastAPI returns 200 for Swagger UI page
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redoc_endpoint_redirect(client: AsyncClient):
    """Test that /redoc redirects to ReDoc documentation."""
    response = await client.get("/redoc", follow_redirects=False)
    # FastAPI returns 200 for ReDoc page
    assert response.status_code == 200
