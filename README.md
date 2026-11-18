# 🍕 Pizzaria API — Guia Completo de Execução e Testes Manuais (Postman)

> **Documento Arquitetural e Operacional**  
> **Autores:**
> Guilherme Gomes |
> Gabriel Flores |
> Marcelo Oliveira |
> Maria Eduarda Gonçalves  
> **Metodologia:** Spec-Driven Development (SDD) & Clean Architecture  
> **Stack:** FastAPI | SQLAlchemy 2.0 ORM | Pydantic v2 | JWT (PyJWT HS256) | SQLite  
> **Conformidade:** Padrão RFC 9457 / Problem Details

---

## 📖 1. Visão Geral da API

A **Pizzaria API** é uma solução RESTful moderna desenvolvida para o gerenciamento integral de uma pizzaria, abrangendo o controle de usuários, clientes, funcionários, endereços de entrega, categorias, estoque de ingredientes, produtos comercializados, pedidos e itens de pedidos.

### 🏛️ Destaques da Arquitetura
1. **SQLAlchemy 2.0 Declarativo:** Todas as 11 entidades mapeadas com `Mapped[...]` e `mapped_column(...)`, relacionamentos bidirecionais explícitos e estratégias de **Eager Loading (`selectinload`)** para eliminar consultas N+1 em pedidos e produtos.
2. **Autenticação Stateless JWT:** Emissão e validação de tokens Bearer via `PyJWT` (algoritmo `HS256`) contendo claims semânticas (`sub`, `email`, `role`, `iat`, `exp`).
3. **Controle de Acesso Baseado em Papéis (RBAC):** Proteção de rotas conforme o perfil do usuário (`ADMIN`, `FUNCIONARIO`, `CLIENTE`).
4. **Tratamento de Erros Semântico (RFC 9457 / Problem Details):** Todas as falhas HTTP (400, 401, 403, 404 e 422) retornam o schema padronizado `ApiError` com `media_type="application/problem+json"`, proibindo vazamento do formato legado `{"detail": ...}` do FastAPI.

---

## 🛠️ 2. Como Rodar a API Localmente

### Pré-requisitos
- Python 3.12 ou superior (testado e homologado no Python 3.14)
- Pip e venv

### Passo 1: Clonar/Acessar o Diretório do Projeto
```bash
cd /Users/gui/Fatec/WEB
```

### Passo 2: Criar e Ativar o Ambiente Virtual
```bash
# Caso o ambiente virtual ainda não exista:
python3 -m venv .venv

# Ativar no macOS / Linux:
source .venv/bin/activate

# Ou no Windows:
# .venv\Scripts\activate
```

### Passo 3: Instalar as Dependências
```bash
pip install -r src/api/requirements.txt
```

### Passo 4: Iniciar o Servidor ASGI (Uvicorn)
Execute o servidor na porta `5000` (ou na porta de sua preferência):
```bash
uvicorn src.api.main:app --reload --port 5000
```

> **Nota sobre o Seed Automático:**  
> Ao iniciar o servidor, o context manager `lifespan` do FastAPI executa automaticamente a criação das tabelas e o seed idempotente com dados essenciais (usuários, status, categorias, ingredientes e produto inicial).

