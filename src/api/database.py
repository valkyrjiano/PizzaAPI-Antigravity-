"""Database configuration, engine, session factory, dependencies, and seed routines.

Using modern SQLAlchemy 2.0.
"""

from typing import Generator
import bcrypt
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./pizzaria.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy 2.0 models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    """Hash password using bcrypt safely."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def init_db() -> None:
    """Create all database tables."""
    # Import models here to register them with Base.metadata before creating tables
    from src.api import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def seed_db(db: Session = None) -> None:
    """Seed initial data for testing and development in an idempotent way."""
    from src.api.models import (
        CategoriaModel,
        ClienteModel,
        EnderecoModel,
        FuncionarioModel,
        IngredienteModel,
        IngredienteProdutoModel,
        ProdutoModel,
        StatusModel,
        UsuarioModel,
    )

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # 1. Seed Usuários
        admin_user = db.scalar(
            select(UsuarioModel).where(UsuarioModel.email == "admin@pizzaria.com")
        )
        if not admin_user:
            admin_user = UsuarioModel(
                email="admin@pizzaria.com",
                senha=hash_password("admin123"),
                ativo=True,
                nome_perfil="ADMIN",
                descricao="Administrador do Sistema",
            )
            db.add(admin_user)

        func_user = db.scalar(
            select(UsuarioModel).where(UsuarioModel.email == "func@pizzaria.com")
        )
        if not func_user:
            func_user = UsuarioModel(
                email="func@pizzaria.com",
                senha=hash_password("func123"),
                ativo=True,
                nome_perfil="FUNCIONARIO",
                descricao="Funcionário da Cozinha / Balcão",
            )
            db.add(func_user)

        cliente_user = db.scalar(
            select(UsuarioModel).where(UsuarioModel.email == "cliente@pizzaria.com")
        )
        if not cliente_user:
            cliente_user = UsuarioModel(
                email="cliente@pizzaria.com",
                senha=hash_password("cliente123"),
                ativo=True,
                nome_perfil="CLIENTE",
                descricao="Cliente Comprador",
            )
            db.add(cliente_user)

        db.flush()

        # 2. Seed Funcionário vinculado
        func_record = db.scalar(
            select(FuncionarioModel).where(FuncionarioModel.id_usuario == func_user.id_usuario)
        )
        if not func_record:
            func_record = FuncionarioModel(
                id_usuario=func_user.id_usuario,
                nome="Carlos Pizzaiolo",
                cpf="111.222.333-44",
                cargo="Pizzaiolo Chefe",
                telefone="(11) 98888-1111",
            )
            db.add(func_record)

        # 3. Seed Cliente vinculado
        cliente_record = db.scalar(
            select(ClienteModel).where(ClienteModel.id_usuario == cliente_user.id_usuario)
        )
        if not cliente_record:
            cliente_record = ClienteModel(
                id_usuario=cliente_user.id_usuario,
                nome="Maria Oliveira",
                cpf="555.666.777-88",
                telefone="(11) 97777-2222",
            )
            db.add(cliente_record)
            db.flush()

        # 4. Seed Endereço vinculado ao cliente
        endereco_record = db.scalar(
            select(EnderecoModel).where(EnderecoModel.id_cliente == cliente_record.id_cliente)
        )
        if not endereco_record:
            endereco_record = EnderecoModel(
                id_cliente=cliente_record.id_cliente,
                cep="01001-000",
                logradouro="Praça da Sé",
                numero="100",
                complemento="Apto 12",
                bairro="Sé",
                cidade="São Paulo",
                uf="SP",
            )
            db.add(endereco_record)

        # 5. Seed Status de Pedidos
        status_nomes = [
            "Recebido",
            "Em Preparo",
            "Pronto",
            "Em Rota",
            "Entregue",
            "Cancelado",
        ]
        for nome_st in status_nomes:
            st = db.scalar(select(StatusModel).where(StatusModel.nome_status == nome_st))
            if not st:
                db.add(StatusModel(nome_status=nome_st))

        # 6. Seed Categorias
        cat_salgada = db.scalar(
            select(CategoriaModel).where(CategoriaModel.nome == "Pizzas Salgadas")
        )
        if not cat_salgada:
            cat_salgada = CategoriaModel(
                nome="Pizzas Salgadas",
                descricao="Pizzas tradicionais salgadas",
            )
            db.add(cat_salgada)

        cat_doce = db.scalar(
            select(CategoriaModel).where(CategoriaModel.nome == "Pizzas Doces")
        )
        if not cat_doce:
            cat_doce = CategoriaModel(
                nome="Pizzas Doces",
                descricao="Pizzas artesanais doces",
            )
            db.add(cat_doce)

        cat_bebidas = db.scalar(
            select(CategoriaModel).where(CategoriaModel.nome == "Bebidas")
        )
        if not cat_bebidas:
            cat_bebidas = CategoriaModel(
                nome="Bebidas",
                descricao="Refrigerantes, sucos e águas",
            )
            db.add(cat_bebidas)

        db.flush()

        # 7. Seed Ingredientes
        ingredientes_data = [
            ("Massa Tradicional", 100.0, "kg"),
            ("Molho de Tomate", 50.0, "kg"),
            ("Queijo Mussarela", 80.0, "kg"),
            ("Calabresa Fatiada", 40.0, "kg"),
            ("Cebola Fatiada", 25.0, "kg"),
        ]
        ingredientes_map = {}
        for nome_ing, qtd, unid in ingredientes_data:
            ing = db.scalar(select(IngredienteModel).where(IngredienteModel.nome == nome_ing))
            if not ing:
                ing = IngredienteModel(
                    nome=nome_ing,
                    quantidade_estoque=qtd,
                    unidade_medida=unid,
                )
                db.add(ing)
                db.flush()
            ingredientes_map[nome_ing] = ing

        # 8. Seed Produto (Pizza de Calabresa)
        pizza_calabresa = db.scalar(
            select(ProdutoModel).where(ProdutoModel.nome == "Pizza Calabresa")
        )
        if not pizza_calabresa:
            pizza_calabresa = ProdutoModel(
                id_categoria=cat_salgada.id_categoria,
                nome="Pizza Calabresa",
                tamanho="Grande",
                preco=45.00,
                disponivel=True,
            )
            db.add(pizza_calabresa)
            db.flush()

            # Vincular ingredientes à pizza de calabresa
            if "Massa Tradicional" in ingredientes_map:
                db.add(
                    IngredienteProdutoModel(
                        id_produto=pizza_calabresa.id_produto,
                        id_ingrediente=ingredientes_map["Massa Tradicional"].id_ingrediente,
                        quantidade_necessaria=0.35,
                    )
                )
            if "Calabresa Fatiada" in ingredientes_map:
                db.add(
                    IngredienteProdutoModel(
                        id_produto=pizza_calabresa.id_produto,
                        id_ingrediente=ingredientes_map["Calabresa Fatiada"].id_ingrediente,
                        quantidade_necessaria=0.20,
                    )
                )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if should_close:
            db.close()
