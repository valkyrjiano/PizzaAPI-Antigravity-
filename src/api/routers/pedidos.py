"""Pedidos router: CRUD operations for Pedidos and sub-routes for Itens de Pedido with Eager Loading (preventing N+1)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.api.database import get_db
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import (
    ClienteModel,
    EnderecoModel,
    FuncionarioModel,
    ItemPedidoModel,
    PedidoModel,
    ProdutoModel,
    StatusModel,
)
from src.api.schemas import (
    ItemPedido,
    ItemPedidoInput,
    Pedido,
    PedidoDetalhado,
    PedidoInput,
)

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.get("", response_model=List[PedidoDetalhado], summary="Listar pedidos")
def list_pedidos(
    id_cliente: Optional[int] = Query(None, description="Filtrar por cliente"),
    id_status: Optional[int] = Query(None, description="Filtrar por status"),
    db: Session = Depends(get_db),
):
    """Retorna listagem de pedidos aplicando filtros e Eager Loading (selectinload) em seus itens."""
    stmt = select(PedidoModel).options(selectinload(PedidoModel.itens))

    if id_cliente is not None:
        stmt = stmt.where(PedidoModel.id_cliente == id_cliente)
    if id_status is not None:
        stmt = stmt.where(PedidoModel.id_status == id_status)

    return db.scalars(stmt).all()


@router.post(
    "",
    response_model=Pedido,
    status_code=status.HTTP_201_CREATED,
    summary="Criar pedido",
)
def create_pedido(payload: PedidoInput, db: Session = Depends(get_db)):
    """Registra um novo pedido validando chaves estrangeiras relacionadas."""
    # Validações relacionais
    cli = db.scalar(
        select(ClienteModel).where(ClienteModel.id_cliente == payload.id_cliente)
    )
    if not cli:
        raise BadRequestException(
            detail=f"Cliente com ID {payload.id_cliente} não foi encontrado."
        )

    func = db.scalar(
        select(FuncionarioModel).where(
            FuncionarioModel.id_funcionario == payload.id_funcionario
        )
    )
    if not func:
        raise BadRequestException(
            detail=f"Funcionário com ID {payload.id_funcionario} não foi encontrado."
        )

    st = db.scalar(
        select(StatusModel).where(StatusModel.id_status == payload.id_status)
    )
    if not st:
        raise BadRequestException(
            detail=f"Status com ID {payload.id_status} não foi encontrado."
        )

    end = db.scalar(
        select(EnderecoModel).where(EnderecoModel.id_endereco == payload.id_endereco)
    )
    if not end:
        raise BadRequestException(
            detail=f"Endereço com ID {payload.id_endereco} não foi encontrado."
        )

    novo_pedido = PedidoModel(
        id_cliente=payload.id_cliente,
        id_funcionario=payload.id_funcionario,
        id_status=payload.id_status,
        id_endereco=payload.id_endereco,
        forma_pagamento=payload.forma_pagamento,
        taxa_entrega=payload.taxa_entrega,
        valor_total=payload.valor_total,
    )
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    return novo_pedido


@router.get("/{id}", response_model=PedidoDetalhado, summary="Buscar pedido por ID")
def get_pedido(id: int, db: Session = Depends(get_db)):
    """Busca um pedido pelo ID com Eager Loading de todos os seus itens vinculados."""
    pedido = db.scalar(
        select(PedidoModel)
        .where(PedidoModel.id_pedido == id)
        .options(selectinload(PedidoModel.itens))
    )
    if not pedido:
        raise NotFoundException(detail=f"Pedido com ID {id} não foi encontrado.")
    return pedido


@router.put("/{id}", response_model=Pedido, summary="Atualizar pedido")
def update_pedido(id: int, payload: PedidoInput, db: Session = Depends(get_db)):
    """Atualiza as informações gerais de um pedido."""
    pedido = db.scalar(select(PedidoModel).where(PedidoModel.id_pedido == id))
    if not pedido:
        raise NotFoundException(detail=f"Pedido com ID {id} não foi encontrado.")

    pedido.id_cliente = payload.id_cliente
    pedido.id_funcionario = payload.id_funcionario
    pedido.id_status = payload.id_status
    pedido.id_endereco = payload.id_endereco
    pedido.forma_pagamento = payload.forma_pagamento
    pedido.taxa_entrega = payload.taxa_entrega
    pedido.valor_total = payload.valor_total

    db.commit()
    db.refresh(pedido)
    return pedido


@router.delete(
    ("/{id}"),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir pedido",
)
def delete_pedido(id: int, db: Session = Depends(get_db)):
    """Cancela/remove um pedido e seus respectivos itens."""
    pedido = db.scalar(select(PedidoModel).where(PedidoModel.id_pedido == id))
    if not pedido:
        raise NotFoundException(detail=f"Pedido com ID {id} não foi encontrado.")

    db.delete(pedido)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# Sub-rotas: Itens dos Pedidos
# ==========================================


@router.get(
    "/{id}/itens",
    response_model=List[ItemPedido],
    summary="Listar itens de um pedido",
)
def list_itens_pedido(id: int, db: Session = Depends(get_db)):
    """Retorna a lista de itens associados a um pedido."""
    pedido = db.scalar(select(PedidoModel).where(PedidoModel.id_pedido == id))
    if not pedido:
        raise NotFoundException(detail=f"Pedido com ID {id} não foi encontrado.")

    return db.scalars(
        select(ItemPedidoModel).where(ItemPedidoModel.id_pedido == id)
    ).all()


@router.post(
    "/{id}/itens",
    response_model=ItemPedido,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar item ao pedido",
)
def add_item_pedido(
    id: int, payload: ItemPedidoInput, db: Session = Depends(get_db)
):
    """Adiciona um item ao pedido calculando o subtotal e atualizando a transação."""
    pedido = db.scalar(select(PedidoModel).where(PedidoModel.id_pedido == id))
    if not pedido:
        raise NotFoundException(detail=f"Pedido com ID {id} não foi encontrado.")

    prod = db.scalar(
        select(ProdutoModel).where(ProdutoModel.id_produto == payload.id_produto)
    )
    if not prod:
        raise BadRequestException(
            detail=f"Produto com ID {payload.id_produto} não foi encontrado."
        )

    item = ItemPedidoModel(
        id_pedido=id,
        id_produto=payload.id_produto,
        quantidade=payload.quantidade,
        preco_unitario=payload.preco_unitario,
        subtotal=payload.subtotal,
        observacao=payload.observacao,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put(
    "/{id}/itens/{idItem}",
    response_model=ItemPedido,
    summary="Atualizar item do pedido",
)
def update_item_pedido(
    id: int,
    idItem: int,
    payload: ItemPedidoInput,
    db: Session = Depends(get_db),
):
    """Atualiza a quantidade, preço unitário, subtotal ou observação de um item do pedido."""
    pedido = db.scalar(select(PedidoModel).where(PedidoModel.id_pedido == id))
    if not pedido:
        raise NotFoundException(detail=f"Pedido com ID {id} não foi encontrado.")

    item = db.scalar(
        select(ItemPedidoModel).where(
            ItemPedidoModel.id_item_pedido == idItem,
            ItemPedidoModel.id_pedido == id,
        )
    )
    if not item:
        raise NotFoundException(
            detail=f"Item com ID {idItem} não pertence ao pedido {id}."
        )

    item.id_produto = payload.id_produto
    item.quantidade = payload.quantidade
    item.preco_unitario = payload.preco_unitario
    item.subtotal = payload.subtotal
    item.observacao = payload.observacao

    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/{id}/itens/{idItem}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover item do pedido",
)
def remove_item_pedido(id: int, idItem: int, db: Session = Depends(get_db)):
    """Remove um item do pedido."""
    pedido = db.scalar(select(PedidoModel).where(PedidoModel.id_pedido == id))
    if not pedido:
        raise NotFoundException(detail=f"Pedido com ID {id} não foi encontrado.")

    item = db.scalar(
        select(ItemPedidoModel).where(
            ItemPedidoModel.id_item_pedido == idItem,
            ItemPedidoModel.id_pedido == id,
        )
    )
    if not item:
        raise NotFoundException(
            detail=f"Item com ID {idItem} não pertence ao pedido {id}."
        )

    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