### Passo 5: Testar Conectividade
Abra seu navegador ou cliente HTTP e acesse:
- **Healthcheck:** [http://localhost:5000/health](http://localhost:5000/health)
- **Documentação Interativa Swagger UI:** [http://localhost:5000/docs](http://localhost:5000/docs)
- **Documentação ReDoc:** [http://localhost:5000/redoc](http://localhost:5000/redoc)

---

## 🧪 3. Execução dos Testes Automatizados

Para rodar a suíte completa de 34 testes automatizados em banco isolado em memória:
```bash
pytest -v
```

---

## 👥 4. Credenciais Pré-configuradas (Seed Inicial)

O banco inicial já possui 3 usuários para testes imediatos de login e RBAC:

| Papel (Role) | E-mail | Senha | Vínculo Cadastral | Permissões |
| :--- | :--- | :--- | :--- | :--- |
| **ADMIN** | `admin@pizzaria.com` | `admin123` | Administrador Geral | Acesso total a todos os recursos e exclusões |
| **FUNCIONARIO** | `func@pizzaria.com` | `func123` | Carlos Pizzaiolo (ID 1) | Gestão de produtos, estoque e pedidos |
| **CLIENTE** | `cliente@pizzaria.com` | `cliente123` | Maria Oliveira (ID 1) | Consulta e pedidos (proibido de deletar produtos/categorias) |

---

## 📮 5. Roteiro Passo a Passo de Testes Manuais com Postman / Insomnia

Recomendamos configurar uma variável de ambiente no Postman:
- `baseUrl`: `http://localhost:5000/api/v1`
- `token`: (será preenchido após o login)

---

### Caso de Teste 1: Autenticação e Obtenção de Token JWT
*Objetivo: Efetuar login e obter o access_token para autenticar requisições privadas.*

- **Método:** `POST`
- **URL:** `{{baseUrl}}/auth/login`
- **Headers:** `Content-Type: application/json`
- **Body (raw JSON):**
```json
{
  "email": "admin@pizzaria.com",
  "senha": "admin123"
}
```
- **Resposta Esperada (HTTP 200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
> 💡 **Dica no Postman:** Copie o valor de `access_token` e defina na aba **Authorization** como **Type: Bearer Token**.

---

### Caso de Teste 2: Identificação do Usuário Logado (/auth/me)
*Objetivo: Validar decodificação do token e dados do usuário corrente.*

- **Método:** `GET`
- **URL:** `{{baseUrl}}/auth/me`
- **Headers:**
  - `Authorization`: `Bearer {{token}}`
- **Resposta Esperada (HTTP 200 OK):**
```json
{
  "id_usuario": 1,
  "email": "admin@pizzaria.com",
  "nome_perfil": "ADMIN",
  "ativo": true,
  "descricao": "Administrador do Sistema",
  "role": "ADMIN"
}
```

---

### Caso de Teste 3: Verificação de Erro 401 Unauthorized (Token Ausente ou Inválido)
*Objetivo: Garantir conformidade com RFC 9457 ao tentar acessar recurso protegido sem autenticação.*

- **Método:** `GET`
- **URL:** `{{baseUrl}}/auth/me`
- **Headers:** *(Sem header Authorization)*
- **Resposta Esperada (HTTP 401 Unauthorized):**
```json
{
  "type": "https://api.pizzariabarriga.dev/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Cabeçalho de autorização ausente ou token não fornecido.",
  "instance": "/api/v1/auth/me"
}
```

---

### Caso de Teste 4: Verificação de Erro 403 Forbidden (RBAC)
*Objetivo: Demonstrar que um CLIENTE é impedido de realizar operações administrativas.*

1. Faça login como cliente (`cliente@pizzaria.com` / `cliente123`) e copie seu token.
2. Tente excluir um produto:
- **Método:** `DELETE`
- **URL:** `{{baseUrl}}/produtos/1`
- **Headers:**
  - `Authorization`: `Bearer {{token_cliente}}`
- **Resposta Esperada (HTTP 403 Forbidden):**
```json
{
  "type": "https://api.pizzariabarriga.dev/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Acesso negado: Perfil 'CLIENTE' não possui permissão para esta operação. Papéis permitidos: [ADMIN, FUNCIONARIO].",
  "instance": "/api/v1/produtos/1"
}
```

---

### Caso de Teste 5: Consulta ao Catálogo com Filtros e Eager Loading
*Objetivo: Listar produtos ativos aplicando filtros de busca.*

- **Método:** `GET`
- **URL:** `{{baseUrl}}/produtos?id_categoria=1&disponivel=true`
- **Resposta Esperada (HTTP 200 OK):**
```json
[
  {
    "id_produto": 1,
    "id_categoria": 1,
    "nome": "Pizza Calabresa",
    "tamanho": "Grande",
    "preco": 45.0,
    "disponivel": true
  }
]
```

---

### Caso de Teste 6: Sub-rotas N:M — Ingredientes do Produto
*Objetivo: Consultar e associar novos insumos à pizza.*

1. **Listar ingredientes vinculados à Pizza Calabresa (ID 1):**
   - **Método:** `GET`
   - **URL:** `{{baseUrl}}/produtos/1/ingredientes`
   - **Resposta Esperada (HTTP 200 OK):**
   ```json
   [
     {
       "id_ingrediente_produto": 1,
       "id_produto": 1,
       "id_ingrediente": 1,
       "quantidade_necessaria": 0.35
     },
     {
       "id_ingrediente_produto": 2,
       "id_produto": 1,
       "id_ingrediente": 4,
       "quantidade_necessaria": 0.20
     }
   ]
   ```

2. **Vincular novo ingrediente (Cebola Fatiada - ID 5):**
   - **Método:** `POST`
   - **URL:** `{{baseUrl}}/produtos/1/ingredientes`
   - **Headers:** `Content-Type: application/json`
   - **Body (raw JSON):**
   ```json
   {
     "id_ingrediente": 5,
     "quantidade_necessaria": 0.10
   }
   ```
   - **Resposta Esperada (HTTP 201 Created):** Retorna o vínculo criado com sucesso.

---

### Caso de Teste 7: Fluxo Completo de Pedido (Order & Item Workflow)
*Objetivo: Abrir um novo pedido e adicionar itens calculando valores.*

1. **Criar Pedido:**
   - **Método:** `POST`
   - **URL:** `{{baseUrl}}/pedidos`
   - **Headers:** `Content-Type: application/json`
   - **Body (raw JSON):**
   ```json
   {
     "id_cliente": 1,
     "id_funcionario": 1,
     "id_status": 1,
     "id_endereco": 1,
     "forma_pagamento": "Cartão de Crédito",
     "taxa_entrega": 7.50,
     "valor_total": 52.50
   }
   ```
   - **Resposta Esperada (HTTP 201 Created):** Retorna o pedido com `id_pedido` gerado (ex: `2`).

2. **Adicionar Item ao Pedido Criado:**
   - **Método:** `POST`
   - **URL:** `{{baseUrl}}/pedidos/2/itens`
   - **Headers:** `Content-Type: application/json`
   - **Body (raw JSON):**
   ```json
   {
     "id_produto": 1,
     "quantidade": 1,
     "preco_unitario": 45.00,
     "subtotal": 45.00,
     "observacao": "Sem cebola e bem assada"
   }
   ```
   - **Resposta Esperada (HTTP 201 Created):** Retorna o item cadastrado com `id_item_pedido`.

3. **Consultar Pedido com Eager Loading dos Itens:**
   - **Método:** `GET`
   - **URL:** `{{baseUrl}}/pedidos/2`
   - **Resposta Esperada (HTTP 200 OK):**
   ```json
   {
     "id_pedido": 2,
     "id_cliente": 1,
     "id_funcionario": 1,
     "id_status": 1,
     "id_endereco": 1,
     "data_hora_pedido": "2026-11-17T22:00:00",
     "forma_pagamento": "Cartão de Crédito",
     "taxa_entrega": 7.50,
     "valor_total": 52.50,
     "itens": [
       {
         "id_item_pedido": 1,
         "id_pedido": 2,
         "id_produto": 1,
         "quantidade": 1,
         "preco_unitario": 45.00,
         "subtotal": 45.00,
         "observacao": "Sem cebola e bem assada"
       }
     ]
   }
   ```

---

### Caso de Teste 8: Validação de Contrato RFC 9457 — Erro 422 (Validation Error)
*Objetivo: Demonstrar a formatação de falhas de schema Pydantic no array `invalidParams`.*

- **Método:** `POST`
- **URL:** `{{baseUrl}}/usuarios`
- **Headers:** `Content-Type: application/json`
- **Body (raw JSON):**
```json
{
  "email": "email_invalido_sem_arroba",
  "senha": "123"
}
```
- **Resposta Esperada (HTTP 422 Unprocessable Entity):**
```json
{
  "type": "https://api.pizzariabarriga.dev/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Erro de validação nos parâmetros da requisição.",
  "instance": "/api/v1/usuarios",
  "invalidParams": [
    {
      "name": "email",
      "reason": "value is not a valid email address: An email address must have an @-sign."
    },
    {
      "name": "nome_perfil",
      "reason": "Field required"
    }
  ]
}
```

---

### Caso de Teste 9: Validação de Contrato RFC 9457 — Erro 400 (Bad Request / JSON Malformado)
*Objetivo: Testar payload corrompido.*

- **Método:** `POST`
- **URL:** `{{baseUrl}}/usuarios`
- **Headers:** `Content-Type: application/json`
- **Body (raw):**
```text
{ "email": "teste@pizzaria.com", (JSON CORROMPIDO SEM FECHAR CHAVES)
```
- **Resposta Esperada (HTTP 400 Bad Request):**
```json
{
  "type": "https://api.pizzariabarriga.dev/errors/bad-request",
  "title": "Bad Request",
  "status": 400,
  "detail": "O corpo da requisição contém JSON inválido ou malformado.",
  "instance": "/api/v1/usuarios",
  "invalidParams": [
    {
      "name": "1",
      "reason": "JSON decode error"
    }
  ]
}
```

---

### Caso de Teste 10: Validação de Contrato RFC 9457 — Erro 404 (Not Found)
*Objetivo: Testar busca de recurso inexistente.*

- **Método:** `GET`
- **URL:** `{{baseUrl}}/pedidos/999999`
- **Resposta Esperada (HTTP 404 Not Found):**
```json
{
  "type": "https://api.pizzariabarriga.dev/errors/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Pedido com ID 999999 não foi encontrado.",
  "instance": "/api/v1/pedidos/999999"
}
```

---

## 📌 6. Resumo dos Endpoints REST

| Recurso | Método | Rota | Descrição | Nível RBAC |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/login` | Autenticação e emissão de JWT | Público |
| **Auth** | `GET` | `/api/v1/auth/me` | Dados do usuário autenticado | Autenticado |
| **Usuários** | `GET` / `POST` | `/api/v1/usuarios` | Listar / Cadastrar usuário | Público / Admin |
| **Usuários** | `GET` / `PUT` / `DELETE` | `/api/v1/usuarios/{id}` | Buscar, Atualizar e Excluir | Admin |
| **Funcionários** | `GET` / `POST` | `/api/v1/funcionarios` | Listar / Cadastrar funcionário | Admin |
| **Funcionários** | `GET` / `PUT` / `DELETE` | `/api/v1/funcionarios/{id}` | Buscar, Atualizar e Excluir | Admin |
| **Clientes** | `GET` / `POST` | `/api/v1/clientes` | Listar / Cadastrar cliente | Autenticado |
| **Clientes** | `GET` / `PUT` / `DELETE` | `/api/v1/clientes/{id}` | Buscar, Atualizar e Excluir | Autenticado |
| **Endereços** | `GET` / `POST` | `/api/v1/enderecos` | Listar (filtro `?id_cliente`) / Criar | Autenticado |
| **Endereços** | `GET` / `PUT` / `DELETE` | `/api/v1/enderecos/{id}` | Buscar, Atualizar e Excluir | Autenticado |
| **Categorias** | `GET` / `POST` | `/api/v1/categorias` | Listar / Cadastrar categoria | Público / Admin |
| **Categorias** | `GET` / `PUT` / `DELETE` | `/api/v1/categorias/{id}` | Buscar, Atualizar e Excluir | Admin |
| **Ingredientes** | `GET` / `POST` | `/api/v1/ingredientes` | Listar / Cadastrar no estoque | Autenticado |
| **Ingredientes** | `GET` / `PUT` / `DELETE` | `/api/v1/ingredientes/{id}` | Buscar, Atualizar e Excluir | Autenticado |
| **Status** | `GET` / `POST` | `/api/v1/status` | Listar / Cadastrar status | Admin |
| **Status** | `GET` / `PUT` / `DELETE` | `/api/v1/status/{id}` | Buscar, Atualizar e Excluir | Admin |
| **Produtos** | `GET` / `POST` | `/api/v1/produtos` | Listar (filtros `?id_categoria`, `?disponivel`) / Criar | Público / Admin |
| **Produtos** | `GET` / `PUT` / `DELETE` | `/api/v1/produtos/{id}` | Buscar, Atualizar e Excluir | Admin/Func (DELETE proíbe Cliente: 403) |
| **Ingredientes do Produto** | `GET` / `POST` | `/api/v1/produtos/{id}/ingredientes` | Listar / Vincular insumos | Autenticado |
| **Ingredientes do Produto** | `DELETE` | `/api/v1/produtos/{id}/ingredientes/{idIng}` | Desvincular insumo | Autenticado |
| **Pedidos** | `GET` / `POST` | `/api/v1/pedidos` | Listar (Eager Loading) / Criar pedido | Autenticado |
| **Pedidos** | `GET` / `PUT` / `DELETE` | `/api/v1/pedidos/{id}` | Pedido detalhado com itens | Autenticado |
| **Itens do Pedido** | `GET` / `POST` | `/api/v1/pedidos/{id}/itens` | Listar itens / Adicionar item | Autenticado |
| **Itens do Pedido** | `PUT` / `DELETE` | `/api/v1/pedidos/{id}/itens/{idItem}` | Atualizar / Remover item | Autenticado |
