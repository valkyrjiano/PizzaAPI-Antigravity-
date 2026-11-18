"""Ingredientes router: CRUD operations for Ingrediente entity."""

from typing import List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import IngredienteModel
from src.api.schemas import Ingrediente, IngredienteInput

router = APIRouter(prefix="/ingredientes", tags=["Ingredientes"])


@router.get("", response_model=List[Ingrediente], summary="Listar ingredientes")
def list_ingredientes(db: Session = Depends(get_db)):
    """Retorna todos os ingredientes em estoque."""
    return db.scalars(select(IngredienteModel)).all()


@router.post(
    "",
    response_model=Ingrediente,
    status_code=status.HTTP_201_CREATED,
    summary="Criar ingrediente",
)
def create_ingrediente(payload: IngredienteInput, db: Session = Depends(get_db)):
    """Cadastra um novo ingrediente no estoque."""
    existing = db.scalar(
        select(IngredienteModel).where(IngredienteModel.nome == payload.nome)
    )
    if existing:
        raise BadRequestException(
            detail=f"Já existe um ingrediente com o nome '{payload.nome}'."
        )

    novo_ing = IngredienteModel(
        nome=payload.nome,
        quantidade_estoque=payload.quantidade_estoque,
        unidade_medida=payload.unidade_medida,
    )
    db.add(novo_ing)
    db.commit()
    db.refresh(novo_ing)
    return novo_ing


@router.get("/{id}", response_model=Ingrediente, summary="Buscar ingrediente por ID")
def get_ingrediente(id: int, db: Session = Depends(get_db)):
    """Busca um ingrediente pelo seu identificador primário."""
    ing = db.scalar(
        select(IngredienteModel).where(IngredienteModel.id_ingrediente == id)
    )
    if not ing:
        raise NotFoundException(detail=f"Ingrediente com ID {id} não foi encontrado.")
    return ing


@router.put("/{id}", response_model=Ingrediente, summary="Atualizar ingrediente")
def update_ingrediente(
    id: int, payload: IngredienteInput, db: Session = Depends(get_db)
):
    """Atualiza o saldo ou atributos de um ingrediente."""
    ing = db.scalar(
        select(IngredienteModel).where(IngredienteModel.id_ingrediente == id)
    )
    if not ing:
        raise NotFoundException(detail=f"Ingrediente com ID {id} não foi encontrado.")

    if payload.nome != ing.nome:
        existing = db.scalar(
            select(IngredienteModel).where(IngredienteModel.nome == payload.nome)
        )
        if existing:
            raise BadRequestException(
                detail=f"Já existe outro ingrediente com o nome '{payload.nome}'."
            )

    ing.nome = payload.nome
    ing.quantidade_estoque = payload.quantidade_estoque
    ing.unidade_medida = payload.unidade_medida

    db.commit()
    db.refresh(ing)
    return ing


@router.delete(
    ("/{id}"),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir ingrediente",
)
def delete_ingrediente(id: int, db: Session = Depends(get_db)):
    """Remove um ingrediente do estoque."""
    ing = db.scalar(
        select(IngredienteModel).where(IngredienteModel.id_ingrediente == id)
    )
    if not ing:
        raise NotFoundException(detail=f"Ingrediente com ID {id} não foi encontrado.")

    db.delete(ing)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
