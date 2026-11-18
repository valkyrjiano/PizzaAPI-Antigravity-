"""SQLAlchemy 2.0 ORM entities for Pizzaria API.

Defines all models with modern DeclarativeBase, Mapped typing, and explicit relationships.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.api.database import Base


class UsuarioModel(Base):
    """Tabela de Usuários para autenticação e RBAC."""

    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    senha: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    nome_perfil: Mapped[str] = mapped_column(String(80), nullable=False)  # ADMIN, FUNCIONARIO, CLIENTE
    descricao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relacionamentos com atores
    funcionario: Mapped[Optional["FuncionarioModel"]] = relationship(
        "FuncionarioModel",
        back_populates="usuario",
        uselist=False,
    )
    cliente: Mapped[Optional["ClienteModel"]] = relationship(
        "ClienteModel",
        back_populates="usuario",
        uselist=False,
    )


class FuncionarioModel(Base):
    """Tabela de Funcionários da Pizzaria."""

    __tablename__ = "funcionarios"

    id_funcionario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    cargo: Mapped[str] = mapped_column(String(80), nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relacionamentos
    usuario: Mapped["UsuarioModel"] = relationship("UsuarioModel", back_populates="funcionario")
    pedidos: Mapped[List["PedidoModel"]] = relationship("PedidoModel", back_populates="funcionario")


class ClienteModel(Base):
    """Tabela de Clientes da Pizzaria."""

    __tablename__ = "clientes"

    id_cliente: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relacionamentos
    usuario: Mapped["UsuarioModel"] = relationship("UsuarioModel", back_populates="cliente")
    enderecos: Mapped[List["EnderecoModel"]] = relationship(
        "EnderecoModel",
        back_populates="cliente",
        cascade="all, delete-orphan",
    )
    pedidos: Mapped[List["PedidoModel"]] = relationship("PedidoModel", back_populates="cliente")


class EnderecoModel(Base):
    """Tabela de Endereços dos Clientes."""

    __tablename__ = "enderecos"

    id_endereco: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("clientes.id_cliente"), nullable=False)
    cep: Mapped[str] = mapped_column(String(9), nullable=False)
    logradouro: Mapped[str] = mapped_column(String(160), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    complemento: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bairro: Mapped[str] = mapped_column(String(100), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)

    # Relacionamentos
    cliente: Mapped["ClienteModel"] = relationship("ClienteModel", back_populates="enderecos")
    pedidos: Mapped[List["PedidoModel"]] = relationship("PedidoModel", back_populates="endereco")


class CategoriaModel(Base):
    """Tabela de Categorias de Produtos."""

    __tablename__ = "categorias"

    id_categoria: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relacionamentos (1:N)
    produtos: Mapped[List["ProdutoModel"]] = relationship(
        "ProdutoModel",
        back_populates="categoria",
        cascade="all, delete-orphan",
    )


class IngredienteModel(Base):
    """Tabela de Ingredientes em Estoque."""

    __tablename__ = "ingredientes"

    id_ingrediente: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    quantidade_estoque: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relacionamentos
    ingredientes_produto: Mapped[List["IngredienteProdutoModel"]] = relationship(
        "IngredienteProdutoModel",
        back_populates="ingrediente",
        cascade="all, delete-orphan",
    )


class ProdutoModel(Base):
    """Tabela de Produtos comercializados."""

    __tablename__ = "produtos"

    id_produto: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categorias.id_categoria"), nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tamanho: Mapped[str] = mapped_column(String(30), nullable=False)
    preco: Mapped[float] = mapped_column(Float, nullable=False)
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    categoria: Mapped["CategoriaModel"] = relationship("CategoriaModel", back_populates="produtos")
    ingredientes_produto: Mapped[List["IngredienteProdutoModel"]] = relationship(
        "IngredienteProdutoModel",
        back_populates="produto",
        cascade="all, delete-orphan",
    )
    itens_pedido: Mapped[List["ItemPedidoModel"]] = relationship(
        "ItemPedidoModel",
        back_populates="produto",
    )


class IngredienteProdutoModel(Base):
    """Tabela associativa N:M entre Produtos e Ingredientes com atributo de quantidade."""

    __tablename__ = "ingrediente_produtos"

    id_ingrediente_produto: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_produto: Mapped[int] = mapped_column(ForeignKey("produtos.id_produto"), nullable=False)
    id_ingrediente: Mapped[int] = mapped_column(ForeignKey("ingredientes.id_ingrediente"), nullable=False)
    quantidade_necessaria: Mapped[float] = mapped_column(Float, nullable=False)

    # Relacionamentos
    produto: Mapped["ProdutoModel"] = relationship("ProdutoModel", back_populates="ingredientes_produto")
    ingrediente: Mapped["IngredienteModel"] = relationship("IngredienteModel", back_populates="ingredientes_produto")


class StatusModel(Base):
    """Tabela de Status dos Pedidos."""

    __tablename__ = "status"

    id_status: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_status: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relacionamentos (1:N)
    pedidos: Mapped[List["PedidoModel"]] = relationship("PedidoModel", back_populates="status")


class PedidoModel(Base):
    """Tabela de Pedidos realizados."""

    __tablename__ = "pedidos"

    id_pedido: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("clientes.id_cliente"), nullable=False)
    id_funcionario: Mapped[int] = mapped_column(ForeignKey("funcionarios.id_funcionario"), nullable=False)
    id_status: Mapped[int] = mapped_column(ForeignKey("status.id_status"), nullable=False)
    id_endereco: Mapped[int] = mapped_column(ForeignKey("enderecos.id_endereco"), nullable=False)
    data_hora_pedido: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    forma_pagamento: Mapped[str] = mapped_column(String(40), nullable=False)
    taxa_entrega: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False)

    # Relacionamentos (1:N para Itens e Many-to-One para Atores e Status)
    cliente: Mapped["ClienteModel"] = relationship("ClienteModel", back_populates="pedidos")
    funcionario: Mapped["FuncionarioModel"] = relationship("FuncionarioModel", back_populates="pedidos")
    status: Mapped["StatusModel"] = relationship("StatusModel", back_populates="pedidos")
    endereco: Mapped["EnderecoModel"] = relationship("EnderecoModel", back_populates="pedidos")
    itens: Mapped[List["ItemPedidoModel"]] = relationship(
        "ItemPedidoModel",
        back_populates="pedido",
        cascade="all, delete-orphan",
    )


class ItemPedidoModel(Base):
    """Tabela de Itens pertencentes a um Pedido."""

    __tablename__ = "item_pedidos"

    id_item_pedido: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_pedido: Mapped[int] = mapped_column(ForeignKey("pedidos.id_pedido"), nullable=False)
    id_produto: Mapped[int] = mapped_column(ForeignKey("produtos.id_produto"), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relacionamentos
    pedido: Mapped["PedidoModel"] = relationship("PedidoModel", back_populates="itens")
    produto: Mapped["ProdutoModel"] = relationship("ProdutoModel", back_populates="itens_pedido")


# Aliases para conformidade com nomenclaturas genéricas de especificações
UserModel = UsuarioModel
ProjectModel = CategoriaModel
TaskModel = PedidoModel
