# PLAN.md — Plano Arquitetural e Checklist de Implementação: Pizzaria API

> **Papel:** `[QA Engineer]`  
> **Metodologia:** Spec-Driven Development (SDD) & Clean Architecture  
> **Fontes da Verdade:** `STYLEGUIDE.md`, `SPEC.yaml`, `pizzaria-barriga.Apidog.json` e `AGENTS.md`  
> **Status Geral do Projeto:** 🟢 Todas as Fases (1 a 6) Concluídas e Aprovadas (100% dos Testes Aprovados - Green Bar)

---

## 📌 Visão Geral da Arquitetura e Governança

Este documento estabelece o roteiro técnico sequencial e granular para a implementação da **Pizzaria API**, construída sobre **FastAPI**, **SQLAlchemy 2.0 ORM** (sintaxe declarativa moderna com prevenção estrita a queries N+1), autenticação **Stateless JWT (`PyJWT`)** e autorização granular baseada em papéis (**RBAC**: `ADMIN`, `FUNCIONARIO`, `CLIENTE`).

Todas as respostas de erro seguirão rigorosamente o padrão **RFC 9457 / Problem Details** com o schema `ApiError`. É proibido retornar o payload padrão `{"detail": "..."}` do FastAPI.

```
Legenda de Status:
[ ] Não iniciado
[🔄] Em andamento
[x] Concluído e verificado
```

---

## 📋 Checklist Sequencial por Fases

### Fase 1: Estrutura de Diretórios e Dependências (`requirements.txt`)
*Objetivo: Estabelecer o layout modular do projeto e configurar o ambiente com dependências estritas sem acoplamento externo.*

- [x] **1.1 Criar a estrutura hierárquica de diretórios do projeto:**
  - [x] Criar diretório raiz de código: `src/api/`
  - [x] Criar subdiretório de roteamento modular: `src/api/routers/`
  - [x] Criar subdiretório da suíte de testes: `src/api/tests/`
- [x] **1.2 Inicializar pacotes Python:**
  - [x] Criar `src/api/__init__.py`
  - [x] Criar `src/api/routers/__init__.py`
  - [x] Criar `src/api/tests/__init__.py`
- [x] **1.3 Definir e validar o arquivo `src/api/requirements.txt`:**
  - [x] Incluir `fastapi>=0.110.0` (framework web assíncrono)
  - [x] Incluir `uvicorn[standard]>=0.28.0` (servidor ASGI)
  - [x] Incluir `pydantic>=2.6.0` (validação e serialização v2)
  - [x] Incluir `email-validator>=2.1.0` (suporte a tipos `EmailStr` do Pydantic)
  - [x] Incluir `sqlalchemy>=2.0.28` (ORM declarativo 2.0)
  - [x] Incluir `pyjwt>=2.8.0` (codificação e decodificação de tokens JWT HS256)
  - [x] Incluir `passlib[bcrypt]>=1.7.4` e `bcrypt>=4.1.2` (hashing seguro de senhas)
  - [x] Incluir `pytest>=8.1.0` e `pytest-asyncio` (runner de testes unitários e de integração)
  - [x] Incluir `httpx>=0.27.0` (cliente HTTP para `fastapi.testclient.TestClient`)
- [x] **1.4 Validação da Fase 1:**
  - [x] Verificar integridade da árvore de diretórios via terminal
  - [x] Validar instalação e resolução do ambiente virtual (`.venv`) com `pip check`

---

### Fase 2: Extração de Schemas Pydantic v2 (Apidog + DTOs de Auth + RFC 9457)
*Objetivo: Tipar e validar contratos estritos no arquivo `src/api/schemas.py`, espelhando `SPEC.yaml` e `pizzaria-barriga.Apidog.json`, com `from_attributes = True` e `snake_case` nativo.*

- [x] **2.1 Configuração Base e Schemas de Erro RFC 9457:**
  - [x] Criar schema `InvalidParam(BaseModel)` contendo `name: str` e `reason: str`
  - [x] Criar schema `ApiError(BaseModel)` contendo:
    - `type: str` (URI identificadora do erro)
    - `title: str` (resumo curto do erro)
    - `status: int` (código HTTP 400, 401, 403, 404, 422)
    - `detail: str` (descrição clara da falha)
    - `instance: str` (caminho da URI requisitada)
    - `invalidParams: Optional[List[InvalidParam]] = None` (obrigatório em 400/422 de validação)
