"""Main application entrypoint for Pizzaria API.

Configures FastAPI instance, lifespan (init_db + seed_db), CORS middleware,
RFC 9457 exception handlers, and inclusion of modular routers under /api/v1.
"""

from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.database import init_db, seed_db
from src.api.exceptions import register_exception_handlers
from src.api.routers import (
    auth,
    categorias,
    clientes,
    enderecos,
    funcionarios,
    ingredientes,
    pedidos,
    produtos,
    status,
    usuarios,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize and seed database on startup."""
    init_db()
    seed_db()
    yield


app = FastAPI(
    title="Pizzaria API",
    description="API REST para gerenciamento de uma pizzaria com SQLAlchemy 2.0 ORM, JWT e RBAC.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuração do Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Handlers Globais RFC 9457 (Problem Details)
register_exception_handlers(app)

# Roteador versionado /api/v1
api_v1_router = APIRouter(prefix="/api/v1")

all_routers = [
    auth.router,
    usuarios.router,
    funcionarios.router,
    clientes.router,
    enderecos.router,
    categorias.router,
    ingredientes.router,
    status.router,
    produtos.router,
    pedidos.router,
]

for router in all_routers:
    api_v1_router.include_router(router)
    # Também inclui na raiz para compatibilidade total com SPEC.yaml (/usuarios, /pedidos, etc.)
    app.include_router(router)

app.include_router(api_v1_router)


@app.get("/health", tags=["Health"], summary="Verificar saúde da API")
def health_check():
    """Endpoint leve de healthcheck."""
    return {"status": "healthy", "version": "1.0.0"}
