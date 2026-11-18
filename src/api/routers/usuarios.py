"""Usuarios router: CRUD operations for Usuario entity."""

from typing import List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db, hash_password
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import UsuarioModel
from src.api.schemas import Usuario, UsuarioInput

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get("", response_model=List[Usuario], summary="Listar usuários")
def list_usuarios(db: Session = Depends(get_db)):
    """Retorna a listagem de todos os usuários cadastrados."""
    return db.scalars(select(UsuarioModel)).all()


@router.post(
    "",
    response_model=Usuario,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário",
)
def create_usuario(payload: UsuarioInput, db: Session = Depends(get_db)):
    """Cria um novo usuário criptografando a senha informada."""
    existing = db.scalar(
        select(UsuarioModel).where(UsuarioModel.email == payload.email)
    )
    if existing:
        raise BadRequestException(
            detail=f"Já existe um usuário cadastrado com o e-mail '{payload.email}'."
        )

    novo_usuario = UsuarioModel(
        email=payload.email,
        senha=hash_password(payload.senha),
        ativo=payload.ativo,
        nome_perfil=payload.nome_perfil,
        descricao=payload.descricao,
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@router.get("/{id}", response_model=Usuario, summary="Buscar usuário por ID")
def get_usuario(id: int, db: Session = Depends(get_db)):
    """Busca um usuário pelo seu identificador primário."""
    user = db.scalar(select(UsuarioModel).where(UsuarioModel.id_usuario == id))
    if not user:
        raise NotFoundException(detail=f"Usuário com ID {id} não foi encontrado.")
    return user


@router.put("/{id}", response_model=Usuario, summary="Atualizar usuário")
def update_usuario(id: int, payload: UsuarioInput, db: Session = Depends(get_db)):
    """Atualiza as informações de um usuário existente."""
    user = db.scalar(select(UsuarioModel).where(UsuarioModel.id_usuario == id))
    if not user:
        raise NotFoundException(detail=f"Usuário com ID {id} não foi encontrado.")

    # Verifica se novo e-mail já pertence a outro usuário
    if payload.email != user.email:
        conflict = db.scalar(
            select(UsuarioModel).where(UsuarioModel.email == payload.email)
        )
        if conflict:
            raise BadRequestException(
                detail=f"Já existe outro usuário com o e-mail '{payload.email}'."
            )

    user.email = payload.email
    user.senha = hash_password(payload.senha)
    user.ativo = payload.ativo
    user.nome_perfil = payload.nome_perfil
    user.descricao = payload.descricao

    db.commit()
    db.refresh(user)
    return user


@router.delete(
    ("/{id}"),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir usuário",
)
def delete_usuario(id: int, db: Session = Depends(get_db)):
    """Remove um usuário do banco de dados."""
    user = db.scalar(select(UsuarioModel).where(UsuarioModel.id_usuario == id))
    if not user:
        raise NotFoundException(detail=f"Usuário com ID {id} não foi encontrado.")

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