- [x] **2.2 DTOs de Autenticação e Segurança (Auth):**
  - [x] Criar `LoginInput(BaseModel)`: `email: EmailStr`, `senha: str`
  - [x] Criar `TokenResponse(BaseModel)`: `access_token: str`, `token_type: str = "bearer"`
  - [x] Criar `UsuarioAuthResponse(BaseModel)`: `id_usuario: int`, `email: EmailStr`, `nome_perfil: str`, `ativo: bool`, `role: str`
  - [x] Criar `TokenData(BaseModel)`: payload decodificado do JWT (`sub: str`, `email: str`, `role: str`, `exp: Optional[int]`)
- [x] **2.3 Contratos de Domínio — Usuários e Atores:**
  - [x] `UsuarioInput(BaseModel)`: `email` (max 160), `senha` (max 255), `ativo: bool = True`, `nome_perfil` (max 80, enum: ADMIN, FUNCIONARIO, CLIENTE), `descricao` (opcional, max 500)
  - [x] `Usuario(BaseModel)`: herda de `UsuarioInput` + `id_usuario: int`
  - [x] `FuncionarioInput(BaseModel)`: `id_usuario: int`, `nome` (max 120), `cpf` (max 14), `cargo` (max 80), `telefone` (opcional, max 20)
  - [x] `Funcionario(BaseModel)`: herda de `FuncionarioInput` + `id_funcionario: int`
  - [x] `ClienteInput(BaseModel)`: `id_usuario: int`, `nome` (max 120), `cpf` (max 14), `telefone` (opcional, max 20)
  - [x] `Cliente(BaseModel)`: herda de `ClienteInput` + `id_cliente: int`
- [x] **2.4 Contratos de Domínio — Endereços e Categorias:**
  - [x] `EnderecoInput(BaseModel)`: `id_cliente: int`, `cep` (max 9), `logradouro` (max 160), `numero` (max 20), `complemento` (opcional, max 100), `bairro` (max 100), `cidade` (max 100), `uf` (min 2, max 2)
  - [x] `Endereco(BaseModel)`: herda de `EnderecoInput` + `id_endereco: int`
  - [x] `CategoriaInput(BaseModel)`: `nome` (max 100), `descricao` (opcional, max 500)
  - [x] `Categoria(BaseModel)`: herda de `CategoriaInput` + `id_categoria: int`
- [x] **2.5 Contratos de Domínio — Ingredientes e Produtos:**
  - [x] `IngredienteInput(BaseModel)`: `nome` (max 120), `quantidade_estoque: float >= 0 = 0.0`, `unidade_medida` (max 20)
  - [x] `Ingrediente(BaseModel)`: herda de `IngredienteInput` + `id_ingrediente: int`
  - [x] `ProdutoInput(BaseModel)`: `id_categoria: int`, `nome` (max 120), `tamanho` (max 30), `preco: float >= 0`, `disponivel: bool = True`
  - [x] `Produto(BaseModel)`: herda de `ProdutoInput` + `id_produto: int`
  - [x] `IngredienteProdutoVinculo(BaseModel)`: `id_ingrediente: int`, `quantidade_necessaria: float >= 0`
  - [x] `IngredienteProduto(BaseModel)`: `id_ingrediente_produto: int`, `id_produto: int`, `id_ingrediente: int`, `quantidade_necessaria: float`
