"""Categorias router: CRUD operations for Categoria entity."""

from typing import List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import CategoriaModel
from src.api.schemas import Categoria, CategoriaInput

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("", response_model=List[Categoria], summary="Listar categorias")
def list_categorias(db: Session = Depends(get_db)):
    """Retorna todas as categorias cadastradas."""
    return db.scalars(select(CategoriaModel)).all()


@router.post(
    "",
    response_model=Categoria,
    status_code=status.HTTP_201_CREATED,
    summary="Criar categoria",
)
def create_categoria(payload: CategoriaInput, db: Session = Depends(get_db)):
    """Cria uma nova categoria de produto."""
    existing = db.scalar(
        select(CategoriaModel).where(CategoriaModel.nome == payload.nome)
    )
    if existing:
        raise BadRequestException(
            detail=f"Já existe uma categoria cadastrada com o nome '{payload.nome}'."
        )

    nova_cat = CategoriaModel(nome=payload.nome, descricao=payload.descricao)
    db.add(nova_cat)
    db.commit()
    db.refresh(nova_cat)
    return nova_cat


@router.get("/{id}", response_model=Categoria, summary="Buscar categoria por ID")
def get_categoria(id: int, db: Session = Depends(get_db)):
    """Busca uma categoria pelo seu identificador primário."""
    cat = db.scalar(
        select(CategoriaModel).where(CategoriaModel.id_categoria == id)
    )
    if not cat:
        raise NotFoundException(detail=f"Categoria com ID {id} não foi encontrada.")
    return cat


@router.put("/{id}", response_model=Categoria, summary="Atualizar categoria")
def update_categoria(
    id: int, payload: CategoriaInput, db: Session = Depends(get_db)
):
    """Atualiza o nome ou descrição de uma categoria."""
    cat = db.scalar(
        select(CategoriaModel).where(CategoriaModel.id_categoria == id)
    )
    if not cat:
        raise NotFoundException(detail=f"Categoria com ID {id} não foi encontrada.")

    if payload.nome != cat.nome:
        existing = db.scalar(
            select(CategoriaModel).where(CategoriaModel.nome == payload.nome)
        )
        if existing:
            raise BadRequestException(
                detail=f"Já existe outra categoria com o nome '{payload.nome}'."
            )

    cat.nome = payload.nome
    cat.descricao = payload.descricao
    db.commit()
    db.refresh(cat)
    return cat


@router.delete(
    ("/{id}"),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir categoria",
)
def delete_categoria(id: int, db: Session = Depends(get_db)):
    """Remove uma categoria do banco de dados."""
    cat = db.scalar(
        select(CategoriaModel).where(CategoriaModel.id_categoria == id)
    )
    if not cat:
        raise NotFoundException(detail=f"Categoria com ID {id} não foi encontrada.")

    db.delete(cat)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
