# STYLEGUIDE.md — Constituição Técnica (Pizzaria API: ORM & Auth Edition)

## 1. Stack Tecnológica e Versões Obrigatórias
- **Linguagem:** Python 3.12+ com anotações estáticas de tipo (`typing`, `UUID`, `datetime`, `Enum`, `Annotated`).
- **Framework Web:** FastAPI (com suporte a escopo `/api/v1`).
- **Validação e Serialização:** Pydantic v2 (`BaseModel`, `ConfigDict(populate_by_name=True, from_attributes=True)`, `Field`, `@field_validator`).
- **Persistência e ORM:** SQLAlchemy 2.0+ utilizando sintaxe declarativa moderna (`DeclarativeBase`, `Mapped`, `mapped_column`, `relationship`, `ForeignKey`) com banco SQLite (`sqlite:///./pizzaria.db` em execução normal e banco isolado em memória/arquivo temporário nos testes).
- **Segurança, Autenticação e Autorização:** Autenticação Stateless via **JWT (`PyJWT`)** no padrão `Bearer Token` (`HTTPBearer`) e controle de acesso baseado em papéis (**RBAC**: `ADMIN`, `FUNCIONARIO`, `CLIENTE`).
- **Suíte de Testes:** `pytest` + `fastapi.testclient.TestClient` + `httpx`.

---

## 2. Arquitetura de Diretórios e Separação de Camadas
Todo o código da API deve respeitar rigorosamente a estrutura modular abaixo:

```text
src/api/
├── __init__.py
├── main.py          # Instância FastAPI, lifespan (init_db + seed), CORS, handlers de exceção e inclusão de routers
├── schemas.py       # Contratos Pydantic v2 espelhando exatamente os Data Schemas do Apidog (snake_case no contrato da pizzaria)
├── models.py        # Entidades ORM SQLAlchemy 2.0 (UsuarioModel, FuncionarioModel, ClienteModel, EnderecoModel, CategoriaModel, ProdutoModel, IngredienteModel, IngredienteProdutoModel, StatusModel, PedidoModel, ItemPedidoModel)
├── database.py      # Engine SQLAlchemy, SessionLocal, get_db (Dependency Injection) e seed inicial de dados
├── security.py      # Geração/validação de JWT, hash de senha (pwd_context) e dependências RBAC (get_current_user, require_role)
├── exceptions.py    # Exceções de domínio e handlers globais no padrão RFC 9457 / Problem Details (400, 401, 403, 404, 422)
├── requirements.txt # Dependências estritas do projeto (fastapi, uvicorn, pydantic, sqlalchemy, pyjwt, passlib, bcrypt, pytest, httpx)
├── routers/
│   ├── __init__.py
│   ├── auth.py          # Endpoints de autenticação (/api/v1/auth/login e /api/v1/auth/me)
│   ├── usuarios.py      # /api/v1/usuarios
│   ├── funcionarios.py  # /api/v1/funcionarios
│   ├── clientes.py      # /api/v1/clientes
│   ├── enderecos.py     # /api/v1/enderecos (com suporte ao filtro query ?id_cliente)
│   ├── categorias.py    # /api/v1/categorias
│   ├── produtos.py      # /api/v1/produtos (com filtros ?id_categoria, ?disponivel e sub-rotas de ingredientes)
│   ├── ingredientes.py  # /api/v1/ingredientes
│   ├── status.py        # /api/v1/status
│   └── pedidos.py       # /api/v1/pedidos (com suporte a filtros e sub-rotas de itens de pedido)
└── tests/
    ├── __init__.py
    ├── conftest.py          # Override de get_db para banco SQLite isolado e fixtures de tokens JWT/RBAC
    ├── test_auth.py         # Testes de autenticação, login e perfis RBAC (401 e 403)
    ├── test_usuarios.py     # Testes de CRUD da entidade Usuários
    ├── test_clientes.py     # Testes de CRUD e vínculo de Clientes
    ├── test_produtos.py     # Testes de produtos, categorias e vínculo de ingredientes (Eager Loading)
    ├── test_pedidos.py      # Testes de criação, alteração de status e itens de pedidos
    └── test_errors.py       # Testes de conformidade do formato de erro RFC 9457 (400, 401, 403, 404, 422)
```