- [x] **2.6 Contratos de Domínio — Status, Pedidos e Itens:**
  - [x] `StatusInput(BaseModel)`: `nome_status` (max 50)
  - [x] `Status(BaseModel)`: herda de `StatusInput` + `id_status: int`
  - [x] `ItemPedidoInput(BaseModel)`: `id_produto: int`, `quantidade: int >= 1`, `preco_unitario: float >= 0`, `subtotal: float >= 0`, `observacao` (opcional, max 500)
  - [x] `ItemPedido(BaseModel)`: herda de `ItemPedidoInput` + `id_item_pedido: int`, `id_pedido: int`
  - [x] `PedidoInput(BaseModel)`: `id_cliente: int`, `id_funcionario: int`, `id_status: int`, `id_endereco: int`, `forma_pagamento` (max 40), `taxa_entrega: float >= 0 = 0.0`, `valor_total: float >= 0`
  - [x] `Pedido(BaseModel)`: herda de `PedidoInput` + `id_pedido: int`, `data_hora_pedido: datetime`
  - [x] `PedidoDetalhado(Pedido)`: modelo estendido contendo `itens: List[ItemPedido] = []`
- [x] **2.7 Validação da Fase 2:**
  - [x] Verificar importação limpa de todos os schemas em Python sem erros de sintaxe
  - [x] Assegurar `ConfigDict(populate_by_name=True, from_attributes=True)` em todos os modelos para interoperabilidade com o ORM

---

### Fase 3: Modelos ORM SQLAlchemy 2.0 e `database.py` com Seed
*Objetivo: Modelar tabelas com sintaxe declarativa moderna SQLAlchemy 2.0 (`Mapped`, `mapped_column`, `relationship`, `ForeignKey`) no arquivo `src/api/models.py`, e estruturar engine, sessions, injeção de dependência e seed em `src/api/database.py`.*

- [x] **3.1 Configuração da Camada de Banco (`src/api/database.py`):**
  - [x] Definir classe base `class Base(DeclarativeBase): pass`
  - [x] Configurar `engine = create_engine("sqlite:///./pizzaria.db", connect_args={"check_same_thread": False})`
  - [x] Configurar fábrica de sessões `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`
  - [x] Implementar dependência geradora `get_db() -> Generator[Session, None, None]` com fechamento seguro no bloco `finally`
  - [x] Implementar rotina `init_db()` executando `Base.metadata.create_all(bind=engine)`
  - [x] Implementar rotina `seed_db(db: Session)` para inserção inicial idempotente:
    - Perfis/Usuários padrão (`admin@pizzaria.com` [ADMIN], `func@pizzaria.com` [FUNCIONARIO], `cliente@pizzaria.com` [CLIENTE]) com senhas criptografadas via bcrypt
    - Registros correspondentes em `FuncionarioModel` e `ClienteModel`
    - Status canônicos de pedidos (`Recebido`, `Em Preparo`, `Pronto`, `Em Rota`, `Entregue`, `Cancelado`)
    - Categorias iniciais (`Pizzas Salgadas`, `Pizzas Doces`, `Bebidas`)
    - Ingredientes básicos para estoque inicial
