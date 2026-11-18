"""Status router: CRUD operations for Status entity."""

from typing import List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import StatusModel
from src.api.schemas import Status, StatusInput

router = APIRouter(prefix="/status", tags=["Status"])


@router.get("", response_model=List[Status], summary="Listar status de pedidos")
def list_status(db: Session = Depends(get_db)):
    """Retorna todos os status de pedidos cadastrados."""
    return db.scalars(select(StatusModel)).all()


@router.post(
    "",
    response_model=Status,
    status_code=status.HTTP_201_CREATED,
    summary="Criar status",
)
def create_status(payload: StatusInput, db: Session = Depends(get_db)):
    """Cadastra um novo status de pedido."""
    existing = db.scalar(
        select(StatusModel).where(StatusModel.nome_status == payload.nome_status)
    )
    if existing:
        raise BadRequestException(
            detail=f"Já existe um status cadastrado como '{payload.nome_status}'."
        )

    novo_status = StatusModel(nome_status=payload.nome_status)
    db.add(novo_status)
    db.commit()
    db.refresh(novo_status)
    return novo_status


@router.get("/{id}", response_model=Status, summary="Buscar status por ID")
def get_status(id: int, db: Session = Depends(get_db)):
    """Busca um status pelo seu identificador primário."""
    st = db.scalar(select(StatusModel).where(StatusModel.id_status == id))
    if not st:
        raise NotFoundException(detail=f"Status com ID {id} não foi encontrado.")
    return st


@router.put("/{id}", response_model=Status, summary="Atualizar status")
def update_status(id: int, payload: StatusInput, db: Session = Depends(get_db)):
    """Atualiza a descrição de um status."""
    st = db.scalar(select(StatusModel).where(StatusModel.id_status == id))
    if not st:
        raise NotFoundException(detail=f"Status com ID {id} não foi encontrado.")

    if payload.nome_status != st.nome_status:
        existing = db.scalar(
            select(StatusModel).where(
                StatusModel.nome_status == payload.nome_status
            )
        )
        if existing:
            raise BadRequestException(
                detail=f"Já existe outro status cadastrado como '{payload.nome_status}'."
            )

    st.nome_status = payload.nome_status
    db.commit()
    db.refresh(st)
    return st


@router.delete(
    ("/{id}"),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir status",
)
def delete_status(id: int, db: Session = Depends(get_db)):
    """Remove um status do banco de dados."""
    st = db.scalar(select(StatusModel).where(StatusModel.id_status == id))
    if not st:
        raise NotFoundException(detail=f"Status com ID {id} não foi encontrado.")

    db.delete(st)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
