"""Enderecos router: CRUD operations for Endereco entity."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import BadRequestException, NotFoundException
from src.api.models import ClienteModel, EnderecoModel
from src.api.schemas import Endereco, EnderecoInput

router = APIRouter(prefix="/enderecos", tags=["Endereços"])


@router.get("", response_model=List[Endereco], summary="Listar endereços")
def list_enderecos(
    id_cliente: Optional[int] = Query(None, description="Filtrar por cliente"),
    db: Session = Depends(get_db),
):
    """Retorna endereços cadastrados, opcionalmente filtrados por cliente."""
    stmt = select(EnderecoModel)
    if id_cliente is not None:
        stmt = stmt.where(EnderecoModel.id_cliente == id_cliente)
    return db.scalars(stmt).all()


@router.post(
    "",
    response_model=Endereco,
    status_code=status.HTTP_201_CREATED,
    summary="Criar endereço",
)
def create_endereco(payload: EnderecoInput, db: Session = Depends(get_db)):
    """Cadastra um novo endereço vinculado a um cliente existente."""
    cliente = db.scalar(
        select(ClienteModel).where(ClienteModel.id_cliente == payload.id_cliente)
    )
    if not cliente:
        raise BadRequestException(
            detail=f"Cliente com ID {payload.id_cliente} não foi encontrado."
        )

    novo_end = EnderecoModel(
        id_cliente=payload.id_cliente,
        cep=payload.cep,
        logradouro=payload.logradouro,
        numero=payload.numero,
        complemento=payload.complemento,
        bairro=payload.bairro,
        cidade=payload.cidade,
        uf=payload.uf.upper(),
    )
    db.add(novo_end)
    db.commit()
    db.refresh(novo_end)
    return novo_end


@router.get("/{id}", response_model=Endereco, summary="Buscar endereço por ID")
def get_endereco(id: int, db: Session = Depends(get_db)):
    """Busca um endereço pelo seu identificador primário."""
    end = db.scalar(select(EnderecoModel).where(EnderecoModel.id_endereco == id))
    if not end:
        raise NotFoundException(detail=f"Endereço com ID {id} não foi encontrado.")
    return end


@router.put("/{id}", response_model=Endereco, summary="Atualizar endereço")
def update_endereco(id: int, payload: EnderecoInput, db: Session = Depends(get_db)):
    """Atualiza as informações de um endereço existente."""
    end = db.scalar(select(EnderecoModel).where(EnderecoModel.id_endereco == id))
    if not end:
        raise NotFoundException(detail=f"Endereço com ID {id} não foi encontrado.")

    if payload.id_cliente != end.id_cliente:
        cliente = db.scalar(
            select(ClienteModel).where(ClienteModel.id_cliente == payload.id_cliente)
        )
        if not cliente:
            raise BadRequestException(
                detail=f"Cliente com ID {payload.id_cliente} não foi encontrado."
            )

    end.id_cliente = payload.id_cliente
    end.cep = payload.cep
    end.logradouro = payload.logradouro
    end.numero = payload.numero
    end.complemento = payload.complemento
    end.bairro = payload.bairro
    end.cidade = payload.cidade
    end.uf = payload.uf.upper()

    db.commit()
    db.refresh(end)
    return end


@router.delete(
    ("/{id}"),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir endereço",
)
def delete_endereco(id: int, db: Session = Depends(get_db)):
    """Remove um endereço do banco de dados."""
    end = db.scalar(select(EnderecoModel).where(EnderecoModel.id_endereco == id))
    if not end:
        raise NotFoundException(detail=f"Endereço com ID {id} não foi encontrado.")

    db.delete(end)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