- [x] **3.2 Mapeamento das Entidades ORM (`src/api/models.py`):**
  - [x] `UsuarioModel` (`usuarios`):
    - Colunas: `id_usuario` (PK, int, autoincrement), `email` (str, unique, index), `senha` (str), `ativo` (bool, default=True), `nome_perfil` (str), `descricao` (str, nullable)
    - Relacionamentos: `funcionario` (1:1/1:N), `cliente` (1:1/1:N)
  - [x] `FuncionarioModel` (`funcionarios`):
    - Colunas: `id_funcionario` (PK, int), `id_usuario` (FK -> `usuarios.id_usuario`), `nome` (str), `cpf` (str, unique), `cargo` (str), `telefone` (str, nullable)
    - Relacionamento: `usuario = relationship("UsuarioModel", back_populates="funcionario")`
  - [x] `ClienteModel` (`clientes`):
    - Colunas: `id_cliente` (PK, int), `id_usuario` (FK -> `usuarios.id_usuario`), `nome` (str), `cpf` (str, unique), `telefone` (str, nullable)
    - Relacionamentos: `usuario = relationship("UsuarioModel")`, `enderecos = relationship("EnderecoModel", back_populates="cliente", cascade="all, delete-orphan")` (1:N)
  - [x] `EnderecoModel` (`enderecos`):
    - Colunas: `id_endereco` (PK, int), `id_cliente` (FK -> `clientes.id_cliente`), `cep` (str), `logradouro` (str), `numero` (str), `complemento` (str, nullable), `bairro` (str), `cidade` (str), `uf` (str)
    - Relacionamento: `cliente = relationship("ClienteModel", back_populates="enderecos")`
  - [x] `CategoriaModel` (`categorias`):
    - Colunas: `id_categoria` (PK, int), `nome` (str, unique), `descricao` (str, nullable)
    - Relacionamento: `produtos = relationship("ProdutoModel", back_populates="categoria")` (1:N)
  - [x] `ProdutoModel` (`produtos`):
    - Colunas: `id_produto` (PK, int), `id_categoria` (FK -> `categorias.id_categoria`), `nome` (str), `tamanho` (str), `preco` (float), `disponivel` (bool, default=True)
    - Relacionamentos: `categoria = relationship("CategoriaModel", back_populates="produtos")`, `ingredientes_produto = relationship("IngredienteProdutoModel", back_populates="produto", cascade="all, delete-orphan")`
  - [x] `IngredienteModel` (`ingredientes`):
    - Colunas: `id_ingrediente` (PK, int), `nome` (str, unique), `quantidade_estoque` (float), `unidade_medida` (str)
    - Relacionamento: `produtos_associados = relationship("IngredienteProdutoModel", back_populates="ingrediente")`
  - [x] `IngredienteProdutoModel` (`ingrediente_produtos` — Associação N:M):
    - Colunas: `id_ingrediente_produto` (PK, int), `id_produto` (FK -> `produtos.id_produto`), `id_ingrediente` (FK -> `ingredientes.id_ingrediente`), `quantidade_necessaria` (float)
    - Relacionamentos: `produto = relationship("ProdutoModel", back_populates="ingredientes_produto")`, `ingrediente = relationship("IngredienteModel", back_populates="produtos_associados")`
  - [x] `StatusModel` (`status`):
    - Colunas: `id_status` (PK, int), `nome_status` (str, unique)
    - Relacionamento: `pedidos = relationship("PedidoModel", back_populates="status")`
  - [x] `PedidoModel` (`pedidos`):
    - Colunas: `id_pedido` (PK, int), `id_cliente` (FK -> `clientes.id_cliente`), `id_funcionario` (FK -> `funcionarios.id_funcionario`), `id_status` (FK -> `status.id_status`), `id_endereco` (FK -> `enderecos.id_endereco`), `data_hora_pedido` (datetime), `forma_pagamento` (str), `taxa_entrega` (float), `valor_total` (float)
    - Relacionamentos: `itens = relationship("ItemPedidoModel", back_populates="pedido", cascade="all, delete-orphan")` (1:N), `cliente = relationship("ClienteModel")`, `funcionario = relationship("FuncionarioModel")`, `status = relationship("StatusModel", back_populates="pedidos")`, `endereco = relationship("EnderecoModel")`
  - [x] `ItemPedidoModel` (`item_pedidos`):
    - Colunas: `id_item_pedido` (PK, int), `id_pedido` (FK -> `pedidos.id_pedido`), `id_produto` (FK -> `produtos.id_produto`), `quantidade` (int), `preco_unitario` (float), `subtotal` (float), `observacao` (str, nullable)
    - Relacionamentos: `pedido = relationship("PedidoModel", back_populates="itens")`, `produto = relationship("ProdutoModel")`
- [x] **3.3 Validação da Fase 3:**
  - [x] Executar script temporário de validação para instanciar as tabelas SQLite em memória
  - [x] Verificar integridade das chaves estrangeiras e índices

---

### Fase 4: Exceções RFC 9457 (400, 401, 403, 404, 422) e `security.py` (JWT + RBAC)
*Objetivo: Estabelecer o padrão rigoroso de respostas de erro Problem Details e o mecanismo de autenticação/autorização stateless.*

