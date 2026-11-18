"""Produtos router: CRUD operations and ingredient associations with Eager Loading (preventing N+1)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.api.database import get_db
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import (
    CategoriaModel,
    IngredienteModel,
    IngredienteProdutoModel,
    ProdutoModel,
    UsuarioModel,
)
from src.api.schemas import (
    IngredienteProduto,
    IngredienteProdutoVinculo,
    Produto,
    ProdutoInput,
)
from src.api.security import require_roles

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("", response_model=List[Produto], summary="Listar produtos")
def list_produtos(
    id_categoria: Optional[int] = Query(None, description="Filtrar por categoria"),
    disponivel: Optional[bool] = Query(
        None, description="Filtrar pela disponibilidade"
    ),
    db: Session = Depends(get_db),
):
    """Lista todos os produtos aplicando filtros e Eager Loading (selectinload) para evitar N+1."""
    stmt = select(ProdutoModel).options(
        selectinload(ProdutoModel.ingredientes_produto)
    )

    if id_categoria is not None:
        stmt = stmt.where(ProdutoModel.id_categoria == id_categoria)
    if disponivel is not None:
        stmt = stmt.where(ProdutoModel.disponivel == disponivel)

    return db.scalars(stmt).all()


@router.post(
    "",
    response_model=Produto,
    status_code=status.HTTP_201_CREATED,
    summary="Criar produto",
)
def create_produto(payload: ProdutoInput, db: Session = Depends(get_db)):
    """Cadastra um novo produto vinculado a uma categoria existente."""
    categoria = db.scalar(
        select(CategoriaModel).where(
            CategoriaModel.id_categoria == payload.id_categoria
        )
    )
    if not categoria:
        raise BadRequestException(
            detail=f"Categoria com ID {payload.id_categoria} não encontrada."
        )

    novo_prod = ProdutoModel(
        id_categoria=payload.id_categoria,
        nome=payload.nome,
        tamanho=payload.tamanho,
        preco=payload.preco,
        disponivel=payload.disponivel,
    )
    db.add(novo_prod)
    db.commit()
    db.refresh(novo_prod)
    return novo_prod


@router.get("/{id}", response_model=Produto, summary="Buscar produto por ID")
def get_produto(id: int, db: Session = Depends(get_db)):
    """Busca um produto por ID carregando seus vínculos com ingredientes adiantadamente."""
    prod = db.scalar(
        select(ProdutoModel)
        .where(ProdutoModel.id_produto == id)
        .options(selectinload(ProdutoModel.ingredientes_produto))
    )
    if not prod:
        raise NotFoundException(detail=f"Produto com ID {id} não foi encontrado.")
    return prod


@router.put("/{id}", response_model=Produto, summary="Atualizar produto")
def update_produto(id: int, payload: ProdutoInput, db: Session = Depends(get_db)):
    """Atualiza as informações de um produto existente."""
    prod = db.scalar(select(ProdutoModel).where(ProdutoModel.id_produto == id))
    if not prod:
        raise NotFoundException(detail=f"Produto com ID {id} não foi encontrado.")

    if payload.id_categoria != prod.id_categoria:
        cat = db.scalar(
            select(CategoriaModel).where(
                CategoriaModel.id_categoria == payload.id_categoria
            )
        )
        if not cat:
            raise BadRequestException(
                detail=f"Categoria com ID {payload.id_categoria} não encontrada."
            )

    prod.id_categoria = payload.id_categoria
    prod.nome = payload.nome
    prod.tamanho = payload.tamanho
    prod.preco = payload.preco
    prod.disponivel = payload.disponivel

    db.commit()
    db.refresh(prod)
    return prod


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir produto",
)
def delete_produto(
    id: int,
    current_user: UsuarioModel = Depends(require_roles("ADMIN", "FUNCIONARIO")),
    db: Session = Depends(get_db),
):
    """Remove um produto (Requer privilégios ADMIN ou FUNCIONARIO; CLIENTE retorna 403 Forbidden)."""
    prod = db.scalar(select(ProdutoModel).where(ProdutoModel.id_produto == id))
    if not prod:
        raise NotFoundException(detail=f"Produto com ID {id} não foi encontrado.")

    db.delete(prod)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# Sub-rotas: Ingredientes dos Produtos
# ==========================================


@router.get(
    "/{id}/ingredientes",
    response_model=List[IngredienteProduto],
    summary="Listar ingredientes de um produto",
)
def list_ingredientes_produto(id: int, db: Session = Depends(get_db)):
    """Lista todos os ingredientes vinculados a um produto específico."""
    prod = db.scalar(select(ProdutoModel).where(ProdutoModel.id_produto == id))
    if not prod:
        raise NotFoundException(detail=f"Produto com ID {id} não foi encontrado.")

    return db.scalars(
        select(IngredienteProdutoModel).where(
            IngredienteProdutoModel.id_produto == id
        )
    ).all()


@router.post(
    "/{id}/ingredientes",
    response_model=IngredienteProduto,
    status_code=status.HTTP_201_CREATED,
    summary="Vincular ingrediente a produto",
)
def add_ingrediente_produto(
    id: int, payload: IngredienteProdutoVinculo, db: Session = Depends(get_db)
):
    """Vincula um ingrediente ao produto informando a quantidade necessária."""
    prod = db.scalar(select(ProdutoModel).where(ProdutoModel.id_produto == id))
    if not prod:
        raise NotFoundException(detail=f"Produto com ID {id} não foi encontrado.")

    ing = db.scalar(
        select(IngredienteModel).where(
            IngredienteModel.id_ingrediente == payload.id_ingrediente
        )
    )
    if not ing:
        raise BadRequestException(
            detail=f"Ingrediente com ID {payload.id_ingrediente} não foi encontrado."
        )

    vinculo = IngredienteProdutoModel(
        id_produto=id,
        id_ingrediente=payload.id_ingrediente,
        quantidade_necessaria=payload.quantidade_necessaria,
    )
    db.add(vinculo)
    db.commit()
    db.refresh(vinculo)
    return vinculo


@router.delete(
    "/{id}/ingredientes/{idIngrediente}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover ingrediente de um produto",
)
def remove_ingrediente_produto(
    id: int, idIngrediente: int, db: Session = Depends(get_db)
):
    """Remove a vinculação entre o ingrediente e o produto."""
    vinculo = db.scalar(
        select(IngredienteProdutoModel).where(
            IngredienteProdutoModel.id_produto == id,
            IngredienteProdutoModel.id_ingrediente == idIngrediente,
        )
    )
    if not vinculo:
        raise NotFoundException(
            detail=f"Vínculo do ingrediente {idIngrediente} com o produto {id} não foi encontrado."
        )

    db.delete(vinculo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
