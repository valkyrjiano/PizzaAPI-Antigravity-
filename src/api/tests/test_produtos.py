"""Tests for Categorias, Produtos, and Ingredientes CRUD and N:M relationships with Eager Loading."""

from fastapi.testclient import TestClient


def test_categorias_crud(client: TestClient):
    """Test Categoria CRUD lifecycle."""
    # List
    resp = client.get("/api/v1/categorias")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3

    # Create
    create_resp = client.post(
        "/api/v1/categorias",
        json={"nome": "Sobremesas Especiais", "descricao": "Tortas e mousses"},
    )
    assert create_resp.status_code == 201
    cat_id = create_resp.json()["id_categoria"]

    # Get by ID
    get_resp = client.get(f"/api/v1/categorias/{cat_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["nome"] == "Sobremesas Especiais"

    # Update
    put_resp = client.put(
        f"/api/v1/categorias/{cat_id}",
        json={"nome": "Sobremesas Premium", "descricao": "Doces finos"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["nome"] == "Sobremesas Premium"

    # Delete
    del_resp = client.delete(f"/api/v1/categorias/{cat_id}")
    assert del_resp.status_code == 204


def test_produtos_crud_and_query_filters(client: TestClient, admin_headers: dict):
    """Test Produto CRUD, query filters (?id_categoria, ?disponivel), and Eager Loading."""
    # 1. Create a new product
    prod_payload = {
        "id_categoria": 1,
        "nome": "Pizza Quatro Queijos",
        "tamanho": "Grande",
        "preco": 55.00,
        "disponivel": True,
    }
    create_resp = client.post("/api/v1/produtos", json=prod_payload)
    assert create_resp.status_code == 201
    prod_id = create_resp.json()["id_produto"]

    # 2. Query filter by id_categoria=1
    filter_cat = client.get("/api/v1/produtos?id_categoria=1")
    assert filter_cat.status_code == 200
    assert all(p["id_categoria"] == 1 for p in filter_cat.json())

    # 3. Query filter by disponivel=true
    filter_disp = client.get("/api/v1/produtos?disponivel=true")
    assert filter_disp.status_code == 200
    assert any(p["id_produto"] == prod_id for p in filter_disp.json())

    # 4. Get product by ID (verifying eager loading succeeds)
    get_resp = client.get(f"/api/v1/produtos/{prod_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["nome"] == "Pizza Quatro Queijos"

    # 5. Delete product with Admin privileges
    del_resp = client.delete(f"/api/v1/produtos/{prod_id}", headers=admin_headers)
    assert del_resp.status_code == 204


def test_produto_ingredientes_subroutes(client: TestClient):
    """Test N:M association subroutes: GET, POST, DELETE /produtos/{id}/ingredientes."""
    # 1. List current ingredients for seeded Pizza Calabresa (ID 1)
    list_resp = client.get("/api/v1/produtos/1/ingredientes")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data) >= 1

    # 2. Add Cebola Fatiada (ingrediente 5) to Pizza Calabresa (ID 1)
    add_payload = {
        "id_ingrediente": 5,
        "quantidade_necessaria": 0.10,
    }
    add_resp = client.post("/api/v1/produtos/1/ingredientes", json=add_payload)
    assert add_resp.status_code == 201
    assert add_resp.json()["id_produto"] == 1
    assert add_resp.json()["id_ingrediente"] == 5

    # 3. Delete ingredient 5 from product 1
    del_resp = client.delete("/api/v1/produtos/1/ingredientes/5")
    assert del_resp.status_code == 204

    # 4. Deleting non-linked ingredient returns 404
    del_404 = client.delete("/api/v1/produtos/1/ingredientes/999")
    assert del_404.status_code == 404


def test_ingredientes_crud(client: TestClient):
    """Test Ingrediente CRUD operations."""
    # Create
    create_resp = client.post(
        "/api/v1/ingredientes",
        json={"nome": "Orégano Peruano", "quantidade_estoque": 5.0, "unidade_medida": "kg"},
    )
    assert create_resp.status_code == 201
    ing_id = create_resp.json()["id_ingrediente"]

    # Get
    get_resp = client.get(f"/api/v1/ingredientes/{ing_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["nome"] == "Orégano Peruano"

    # Update
    put_resp = client.put(
        f"/api/v1/ingredientes/{ing_id}",
        json={"nome": "Orégano Fresco", "quantidade_estoque": 6.5, "unidade_medida": "kg"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["quantidade_estoque"] == 6.5

    # Delete
    del_resp = client.delete(f"/api/v1/ingredientes/{ing_id}")
    assert del_resp.status_code == 204