- [x] **4.1 Implementação de `src/api/exceptions.py`:**
  - [x] Criar classe base `AppException(Exception)` com atributos `status_code`, `title`, `detail`, `type_uri`, `invalid_params`
  - [x] Criar exceções especializadas:
    - `BadRequestError(AppException)`: status 400, `type="https://api.pizzariabarriga.dev/errors/bad-request"`, title="Bad Request"
    - `UnauthorizedError(AppException)`: status 401, `type="https://api.pizzariabarriga.dev/errors/unauthorized"`, title="Unauthorized"
    - `ForbiddenError(AppException)`: status 403, `type="https://api.pizzariabarriga.dev/errors/forbidden"`, title="Forbidden"
    - `NotFoundError(AppException)`: status 404, `type="https://api.pizzariabarriga.dev/errors/not-found"`, title="Not Found"
    - `UnprocessableEntityError(AppException)`: status 422, `type="https://api.pizzariabarriga.dev/errors/validation-error"`, title="Validation Error"
  - [x] Criar gerador helper `build_problem_details_response(...)` retornando `JSONResponse` com `media_type="application/problem+json"`
  - [x] Implementar Exception Handlers customizados para o FastAPI:
    - Handler para `AppException`
    - Handler para `RequestValidationError` (Pydantic): mapear erros de validação para a lista `invalidParams` com `{"name": field, "reason": msg}` (status 422)
    - Handler para `StarletteHTTPException` (FastAPI 404/405/etc.) convertendo para o formato RFC 9457
    - Handler para erros de decodificação de JSON no body (`json.decoder.JSONDecodeError` / body malformado) retornando 400 RFC 9457
- [x] **4.2 Implementação de `src/api/security.py`:**
  - [x] Configurar hashing de senhas com `CryptContext(schemes=["bcrypt"], deprecated="auto")`:
    - Função `verify_password(plain_password: str, hashed_password: str) -> bool`
    - Função `get_password_hash(password: str) -> str`
  - [x] Constantes JWT: `SECRET_KEY`, `ALGORITHM = "HS256"`, `ACCESS_TOKEN_EXPIRE_MINUTES = 60`
  - [x] Função `create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str` injetando claims `sub`, `email`, `role`, `iat`, `exp`
  - [x] Função `decode_access_token(token: str) -> dict` capturando `ExpiredSignatureError` e `PyJWTError` e levantando `UnauthorizedError`
  - [x] Dependência `HTTPBearer(auto_error=False)` customizada para assegurar que ausência de token resulte em RFC 9457 401
  - [x] Dependência `get_current_user(credentials, db) -> UsuarioModel`:
    - Validar presença de token e extrair `sub`
    - Buscar usuário no banco de dados e checar se `ativo == True`
    - Levantar `UnauthorizedError` se inválido ou inativo
  - [x] Dependência de autorização baseada em papéis (RBAC) `require_role(allowed_roles: List[str])`:
    - Interceptar usuário corrente e verificar se seu `nome_perfil` (ex: ADMIN, FUNCIONARIO, CLIENTE) está em `allowed_roles`
    - Levantar `ForbiddenError` (403 RFC 9457) se o perfil não tiver permissão
- [x] **4.3 Validação da Fase 4:**
  - [x] Testar codificação e validação de tokens JWT isoladamente
  - [x] Garantir que qualquer exceção resulte no dicionário com chaves `type`, `title`, `status`, `detail`, `instance`

---

### Fase 5: Routers e `main.py`
*Objetivo: Construir os endpoints da API sob o escopo `/api/v1`, aplicando verificação RBAC, persistência transacional explícita e Eager Loading com `selectinload` / `joinedload`.*

- [x] **5.1 Router de Autenticação (`src/api/routers/auth.py`):**
  - [x] `POST /api/v1/auth/login`: autenticação por email e senha, retornando `TokenResponse`
  - [x] `GET /api/v1/auth/me`: retorna os dados do usuário autenticado (`UsuarioAuthResponse`), protegido por `get_current_user`
- [x] **5.2 Router de Usuários (`src/api/routers/usuarios.py`):**
  - [x] `GET /api/v1/usuarios`: listar usuários (RBAC: `ADMIN`)
  - [x] `POST /api/v1/usuarios`: criar novo usuário com senha hasheada (público ou restrito a ADMIN)
  - [x] `GET /api/v1/usuarios/{id}`: buscar usuário por ID (404 se inexistente)
  - [x] `PUT /api/v1/usuarios/{id}`: atualizar dados do usuário
  - [x] `DELETE /api/v1/usuarios/{id}`: excluir usuário (204 No Content)
