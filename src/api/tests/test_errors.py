"""Tests for RFC 9457 / Problem Details specification compliance across all HTTP error codes."""

from fastapi.testclient import TestClient


def test_rfc9457_error_400_bad_request(client: TestClient):
    """Test that malformed JSON body returns 400 with RFC 9457 schema."""
    response = client.post(
        "/api/v1/usuarios",
        content=b"{ invalid json body ",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()

    # RFC 9457 Fields
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/bad-request"
    assert data["title"] == "Bad Request"
    assert data["status"] == 400
    assert "detail" in data and isinstance(data["detail"], str)
    assert data["instance"] == "/api/v1/usuarios"
    assert "invalidParams" in data
    assert isinstance(data["invalidParams"], list)
    assert len(data["invalidParams"]) > 0
    assert "name" in data["invalidParams"][0]
    assert "reason" in data["invalidParams"][0]

    # Must NOT be FastAPI's default format
    assert not (len(data) == 1 and "detail" in data and isinstance(data["detail"], list))


def test_rfc9457_error_401_unauthorized(client: TestClient):
    """Test that missing authorization returns 401 with RFC 9457 schema."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()

    # RFC 9457 Fields
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/unauthorized"
    assert data["title"] == "Unauthorized"
    assert data["status"] == 401
    assert "detail" in data
    assert data["instance"] == "/api/v1/auth/me"


def test_rfc9457_error_403_forbidden(client: TestClient, cliente_headers: dict):
    """Test that insufficient RBAC role returns 403 with RFC 9457 schema."""
    response = client.delete("/api/v1/produtos/1", headers=cliente_headers)
    assert response.status_code == 403
    data = response.json()

    # RFC 9457 Fields
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/forbidden"
    assert data["title"] == "Forbidden"
    assert data["status"] == 403
    assert "detail" in data
    assert data["instance"] == "/api/v1/produtos/1"


def test_rfc9457_error_404_not_found(client: TestClient):
    """Test that non-existent resource returns 404 with RFC 9457 schema."""
    response = client.get("/api/v1/usuarios/999999")
    assert response.status_code == 404
    data = response.json()

    # RFC 9457 Fields
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/not-found"
    assert data["title"] == "Not Found"
    assert data["status"] == 404
    assert "detail" in data
    assert data["instance"] == "/api/v1/usuarios/999999"


def test_rfc9457_error_422_validation_error(client: TestClient):
    """Test that invalid payload structure returns 422 with invalidParams list in RFC 9457 format."""
    # Sending invalid data (invalid email, missing required fields)
    response = client.post(
        "/api/v1/usuarios",
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422
    data = response.json()

    # RFC 9457 Fields
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/validation-error"
    assert data["title"] == "Validation Error"
    assert data["status"] == 422
    assert "detail" in data
    assert data["instance"] == "/api/v1/usuarios"
    assert "invalidParams" in data
    assert isinstance(data["invalidParams"], list)
    assert len(data["invalidParams"]) >= 1

    # Check structure of invalidParams items
    for item in data["invalidParams"]:
        assert "name" in item
        assert "reason" in item
        assert isinstance(item["name"], str)
        assert isinstance(item["reason"], str)

    # Must NOT be default {"detail": [...]}
    assert "type" in data and "title" in data
