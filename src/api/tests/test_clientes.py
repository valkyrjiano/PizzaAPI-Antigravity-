"""Tests for Clientes, Funcionarios, and Enderecos CRUD and relationship operations."""

from fastapi.testclient import TestClient


def test_list_clientes(client: TestClient):
    """Test listing all clients."""
    response = client.get("/api/v1/clientes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_cliente_success(client: TestClient):
    """Test creating a new client linked to a new user."""
    # First create user
    user_resp = client.post(
        "/api/v1/usuarios",
        json={
            "email": "cliente_novo@pizzaria.com",
            "senha": "password123",
            "ativo": True,
            "nome_perfil": "CLIENTE",
        },
    )
    user_id = user_resp.json()["id_usuario"]

    cliente_payload = {
        "id_usuario": user_id,
        "nome": "João da Silva",
        "cpf": "123.456.789-00",
        "telefone": "(11) 91234-5678",
    }
    response = client.post("/api/v1/clientes", json=cliente_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "João da Silva"
    assert data["cpf"] == "123.456.789-00"
    assert data["id_usuario"] == user_id


def test_create_cliente_duplicate_cpf(client: TestClient):
    """Test creating a client with duplicate CPF returns 400 Bad Request."""
    user_resp = client.post(
        "/api/v1/usuarios",
        json={
            "email": "cliente_dup@pizzaria.com",
            "senha": "password123",
            "ativo": True,
            "nome_perfil": "CLIENTE",
        },
    )
    user_id = user_resp.json()["id_usuario"]

    # Use seeded CPF: 555.666.777-88
    response = client.post(
        "/api/v1/clientes",
        json={
            "id_usuario": user_id,
            "nome": "Outro Nome",
            "cpf": "555.666.777-88",
        },
    )
    assert response.status_code == 400
    assert response.json()["type"] == "https://api.pizzariabarriga.dev/errors/bad-request"


def test_list_funcionarios(client: TestClient):
    """Test listing all employees."""
    response = client.get("/api/v1/funcionarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["nome"] == "Carlos Pizzaiolo"


def test_enderecos_crud_and_query_filter(client: TestClient):
    """Test Endereco CRUD operations and filtering by ?id_cliente."""
    # 1. Create a new address for client 1
    new_addr = {
        "id_cliente": 1,
        "cep": "04000-000",
        "logradouro": "Av. Paulista",
        "numero": "1500",
        "complemento": "Bloco B",
        "bairro": "Bela Vista",
        "cidade": "São Paulo",
        "uf": "SP",
    }
    create_resp = client.post("/api/v1/enderecos", json=new_addr)
    assert create_resp.status_code == 201
    addr_id = create_resp.json()["id_endereco"]

    # 2. Filter by client 1
    list_resp = client.get("/api/v1/enderecos?id_cliente=1")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data) >= 2
    assert all(end["id_cliente"] == 1 for end in data)

    # 3. Update address
    update_addr = new_addr.copy()
    update_addr["numero"] = "1502"
    put_resp = client.put(f"/api/v1/enderecos/{addr_id}", json=update_addr)
    assert put_resp.status_code == 200
    assert put_resp.json()["numero"] == "1502"

    # 4. Delete address
    del_resp = client.delete(f"/api/v1/enderecos/{addr_id}")
    assert del_resp.status_code == 204
