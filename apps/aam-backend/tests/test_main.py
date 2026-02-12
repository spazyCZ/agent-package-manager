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

    def test_get_scoped_package(self, client: TestClient) -> None:
        """Test getting a scoped package returns 404 for non-existent."""
        response = client.get("/api/v1/packages/@author/my-agent")
        assert response.status_code == 404
        data = response.json()
        assert "@author/my-agent" in data["detail"]

    def test_get_scoped_package_version(self, client: TestClient) -> None:
        """Test getting a scoped package version returns 404 for non-existent."""
        response = client.get("/api/v1/packages/@author/my-agent/1.0.0")
        assert response.status_code == 404
        data = response.json()
        assert "@author/my-agent@1.0.0" in data["detail"]

    def test_list_packages_with_scoped_names(self, client: TestClient) -> None:
        """Test listing packages includes scope field in response schema."""
        response = client.get("/api/v1/packages")
        assert response.status_code == 200
        # The empty list is valid — confirms the endpoint works with the new schema
        data = response.json()
        assert data["packages"] == []

    def test_search_scoped_packages(self, client: TestClient) -> None:
        """Test searching for scoped packages by query."""
        response = client.get("/api/v1/packages/search?q=@author")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "@author"

    def test_scoped_route_does_not_conflict_with_unscoped(
        self, client: TestClient
    ) -> None:
        """Verify scoped and unscoped routes don't collide.

        ``/@scope/name`` should not be interpreted as ``/{name}/{version}``
        because scoped routes are registered first.
        """
        # -----
        # Scoped request — should hit the scoped handler
        # -----
        scoped_resp = client.get("/api/v1/packages/@author/my-agent")
        assert scoped_resp.status_code == 404
        assert "@author/my-agent" in scoped_resp.json()["detail"]

        # -----
        # Unscoped with version — should hit the unscoped version handler
        # -----
        version_resp = client.get("/api/v1/packages/my-agent/1.0.0")
        assert version_resp.status_code == 404
        assert "my-agent@1.0.0" in version_resp.json()["detail"]

    def test_download_scoped_package(self, client: TestClient) -> None:
        """Test download endpoint for scoped packages."""
        response = client.get(
            "/api/v1/packages/@author/my-agent/1.0.0/download"
        )
        assert response.status_code == 404

    def test_delete_scoped_package(self, client: TestClient) -> None:
        """Test deleting a scoped package returns 404 for non-existent."""
        response = client.delete("/api/v1/packages/@author/my-agent")
        assert response.status_code == 404

    def test_delete_scoped_version(self, client: TestClient) -> None:
        """Test deleting a scoped package version returns 404."""
        response = client.delete("/api/v1/packages/@author/my-agent/1.0.0")
        assert response.status_code == 404


class TestNamingUtility:
    """Test the backend naming utility module."""

    def test_unit_parse_unscoped(self) -> None:
        """Test parsing an unscoped package name."""
        from aam_backend.core.naming import parse_package_name

        scope, name = parse_package_name("my-package")
        assert scope == ""
        assert name == "my-package"

    def test_unit_parse_scoped(self) -> None:
        """Test parsing a scoped package name."""
        from aam_backend.core.naming import parse_package_name

        scope, name = parse_package_name("@author/my-package")
        assert scope == "author"
        assert name == "my-package"

    def test_unit_parse_empty_rejects(self) -> None:
        """Test that empty string is rejected."""
        from aam_backend.core.naming import parse_package_name

        with pytest.raises(ValueError, match="must not be empty"):
            parse_package_name("")

    def test_unit_parse_empty_scope_rejects(self) -> None:
        """Test that @/pkg (empty scope) is rejected."""
        from aam_backend.core.naming import parse_package_name

        with pytest.raises(ValueError, match="Scope must not be empty"):
            parse_package_name("@/pkg")

    def test_unit_parse_invalid_scope_rejects(self) -> None:
        """Test that @@bad/pkg (invalid scope) is rejected."""
        from aam_backend.core.naming import parse_package_name

        with pytest.raises(ValueError, match="Invalid scope"):
            parse_package_name("@@bad/pkg")

    def test_unit_validate_unscoped(self) -> None:
        """Test validating an unscoped name."""
        from aam_backend.core.naming import validate_package_name

        assert validate_package_name("my-package") is True

    def test_unit_validate_scoped(self) -> None:
        """Test validating a scoped name."""
        from aam_backend.core.naming import validate_package_name

        assert validate_package_name("@author/my-package") is True

    def test_unit_validate_invalid(self) -> None:
        """Test that invalid names are rejected."""
        from aam_backend.core.naming import validate_package_name

        assert validate_package_name("UPPERCASE") is False
        assert validate_package_name("@/name") is False
        assert validate_package_name("") is False

    def test_unit_format_scoped(self) -> None:
        """Test formatting a scoped name."""
        from aam_backend.core.naming import format_package_name

        assert format_package_name("author", "pkg") == "@author/pkg"

    def test_unit_format_unscoped(self) -> None:
        """Test formatting an unscoped name."""
        from aam_backend.core.naming import format_package_name

        assert format_package_name("", "pkg") == "pkg"

    def test_unit_to_filesystem_scoped(self) -> None:
        """Test filesystem name for scoped packages."""
        from aam_backend.core.naming import to_filesystem_name

        assert to_filesystem_name("author", "asvc-report") == "author--asvc-report"

    def test_unit_to_filesystem_unscoped(self) -> None:
        """Test filesystem name for unscoped packages."""
        from aam_backend.core.naming import to_filesystem_name

        assert to_filesystem_name("", "asvc-report") == "asvc-report"

    def test_unit_scope_allows_underscores(self) -> None:
        """Test that scope allows underscores (npm convention)."""
        from aam_backend.core.naming import parse_package_name

        scope, name = parse_package_name("@my_org/my-package")
        assert scope == "my_org"
        assert name == "my-package"

    def test_unit_name_rejects_underscores(self) -> None:
        """Test that name part rejects underscores."""
        from aam_backend.core.naming import parse_package_name

        with pytest.raises(ValueError, match="Invalid name"):
            parse_package_name("@author/my_package")