---

## 3. Regras Inegociáveis de Implementação

### 3.1. Tratamento de Erros Semântico (RFC 9457 / Problem Details)
- É **PROIBIDO** retornar erros no formato padrão do FastAPI (`{"detail": "..."}`).
- Qualquer erro HTTP (`400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`) DEVE retornar um JSON compatível com o schema `ApiError`:
  - `type`: URI identificadora do erro:
    - `https://api.pizzariabarriga.dev/errors/bad-request` (`400`)
    - `https://api.pizzariabarriga.dev/errors/unauthorized` (`401`)
    - `https://api.pizzariabarriga.dev/errors/forbidden` (`403`)
    - `https://api.pizzariabarriga.dev/errors/not-found` (`404`)
    - `https://api.pizzariabarriga.dev/errors/validation-error` (`422`)
  - `title`: Resumo curto e legível do tipo de erro.
  - `status`: Código HTTP numérico.
  - `detail`: Explicação clara sobre a ocorrência específica.
  - `instance`: Caminho da URI requisitada (`request.url.path`).
  - `invalidParams`: Lista de objetos `{"name": "<campo>", "reason": "<motivo>"}` obrigatória em falhas de validação (`400`/`422`).

### 3.2. Regras de ORM e Prevenção do Problema N+1
- Use exclusivamente **SQLAlchemy 2.0** (`select()`, `Session.scalars()`, `Mapped[...]`, `mapped_column(...)`).
- Mapeie todos os relacionamentos de chave estrangeira (`ForeignKey`) e `relationship(...)` de forma explícita:
  - `ClienteModel` -> `EnderecoModel` (1:N)
  - `CategoriaModel` -> `ProdutoModel` (1:N)
  - `ProdutoModel` <-> `IngredienteModel` (N:M via `IngredienteProdutoModel`)
  - `PedidoModel` -> `ItemPedidoModel` (1:N)
- Ao consultar pedidos com itens, ou produtos com seus ingredientes vinculados, utilize **obrigatoriamente** estratégias adequadas de consulta (`selectinload` / `joinedload`) para **evitar o problema de queries N+1**.
- Toda operação de escrita (`POST`, `PUT`, `PATCH`, `DELETE`) deve gerenciar a transação explicitamente (`db.commit()`, `db.refresh()` ou `db.rollback()` em caso de exceção).

### 3.3. Regras de Autenticação JWT e Autorização RBAC
- Tokens JWT devem ser assinados com `HS256` contendo no payload: `sub` (ID do usuário), `email`, `role` (`ADMIN`, `FUNCIONARIO` ou `CLIENTE`), `iat` e `exp`.
- Ausência de cabeçalho `Authorization: Bearer <token>`, token malformado ou expirado deve retornar **`401 Unauthorized`** no formato **RFC 9457 (`ApiError`)**.
- Tentativa de acessar um recurso autenticado sem a permissão necessária (ex.: um usuário `CLIENTE` tentando executar `DELETE /api/v1/produtos/{id}`) deve retornar **`403 Forbidden`** no formato **RFC 9457 (`ApiError`)**.

### 3.4. Convenções de Nomenclatura e Fidelidade ao Contrato Apidog
- As chaves nos payloads JSON de entrada e saída DEVEM respeitar estritamente o contrato especificado no Apidog da Pizzaria (uso de `snake_case` nativo nas entidades da pizzaria, como `id_usuario`, `id_cliente`, `data_hora_pedido`, `unidade_medida`, `quantidade_estoque`, `valor_total`).
- Parâmetros de rota e consulta devem obedecer aos nomes especificados (`id_cliente`, `id_categoria`, `disponivel`, `id_status`, `id_funcionario`, `idIngrediente`, `idItem`).
- Configurações do Pydantic devem utilizar `from_attributes = True` para permitir compatibilidade transparente com os objetos do ORM SQLAlchemy.