- [x] **5.3 Router de Funcionários (`src/api/routers/funcionarios.py`):**
  - [x] `GET /api/v1/funcionarios`: listar funcionários (RBAC: `ADMIN`)
  - [x] `POST /api/v1/funcionarios`: cadastrar funcionário vinculado a `id_usuario` existente
  - [x] `GET /api/v1/funcionarios/{id}`: buscar funcionário por ID
  - [x] `PUT /api/v1/funcionarios/{id}`: atualizar dados do funcionário
  - [x] `DELETE /api/v1/funcionarios/{id}`: excluir funcionário (204 No Content)
- [x] **5.4 Router de Clientes (`src/api/routers/clientes.py`):**
  - [x] `GET /api/v1/clientes`: listar clientes (RBAC: `ADMIN`, `FUNCIONARIO`)
  - [x] `POST /api/v1/clientes`: cadastrar cliente vinculado a `id_usuario`
  - [x] `GET /api/v1/clientes/{id}`: buscar cliente por ID
  - [x] `PUT /api/v1/clientes/{id}`: atualizar dados do cliente
  - [x] `DELETE /api/v1/clientes/{id}`: excluir cliente (204 No Content)
- [x] **5.5 Router de Endereços (`src/api/routers/enderecos.py`):**
  - [x] `GET /api/v1/enderecos`: listar endereços com suporte a filtro query `?id_cliente`
  - [x] `POST /api/v1/enderecos`: cadastrar endereço vinculado ao cliente
  - [x] `GET /api/v1/enderecos/{id}`: buscar endereço por ID
  - [x] `PUT /api/v1/enderecos/{id}`: atualizar endereço
  - [x] `DELETE /api/v1/enderecos/{id}`: remover endereço (204 No Content)
- [x] **5.6 Router de Categorias (`src/api/routers/categorias.py`):**
  - [x] `GET /api/v1/categorias`: listar todas as categorias (público/autenticado)
  - [x] `POST /api/v1/categorias`: cadastrar categoria (RBAC: `ADMIN`)
  - [x] `GET /api/v1/categorias/{id}`: buscar categoria por ID
  - [x] `PUT /api/v1/categorias/{id}`: atualizar categoria (RBAC: `ADMIN`)
  - [x] `DELETE /api/v1/categorias/{id}`: excluir categoria (RBAC: `ADMIN`, 204 No Content)
- [x] **5.7 Router de Ingredientes (`src/api/routers/ingredientes.py`):**
  - [x] `GET /api/v1/ingredientes`: listar ingredientes de estoque
  - [x] `POST /api/v1/ingredientes`: cadastrar ingrediente (RBAC: `ADMIN`, `FUNCIONARIO`)
  - [x] `GET /api/v1/ingredientes/{id}`: buscar ingrediente por ID
  - [x] `PUT /api/v1/ingredientes/{id}`: atualizar ingrediente (RBAC: `ADMIN`, `FUNCIONARIO`)
  - [x] `DELETE /api/v1/ingredientes/{id}`: excluir ingrediente (RBAC: `ADMIN`, 204 No Content)
- [x] **5.8 Router de Status (`src/api/routers/status.py`):**
  - [x] `GET /api/v1/status`: listar status disponíveis
  - [x] `POST /api/v1/status`: cadastrar novo status (RBAC: `ADMIN`)
  - [x] `GET /api/v1/status/{id}`: buscar status por ID
  - [x] `PUT /api/v1/status/{id}`: atualizar status (RBAC: `ADMIN`)
  - [x] `DELETE /api/v1/status/{id}`: excluir status (RBAC: `ADMIN`, 204 No Content)
