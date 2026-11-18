"""Tests for Usuario CRUD operations, password hashing, and validations."""

from fastapi.testclient import TestClient


def test_list_usuarios(client: TestClient):
    """Test listing all users."""
    response = client.get("/api/v1/usuarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_create_usuario_success(client: TestClient):
    """Test creating a user with hashed password."""
    payload = {
        "email": "novousuario@pizzaria.com",
        "senha": "senhasegura123",
        "ativo": True,
        "nome_perfil": "CLIENTE",
        "descricao": "Novo cliente de teste",
    }
    response = client.post("/api/v1/usuarios", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id_usuario" in data
    # Password must be hashed, never plain text
    assert data["senha"] != "senhasegura123"
    assert data["senha"].startswith("$2b$") or len(data["senha"]) > 40


def test_create_usuario_duplicate_email(client: TestClient):
    """Test that creating a user with an existing email returns 400 Bad Request RFC 9457."""
    payload = {
        "email": "admin@pizzaria.com",
        "senha": "password123",
        "ativo": True,
        "nome_perfil": "ADMIN",
    }
    response = client.post("/api/v1/usuarios", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/bad-request"
    assert data["status"] == 400


def test_get_usuario_by_id(client: TestClient):
    """Test retrieving a user by ID."""
    response = client.get("/api/v1/usuarios/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id_usuario"] == 1
    assert data["email"] == "admin@pizzaria.com"


def test_get_usuario_not_found(client: TestClient):
    """Test retrieving a non-existent user returns 404 Not Found RFC 9457."""
    response = client.get("/api/v1/usuarios/99999")
    assert response.status_code == 404
    data = response.json()
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/not-found"
    assert data["status"] == 404


def test_update_usuario(client: TestClient):
    """Test updating user attributes."""
    update_payload = {
        "email": "admin_atualizado@pizzaria.com",
        "senha": "novasenha123",
        "ativo": True,
        "nome_perfil": "ADMIN",
        "descricao": "Admin com descrição atualizada",
    }
    response = client.put("/api/v1/usuarios/1", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin_atualizado@pizzaria.com"
    assert data["descricao"] == "Admin com descrição atualizada"


def test_delete_usuario(client: TestClient):
    """Test deleting a user returns 204 No Content."""
    # Create temporary user to delete
    create_resp = client.post(
        "/api/v1/usuarios",
        json={
            "email": "temp_delete@pizzaria.com",
            "senha": "temp_password",
            "ativo": True,
            "nome_perfil": "CLIENTE",
        },
    )
    user_id = create_resp.json()["id_usuario"]

    delete_resp = client.delete(f"/api/v1/usuarios/{user_id}")
    assert delete_resp.status_code == 204

    # Verify user is gone
    get_resp = client.get(f"/api/v1/usuarios/{user_id}")
    assert get_resp.status_code == 404
