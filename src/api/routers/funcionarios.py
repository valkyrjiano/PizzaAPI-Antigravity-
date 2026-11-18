"""Funcionarios router: CRUD operations for Funcionario entity."""

from typing import List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import FuncionarioModel, UsuarioModel
from src.api.schemas import Funcionario, FuncionarioInput

router = APIRouter(prefix="/funcionarios", tags=["Funcionários"])


@router.get("", response_model=List[Funcionario], summary="Listar funcionários")
def list_funcionarios(db: Session = Depends(get_db)):
    """Retorna todos os funcionários cadastrados."""
    return db.scalars(select(FuncionarioModel)).all()


@router.post(
    "",
    response_model=Funcionario,
    status_code=status.HTTP_201_CREATED,
    summary="Criar funcionário",
)
def create_funcionario(payload: FuncionarioInput, db: Session = Depends(get_db)):
    """Cadastra um novo funcionário associado a um usuário existente."""
    user = db.scalar(
        select(UsuarioModel).where(UsuarioModel.id_usuario == payload.id_usuario)
    )
    if not user:
        raise BadRequestException(
            detail=f"Usuário associado com ID {payload.id_usuario} não existe."
        )

    # Verifica duplicidade de CPF
    cpf_exists = db.scalar(
        select(FuncionarioModel).where(FuncionarioModel.cpf == payload.cpf)
    )
    if cpf_exists:
        raise BadRequestException(
            detail=f"Já existe um funcionário com o CPF '{payload.cpf}'."
        )

    # Verifica se usuário já está associado a outro funcionário
    user_linked = db.scalar(
        select(FuncionarioModel).where(
            FuncionarioModel.id_usuario == payload.id_usuario
        )
    )
    if user_linked:
        raise BadRequestException(
            detail=f"O usuário com ID {payload.id_usuario} já está vinculado a outro funcionário."
        )

    novo_func = FuncionarioModel(
        id_usuario=payload.id_usuario,
        nome=payload.nome,
        cpf=payload.cpf,
        cargo=payload.cargo,
        telefone=payload.telefone,
    )
    db.add(novo_func)
    db.commit()
    db.refresh(novo_func)
    return novo_func


@router.get("/{id}", response_model=Funcionario, summary="Buscar funcionário por ID")
def get_funcionario(id: int, db: Session = Depends(get_db)):
    """Busca um funcionário pelo seu identificador primário."""
    func = db.scalar(
        select(FuncionarioModel).where(FuncionarioModel.id_funcionario == id)
    )
    if not func:
        raise NotFoundException(
            detail=f"Funcionário com ID {id} não foi encontrado."
        )
    return func


@router.put("/{id}", response_model=Funcionario, summary="Atualizar funcionário")
def update_funcionario(
    id: int, payload: FuncionarioInput, db: Session = Depends(get_db)
):
    """Atualiza os dados de um funcionário cadastrado."""
    func = db.scalar(
        select(FuncionarioModel).where(FuncionarioModel.id_funcionario == id)
    )
    if not func:
        raise NotFoundException(
            detail=f"Funcionário com ID {id} não foi encontrado."
        )

    if payload.id_usuario != func.id_usuario:
        user = db.scalar(
            select(UsuarioModel).where(UsuarioModel.id_usuario == payload.id_usuario)
        )
        if not user:
            raise BadRequestException(
                detail=f"Usuário associado com ID {payload.id_usuario} não existe."
            )

    if payload.cpf != func.cpf:
        cpf_exists = db.scalar(
            select(FuncionarioModel).where(FuncionarioModel.cpf == payload.cpf)
        )
        if cpf_exists:
            raise BadRequestException(
                detail=f"Já existe outro funcionário cadastrado com o CPF '{payload.cpf}'."
            )

    func.id_usuario = payload.id_usuario
    func.nome = payload.nome
    func.cpf = payload.cpf
    func.cargo = payload.cargo
    func.telefone = payload.telefone

    db.commit()
    db.refresh(func)
    return func


@router.delete(
    ("/{id}"),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir funcionário",
)
def delete_funcionario(id: int, db: Session = Depends(get_db)):
    """Remove um funcionário do banco de dados."""
    func = db.scalar(
        select(FuncionarioModel).where(FuncionarioModel.id_funcionario == id)
    )
    if not func:
        raise NotFoundException(
            detail=f"Funcionário com ID {id} não foi encontrado."
        )

    db.delete(func)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