- [x] **5.9 Router de Produtos (`src/api/routers/produtos.py`):**
  - [x] `GET /api/v1/produtos`: listagem com filtros query `?id_categoria` e `?disponivel`, aplicando **`selectinload(ProdutoModel.ingredientes_produto)`** para eliminar o problema N+1
  - [x] `POST /api/v1/produtos`: cadastrar produto (RBAC: `ADMIN`, `FUNCIONARIO`)
  - [x] `GET /api/v1/produtos/{id}`: buscar produto por ID com carregamento adiantado
  - [x] `PUT /api/v1/produtos/{id}`: atualizar dados do produto (RBAC: `ADMIN`, `FUNCIONARIO`)
  - [x] `DELETE /api/v1/produtos/{id}`: excluir produto (RBAC: `ADMIN`, 204 No Content)
  - [x] `GET /api/v1/produtos/{id}/ingredientes`: listar ingredientes vinculados ao produto
  - [x] `POST /api/v1/produtos/{id}/ingredientes`: vincular ingrediente ao produto (`id_ingrediente`, `quantidade_necessaria`)
  - [x] `DELETE /api/v1/produtos/{id}/ingredientes/{idIngrediente}`: desvincular ingrediente do produto (204 No Content)
- [x] **5.10 Router de Pedidos (`src/api/routers/pedidos.py`):**
  - [x] `GET /api/v1/pedidos`: listagem com suporte a filtros query (`id_cliente`, `id_status`), aplicando **`selectinload(PedidoModel.itens)`**
  - [x] `POST /api/v1/pedidos`: registrar novo pedido com validações de cliente, endereço e status inicial
  - [x] `GET /api/v1/pedidos/{id}`: buscar pedido por ID com Eager Loading dos itens (`selectinload(PedidoModel.itens)`)
  - [x] `PUT /api/v1/pedidos/{id}`: atualizar dados ou status do pedido
  - [x] `DELETE /api/v1/pedidos/{id}`: cancelar/remover pedido (204 No Content)
  - [x] `GET /api/v1/pedidos/{id}/itens`: listar itens pertencentes ao pedido
  - [x] `POST /api/v1/pedidos/{id}/itens`: adicionar item ao pedido (recalculando subtotal e atualizando `valor_total` da transação)
  - [x] `PUT /api/v1/pedidos/{id}/itens/{idItem}`: atualizar quantidade/observação de um item
  - [x] `DELETE /api/v1/pedidos/{id}/itens/{idItem}`: remover item do pedido (204 No Content)
- [x] **5.11 Ponto de Entrada Principal (`src/api/main.py`):**
  - [x] Instanciar aplicação `app = FastAPI(title="Pizzaria API", version="1.0.0")` com context manager assíncrono `lifespan` para executar `init_db()` e `seed_db()`
  - [x] Registrar `CORSMiddleware` (origens, headers e métodos liberados)
  - [x] Registrar todos os exception handlers da RFC 9457 desenvolvidos na Fase 4
  - [x] Incluir todos os routers sob o prefixo `/api/v1` com tags semânticas correspondentes
- [x] **5.12 Validação da Fase 5:**
  - [x] Subir o servidor ASGI (`uvicorn src.api.main:app`) em modo dry-run e validar o schema Swagger em `/docs` e `/openapi.json`

---

### Fase 6: Suíte Completa de Testes Pytest
*Objetivo: Garantir 100% de conformidade com os contratos do Apidog, cobertura de fluxos de autenticação, validações e conformidade estrita da RFC 9457.*

- [x] **6.1 Configuração de Fixtures e Banco Isolado (`src/api/tests/conftest.py`):**
  - [x] Configurar SQLite isolado em memória (`sqlite:///:memory:` com `StaticPool`)
  - [x] Criar fixture de sessão de banco recriando schema a cada teste (`create_all` / `drop_all`)
  - [x] Aplicar `app.dependency_overrides[get_db]` apontando para a sessão de teste isolada
  - [x] Configurar fixture `client` utilizando `fastapi.testclient.TestClient`
  - [x] Criar fixtures com headers de autenticação JWT pré-configurados:
    - `admin_headers`: Bearer token com role `ADMIN`
    - `funcionario_headers`: Bearer token com role `FUNCIONARIO`
    - `cliente_headers`: Bearer token com role `CLIENTE`
    - `expired_headers`: Bearer token com `exp` expirado
