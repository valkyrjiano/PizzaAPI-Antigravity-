"""Tests for Authentication, JWT generation, /auth/me, and RBAC authorization."""

import pytest
from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    """Test successful login returning JWT access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@pizzaria.com", "senha": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_login_invalid_password(client: TestClient):
    """Test login failure with wrong password returns 401 RFC 9457."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@pizzaria.com", "senha": "wrongpassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/unauthorized"
    assert data["title"] == "Unauthorized"
    assert data["status"] == 401
    assert "Credenciais inválidas" in data["detail"]


def test_login_user_not_found(client: TestClient):
    """Test login failure with non-existent email returns 401 RFC 9457."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@pizzaria.com", "senha": "admin123"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/unauthorized"
    assert data["status"] == 401


def test_auth_me_success(client: TestClient, admin_headers: dict):
    """Test GET /auth/me with valid Bearer token."""
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@pizzaria.com"
    assert data["nome_perfil"] == "ADMIN"
    assert data["role"] == "ADMIN"
    assert data["ativo"] is True


def test_auth_me_missing_token(client: TestClient):
    """Test GET /auth/me without token returns 401 RFC 9457."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/unauthorized"
    assert data["status"] == 401
    assert data["instance"] == "/api/v1/auth/me"


def test_auth_me_invalid_token(client: TestClient, invalid_token_headers: dict):
    """Test GET /auth/me with invalid/malformed token returns 401 RFC 9457."""
    response = client.get("/api/v1/auth/me", headers=invalid_token_headers)
    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/unauthorized"
    assert data["status"] == 401


def test_rbac_cliente_forbidden_delete_product(
    client: TestClient, cliente_headers: dict
):
    """Test that a CLIENTE user cannot delete a product (returns 403 Forbidden RFC 9457)."""
    response = client.delete("/api/v1/produtos/1", headers=cliente_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/forbidden"
    assert data["title"] == "Forbidden"
    assert data["status"] == 403
    assert "Acesso negado" in data["detail"]
    assert data["instance"] == "/api/v1/produtos/1"


def test_rbac_admin_authorized_delete_product(
    client: TestClient, admin_headers: dict
):
    """Test that an ADMIN user is authorized to delete a product (returns 204 No Content)."""
    response = client.delete("/api/v1/produtos/1", headers=admin_headers)
    assert response.status_code == 204
