"""Tests for main application."""

import pytest
from fastapi.testclient import TestClient

from aam_backend.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root(self, client: TestClient) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AAM Registry API"
        assert "version" in data

    def test_health(self, client: TestClient) -> None:
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_ready(self, client: TestClient) -> None:
        """Test readiness endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_invalid_credentials(self, client: TestClient) -> None:
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_register(self, client: TestClient) -> None:
        """Test user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "username": "newuser",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestPackageEndpoints:
    """Test package endpoints."""

    def test_list_packages(self, client: TestClient) -> None:
        """Test listing packages."""
        response = client.get("/api/v1/packages")
        assert response.status_code == 200
        data = response.json()
        assert "packages" in data
        assert "total" in data

    def test_search_packages(self, client: TestClient) -> None:
        """Test searching packages."""
        response = client.get("/api/v1/packages/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["query"] == "test"

    def test_get_nonexistent_package(self, client: TestClient) -> None:
        """Test getting a package that doesn't exist."""
        response = client.get("/api/v1/packages/nonexistent")
        assert response.status_code == 404