- [x] **6.2 Testes de Autenticação e RBAC (`src/api/tests/test_auth.py`):**
  - [x] Testar login bem-sucedido retornando `access_token` e `token_type: bearer`
  - [x] Testar login com senha inválida (esperado: 401 RFC 9457)
  - [x] Testar login com usuário inexistente (esperado: 401 RFC 9457)
  - [x] Testar endpoint `/api/v1/auth/me` autenticado com usuário corrente
  - [x] Testar acesso a rotas privadas sem header de autorização (esperado: 401 RFC 9457)
  - [x] Testar acesso com token corrompido ou expirado (esperado: 401 RFC 9457)
  - [x] Testar restrição RBAC: `CLIENTE` tentando excluir produto ou criar categoria (esperado: 403 RFC 9457)
  - [x] Testar permissão RBAC: `ADMIN` e `FUNCIONARIO` operando recursos autorizados
- [x] **6.3 Testes de Usuários e Funcionários (`src/api/tests/test_usuarios.py`):**
  - [x] Testar criação de usuário verificando se a senha foi hasheada no banco
  - [x] Testar prevenção de duplicidade de e-mail (400 ou 422 RFC 9457)
  - [x] Testar listagem e exclusão de usuário por `ADMIN`
  - [x] Testar criação e vínculo de funcionário ao `id_usuario`
- [x] **6.4 Testes de Clientes e Endereços (`src/api/tests/test_clientes.py`):**
  - [x] Testar CRUD de Clientes
  - [x] Testar CRUD de Endereços vinculado ao cliente
  - [x] Testar filtro de busca de endereços `GET /api/v1/enderecos?id_cliente={id}`
  - [x] Testar integridade referencial ao excluir cliente em cascata com endereços
- [x] **6.5 Testes de Produtos, Categorias e Ingredientes (`src/api/tests/test_produtos.py`):**
  - [x] Testar CRUD de categorias
  - [x] Testar CRUD de produtos com validação de campos obrigatórios
  - [x] Testar filtros de busca `?id_categoria` e `?disponivel`
  - [x] Testar vínculo N:M via sub-rotas `/produtos/{id}/ingredientes` (adição, listagem e remoção)
  - [x] Testar consulta de produtos garantindo ausência de erros de lazy loading / N+1
- [x] **6.6 Testes de Pedidos e Itens (`src/api/tests/test_pedidos.py`):**
  - [x] Testar criação de pedido e cálculo de valores
  - [x] Testar adição de itens ao pedido (`/pedidos/{id}/itens`) com validação de subtotal
  - [x] Testar atualização e remoção de item do pedido
  - [x] Testar alteração de status do pedido
  - [x] Testar carregamento adiantado com `selectinload(PedidoModel.itens)` na busca por ID
- [x] **6.7 Testes de Conformidade RFC 9457 / Problem Details (`src/api/tests/test_errors.py`):**
  - [x] Validar estrutura JSON do erro 400 (Bad Request / JSON malformado no body)
  - [x] Validar estrutura JSON do erro 401 (Unauthorized / token ausente ou expirado)
  - [x] Validar estrutura JSON do erro 403 (Forbidden / violação de RBAC)
  - [x] Validar estrutura JSON do erro 404 (Not Found / recurso inexistente)
  - [x] Validar estrutura JSON do erro 422 (Unprocessable Entity com array `invalidParams` populado)
  - [x] Garantir que em nenhum cenário o FastAPI retorne o payload legado `{"detail": ...}`
- [x] **6.8 Validação da Fase 6:**
  - [x] Executar suíte completa: `pytest -v --tb=short`
  - [x] Comprovar 100% dos testes aprovados (Green Bar)

---

## 🔒 Conclusão e Resumo do Projeto
1. **Status:** 100% dos itens planejados foram executados e validados.
2. **Qualidade:** 34 testes automatizados executados via pytest com isolamento em memória e 100% de aprovação (Green Bar).
3. **Conformidade:** Total aderência a `STYLEGUIDE.md`, `SPEC.yaml`, `pizzaria-barriga.Apidog.json`, SQLAlchemy 2.0 ORM, JWT stateless, RBAC e RFC 9457 (Problem Details).
