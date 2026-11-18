"""Tests for Pedidos and Itens de Pedido with Eager Loading (preventing N+1 queries)."""

from fastapi.testclient import TestClient


def test_create_and_get_pedido_eager_loading(client: TestClient):
    """Test creating a Pedido and retrieving it with Eager Loading of its itens."""
    # 1. Create Pedido
    pedido_payload = {
        "id_cliente": 1,
        "id_funcionario": 1,
        "id_status": 1,
        "id_endereco": 1,
        "forma_pagamento": "Pix",
        "taxa_entrega": 6.00,
        "valor_total": 51.00,
    }
    create_resp = client.post("/api/v1/pedidos", json=pedido_payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    pedido_id = data["id_pedido"]
    assert data["valor_total"] == 51.00

    # 2. Add an item to the pedido
    item_payload = {
        "id_produto": 1,
        "quantidade": 1,
        "preco_unitario": 45.00,
        "subtotal": 45.00,
        "observacao": "Sem azeitonas",
    }
    item_resp = client.post(f"/api/v1/pedidos/{pedido_id}/itens", json=item_payload)
    assert item_resp.status_code == 201
    assert item_resp.json()["id_produto"] == 1

    # 3. Retrieve pedido with Eager Loading of itens (verify no N+1 / detached instance issue)
    get_resp = client.get(f"/api/v1/pedidos/{pedido_id}")
    assert get_resp.status_code == 200
    detalhes = get_resp.json()
    assert len(detalhes["itens"]) == 1
    assert detalhes["itens"][0]["observacao"] == "Sem azeitonas"
    assert detalhes["itens"][0]["preco_unitario"] == 45.00


def test_create_pedido_invalid_foreign_key(client: TestClient):
    """Test creating a Pedido with invalid cliente ID returns 400 Bad Request."""
    pedido_payload = {
        "id_cliente": 99999,
        "id_funcionario": 1,
        "id_status": 1,
        "id_endereco": 1,
        "forma_pagamento": "Dinheiro",
        "valor_total": 50.00,
    }
    response = client.post("/api/v1/pedidos", json=pedido_payload)
    assert response.status_code == 400
    data = response.json()
    assert data["type"] == "https://api.pizzariabarriga.dev/errors/bad-request"
    assert "não foi encontrado" in data["detail"]


def test_itens_pedido_subroutes_lifecycle(client: TestClient):
    """Test full lifecycle of subroutes: POST, GET, PUT, DELETE /pedidos/{id}/itens."""
    # 1. Create order
    order_resp = client.post(
        "/api/v1/pedidos",
        json={
            "id_cliente": 1,
            "id_funcionario": 1,
            "id_status": 1,
            "id_endereco": 1,
            "forma_pagamento": "Cartão",
            "taxa_entrega": 0.0,
            "valor_total": 90.0,
        },
    )
    order_id = order_resp.json()["id_pedido"]

    # 2. Add Item 1
    item_resp = client.post(
        f"/api/v1/pedidos/{order_id}/itens",
        json={
            "id_produto": 1,
            "quantidade": 2,
            "preco_unitario": 45.0,
            "subtotal": 90.0,
            "observacao": "Borda recheada",
        },
    )
    assert item_resp.status_code == 201
    item_id = item_resp.json()["id_item_pedido"]

    # 3. List items of order
    list_items = client.get(f"/api/v1/pedidos/{order_id}/itens")
    assert list_items.status_code == 200
    assert len(list_items.json()) == 1

    # 4. Update item
    put_item = client.put(
        f"/api/v1/pedidos/{order_id}/itens/{item_id}",
        json={
            "id_produto": 1,
            "quantidade": 3,
            "preco_unitario": 45.0,
            "subtotal": 135.0,
            "observacao": "Borda vulcão",
        },
    )
    assert put_item.status_code == 200
    assert put_item.json()["quantidade"] == 3
    assert put_item.json()["subtotal"] == 135.0
    assert put_item.json()["observacao"] == "Borda vulcão"

    # 5. Delete item
    del_item = client.delete(f"/api/v1/pedidos/{order_id}/itens/{item_id}")
    assert del_item.status_code == 204

    # 6. Verify items list is empty
    list_after = client.get(f"/api/v1/pedidos/{order_id}/itens")
    assert len(list_after.json()) == 0


def test_update_status_pedido(client: TestClient):
    """Test updating status of an existing order."""
    # Create order
    order_resp = client.post(
        "/api/v1/pedidos",
        json={
            "id_cliente": 1,
            "id_funcionario": 1,
            "id_status": 1,
            "id_endereco": 1,
            "forma_pagamento": "Pix",
            "valor_total": 45.0,
        },
    )
    order_id = order_resp.json()["id_pedido"]

    # Update status to 'Pronto' (id_status 3)
    update_resp = client.put(
        f"/api/v1/pedidos/{order_id}",
        json={
            "id_cliente": 1,
            "id_funcionario": 1,
            "id_status": 3,
            "id_endereco": 1,
            "forma_pagamento": "Pix",
            "taxa_entrega": 0.0,
            "valor_total": 45.0,
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["id_status"] == 3


def test_delete_pedido(client: TestClient):
    """Test canceling / deleting an order."""
    order_resp = client.post(
        "/api/v1/pedidos",
        json={
            "id_cliente": 1,
            "id_funcionario": 1,
            "id_status": 1,
            "id_endereco": 1,
            "forma_pagamento": "Dinheiro",
            "valor_total": 45.0,
        },
    )
    order_id = order_resp.json()["id_pedido"]

    del_resp = client.delete(f"/api/v1/pedidos/{order_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/pedidos/{order_id}")
    assert get_resp.status_code == 404
