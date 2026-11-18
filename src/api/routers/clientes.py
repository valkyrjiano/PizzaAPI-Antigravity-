"""Clientes router: CRUD operations for Cliente entity."""

from typing import List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import ClienteModel, UsuarioModel
from src.api.schemas import Cliente, ClienteInput

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=List[Cliente], summary="Listar clientes")
def list_clientes(db: Session = Depends(get_db)):
    """Retorna a listagem de todos os clientes cadastrados."""
    return db.scalars(select(ClienteModel)).all()


@router.post(
    "",
    response_model=Cliente,
    status_code=status.HTTP_201_CREATED,
    summary="Criar cliente",
)
def create_cliente(payload: ClienteInput, db: Session = Depends(get_db)):
    """Cadastra um novo cliente associado a um usuário existente."""
    user = db.scalar(
        select(UsuarioModel).where(UsuarioModel.id_usuario == payload.id_usuario)
    )
    if not user:
        raise BadRequestException(
            detail=f"Usuário associado com ID {payload.id_usuario} não foi encontrado."
        )

    cpf_exists = db.scalar(
        select(ClienteModel).where(ClienteModel.cpf == payload.cpf)
    )
    if cpf_exists:
        raise BadRequestException(
            detail=f"Já existe um cliente cadastrado com o CPF '{payload.cpf}'."
        )

    user_linked = db.scalar(
        select(ClienteModel).where(ClienteModel.id_usuario == payload.id_usuario)
    )
    if user_linked:
        raise BadRequestException(
            detail=f"O usuário com ID {payload.id_usuario} já está vinculado a outro cliente."
        )

    novo_cliente = ClienteModel(
        id_usuario=payload.id_usuario,
        nome=payload.nome,
        cpf=payload.cpf,
        telefone=payload.telefone,
    )
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    return novo_cliente


@router.get("/{id}", response_model=Cliente, summary="Buscar cliente por ID")
def get_cliente(id: int, db: Session = Depends(get_db)):
    """Busca um cliente pelo seu identificador primário."""
    cliente = db.scalar(select(ClienteModel).where(ClienteModel.id_cliente == id))
    if not cliente:
        raise NotFoundException(detail=f"Cliente com ID {id} não foi encontrado.")
    return cliente


@router.put("/{id}", response_model=Cliente, summary="Atualizar cliente")
def update_cliente(id: int, payload: ClienteInput, db: Session = Depends(get_db)):
    """Atualiza as informações cadastrais de um cliente."""
    cliente = db.scalar(select(ClienteModel).where(ClienteModel.id_cliente == id))
    if not cliente:
        raise NotFoundException(detail=f"Cliente com ID {id} não foi encontrado.")

    if payload.id_usuario != cliente.id_usuario:
        user = db.scalar(
            select(UsuarioModel).where(UsuarioModel.id_usuario == payload.id_usuario)
        )
        if not user:
            raise BadRequestException(
                detail=f"Usuário associado com ID {payload.id_usuario} não foi encontrado."
            )

    if payload.cpf != cliente.cpf:
        cpf_exists = db.scalar(
            select(ClienteModel).where(ClienteModel.cpf == payload.cpf)
        )
        if cpf_exists:
            raise BadRequestException(
                detail=f"Já existe outro cliente cadastrado com o CPF '{payload.cpf}'."
            )

    cliente.id_usuario = payload.id_usuario
    cliente.nome = payload.nome
    cliente.cpf = payload.cpf
    cliente.telefone = payload.telefone

    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete(
    ("/{id}"),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir cliente",
)
def delete_cliente(id: int, db: Session = Depends(get_db)):
    """Remove um cliente e seus endereços vinculados."""
    cliente = db.scalar(select(ClienteModel).where(ClienteModel.id_cliente == id))
    if not cliente:
        raise NotFoundException(detail=f"Cliente com ID {id} não foi encontrado.")

    db.delete(cliente)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
