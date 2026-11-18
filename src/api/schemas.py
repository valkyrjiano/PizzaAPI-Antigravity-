"""Data schemas and DTOs for Pizzaria API using Pydantic v2.

Matches specifications from SPEC.yaml, Apidog, and STYLEGUIDE.md.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class BaseSchema(BaseModel):
    """Base schema enforcing Pydantic v2 modern configuration."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


# ==========================================
# RFC 9457 / Problem Details Error Schemas
# ==========================================


class InvalidParam(BaseSchema):
    """Specific invalid field identifier and explanation for RFC 9457."""

    name: str = Field(..., description="Nome do campo com erro de validação")
    reason: str = Field(..., description="Motivo ou descrição do erro de validação")


class ApiError(BaseSchema):
    """RFC 9457 / Problem Details standard error payload."""

    type: str = Field(..., description="URI de referência do tipo de erro")
    title: str = Field(..., description="Resumo curto e legível do erro")
    status: int = Field(..., description="Código de status HTTP")
    detail: str = Field(..., description="Explicação detalhada da ocorrência")
    instance: str = Field(..., description="URI da requisição que originou o erro")
    invalidParams: Optional[List[InvalidParam]] = Field(
        default=None,
        description="Lista de falhas de validação de parâmetros, se aplicável",
    )


class Error(BaseSchema):
    """Generic error model specified in SPEC.yaml."""

    message: str = Field(..., description="Mensagem descritiva do erro")
    details: Optional[str] = Field(default=None, description="Detalhes adicionais do erro")


# ==========================================
# Authentication & Authorization DTOs
# ==========================================


class LoginRequestDTO(BaseSchema):
    """DTO para requisição de login e obtenção de token JWT."""

    email: EmailStr = Field(..., max_length=160, description="E-mail de autenticação")
    senha: str = Field(..., max_length=255, description="Senha do usuário")


# Alias para compatibilidade com nomenclaturas de rotas
LoginInput = LoginRequestDTO


class TokenResponseDTO(BaseSchema):
    """DTO para resposta de autenticação com token JWT."""

    access_token: str = Field(..., description="Token de acesso JWT")
    token_type: str = Field(default="bearer", description="Tipo de token (padrão: bearer)")


# Alias para compatibilidade com contratos
TokenResponse = TokenResponseDTO


class UserResponse(BaseSchema):
    """DTO para exibição segura dos dados de usuário autenticado (/auth/me)."""

    id_usuario: int = Field(..., description="Identificador único do usuário")
    email: EmailStr = Field(..., max_length=160, description="E-mail cadastrado")
    nome_perfil: str = Field(..., max_length=80, description="Nome do perfil de acesso (RBAC)")
    ativo: bool = Field(default=True, description="Indicador se a conta está ativa")
    descricao: Optional[str] = Field(default=None, max_length=500, description="Descrição opcional")
    role: Optional[str] = Field(default=None, description="Papel RBAC normalizado")

    @model_validator(mode="after")
    def populate_role_from_perfil(self) -> "UserResponse":
        if self.role is None:
            self.role = self.nome_perfil
        return self


# Alias para compatibilidade com rotas de auth
UsuarioAuthResponse = UserResponse


class TokenData(BaseSchema):
    """DTO contendo os dados decodificados do payload JWT."""

    sub: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


# ==========================================
# Usuários & Atores
# ==========================================


class UsuarioInput(BaseSchema):
    """Contrato de entrada para criação/atualização de usuário."""

    email: EmailStr = Field(..., max_length=160, description="E-mail do usuário")
    senha: str = Field(..., max_length=255, description="Senha de acesso")
    ativo: bool = Field(default=True, description="Status de ativação do usuário")
    nome_perfil: str = Field(..., max_length=80, description="Perfil de acesso (ex: ADMIN, FUNCIONARIO, CLIENTE)")
    descricao: Optional[str] = Field(default=None, max_length=500, description="Descrição complementar")


class Usuario(BaseSchema):
    """Contrato completo de usuário persistido."""

    id_usuario: int = Field(..., description="ID único do usuário")
    email: EmailStr = Field(..., max_length=160, description="E-mail do usuário")
    senha: str = Field(..., max_length=255, description="Hash da senha do usuário")
    ativo: bool = Field(default=True, description="Status de ativação do usuário")
    nome_perfil: str = Field(..., max_length=80, description="Perfil de acesso")
    descricao: Optional[str] = Field(default=None, max_length=500, description="Descrição complementar")


class FuncionarioInput(BaseSchema):
    """Contrato de entrada para cadastro/atualização de funcionário."""

    id_usuario: int = Field(..., description="ID do usuário associado")
    nome: str = Field(..., max_length=120, description="Nome completo do funcionário")
    cpf: str = Field(..., max_length=14, description="CPF formatado ou dígitos")
    cargo: str = Field(..., max_length=80, description="Cargo ou função exercida")
    telefone: Optional[str] = Field(default=None, max_length=20, description="Telefone de contato")


class Funcionario(BaseSchema):
    """Contrato completo de funcionário persistido."""

    id_funcionario: int = Field(..., description="ID único do funcionário")
    id_usuario: int = Field(..., description="ID do usuário associado")
    nome: str = Field(..., max_length=120, description="Nome completo do funcionário")
    cpf: str = Field(..., max_length=14, description="CPF do funcionário")
    cargo: str = Field(..., max_length=80, description="Cargo exercido")
    telefone: Optional[str] = Field(default=None, max_length=20, description="Telefone de contato")


class ClienteInput(BaseSchema):
    """Contrato de entrada para cadastro/atualização de cliente."""

    id_usuario: int = Field(..., description="ID do usuário associado")
    nome: str = Field(..., max_length=120, description="Nome completo do cliente")
    cpf: str = Field(..., max_length=14, description="CPF do cliente")
    telefone: Optional[str] = Field(default=None, max_length=20, description="Telefone de contato")


class Cliente(BaseSchema):
    """Contrato completo de cliente persistido."""

    id_cliente: int = Field(..., description="ID único do cliente")
    id_usuario: int = Field(..., description="ID do usuário associado")
    nome: str = Field(..., max_length=120, description="Nome completo do cliente")
    cpf: str = Field(..., max_length=14, description="CPF do cliente")
    telefone: Optional[str] = Field(default=None, max_length=20, description="Telefone de contato")


# ==========================================
# Endereços & Categorias
# ==========================================


class EnderecoInput(BaseSchema):
    """Contrato de entrada para criação/atualização de endereço."""

    id_cliente: int = Field(..., description="ID do cliente proprietário do endereço")
    cep: str = Field(..., max_length=9, description="Código de Endereçamento Postal (CEP)")
    logradouro: str = Field(..., max_length=160, description="Logradouro (rua, avenida, etc.)")
    numero: str = Field(..., max_length=20, description="Número do imóvel")
    complemento: Optional[str] = Field(default=None, max_length=100, description="Complemento ou referência")
    bairro: str = Field(..., max_length=100, description="Bairro")
    cidade: str = Field(..., max_length=100, description="Cidade")
    uf: str = Field(..., min_length=2, max_length=2, description="Unidade Federativa (UF com 2 letras)")


class Endereco(BaseSchema):
    """Contrato completo de endereço persistido."""

    id_endereco: int = Field(..., description="ID único do endereço")
    id_cliente: int = Field(..., description="ID do cliente proprietário")
    cep: str = Field(..., max_length=9, description="CEP")
    logradouro: str = Field(..., max_length=160, description="Logradouro")
    numero: str = Field(..., max_length=20, description="Número")
    complemento: Optional[str] = Field(default=None, max_length=100, description="Complemento")
    bairro: str = Field(..., max_length=100, description="Bairro")
    cidade: str = Field(..., max_length=100, description="Cidade")
    uf: str = Field(..., min_length=2, max_length=2, description="UF")


class CategoriaInput(BaseSchema):
    """Contrato de entrada para criação/atualização de categoria."""

    nome: str = Field(..., max_length=100, description="Nome da categoria (ex: Pizzas Salgadas)")
    descricao: Optional[str] = Field(default=None, max_length=500, description="Descrição da categoria")


class Categoria(BaseSchema):
    """Contrato completo de categoria persistida."""

    id_categoria: int = Field(..., description="ID único da categoria")
    nome: str = Field(..., max_length=100, description="Nome da categoria")
    descricao: Optional[str] = Field(default=None, max_length=500, description="Descrição da categoria")


# ==========================================
# Ingredientes & Produtos
# ==========================================


class IngredienteInput(BaseSchema):
    """Contrato de entrada para cadastro/atualização de ingrediente."""

    nome: str = Field(..., max_length=120, description="Nome do ingrediente")
    quantidade_estoque: float = Field(default=0.0, ge=0, description="Quantidade disponível em estoque")
    unidade_medida: str = Field(..., max_length=20, description="Unidade de medida (kg, g, un, l, ml)")


class Ingrediente(BaseSchema):
    """Contrato completo de ingrediente persistido."""

    id_ingrediente: int = Field(..., description="ID único do ingrediente")
    nome: str = Field(..., max_length=120, description="Nome do ingrediente")
    quantidade_estoque: float = Field(..., ge=0, description="Quantidade em estoque")
    unidade_medida: str = Field(..., max_length=20, description="Unidade de medida")


class ProdutoInput(BaseSchema):
    """Contrato de entrada para criação/atualização de produto."""

    id_categoria: int = Field(..., description="ID da categoria à qual o produto pertence")
    nome: str = Field(..., max_length=120, description="Nome do produto")
    tamanho: str = Field(..., max_length=30, description="Tamanho do produto (ex: Broto, Grande, 2L)")
    preco: float = Field(..., ge=0, description="Preço unitário de venda")
    disponivel: bool = Field(default=True, description="Indicador se o produto está disponível para venda")


class Produto(BaseSchema):
    """Contrato completo de produto persistido."""

    id_produto: int = Field(..., description="ID único do produto")
    id_categoria: int = Field(..., description="ID da categoria")
    nome: str = Field(..., max_length=120, description="Nome do produto")
    tamanho: str = Field(..., max_length=30, description="Tamanho")
    preco: float = Field(..., ge=0, description="Preço unitário")
    disponivel: bool = Field(default=True, description="Disponibilidade")


class IngredienteProdutoVinculo(BaseSchema):
    """Contrato de entrada para vinculação de ingrediente a um produto."""

    id_ingrediente: int = Field(..., description="ID do ingrediente")
    quantidade_necessaria: float = Field(..., ge=0, description="Quantidade necessária por unidade do produto")


# Alias para flexibilidade de nomenclatura
IngredienteProdutoInput = IngredienteProdutoVinculo


class IngredienteProduto(BaseSchema):
    """Contrato completo de associação entre Produto e Ingrediente."""

    id_ingrediente_produto: int = Field(..., description="ID da associação")
    id_produto: int = Field(..., description="ID do produto")
    id_ingrediente: int = Field(..., description="ID do ingrediente")
    quantidade_necessaria: float = Field(..., ge=0, description="Quantidade necessária")


# ==========================================
# Status, Pedidos & Itens
# ==========================================


class StatusInput(BaseSchema):
    """Contrato de entrada para criação/atualização de status de pedido."""

    nome_status: str = Field(..., max_length=50, description="Nome do status (ex: Recebido, Em Preparo)")


class Status(BaseSchema):
    """Contrato completo de status persistido."""

    id_status: int = Field(..., description="ID único do status")
    nome_status: str = Field(..., max_length=50, description="Nome descritivo do status")


class ItemPedidoInput(BaseSchema):
    """Contrato de entrada para inclusão de item em um pedido."""

    id_produto: int = Field(..., description="ID do produto selecionado")
    quantidade: int = Field(..., ge=1, description="Quantidade do item (mínimo 1)")
    preco_unitario: float = Field(..., ge=0, description="Preço unitário no momento do pedido")
    subtotal: float = Field(..., ge=0, description="Subtotal do item (quantidade * preco_unitario)")
    observacao: Optional[str] = Field(default=None, max_length=500, description="Observação específica para o item")


class ItemPedido(BaseSchema):
    """Contrato completo de item de pedido persistido."""

    id_item_pedido: int = Field(..., description="ID único do item de pedido")
    id_pedido: int = Field(..., description="ID do pedido associado")
    id_produto: int = Field(..., description="ID do produto")
    quantidade: int = Field(..., ge=1, description="Quantidade")
    preco_unitario: float = Field(..., ge=0, description="Preço unitário")
    subtotal: float = Field(..., ge=0, description="Subtotal do item")
    observacao: Optional[str] = Field(default=None, max_length=500, description="Observação")


class PedidoInput(BaseSchema):
    """Contrato de entrada para criação/atualização de pedido."""

    id_cliente: int = Field(..., description="ID do cliente solicitante")
    id_funcionario: int = Field(..., description="ID do funcionário responsável")
    id_status: int = Field(..., description="ID do status atual do pedido")
    id_endereco: int = Field(..., description="ID do endereço de entrega")
    forma_pagamento: str = Field(..., max_length=40, description="Forma de pagamento (ex: Cartão, Pix, Dinheiro)")
    taxa_entrega: float = Field(default=0.0, ge=0, description="Taxa de entrega cobrada")
    valor_total: float = Field(..., ge=0, description="Valor total consolidado do pedido")


class Pedido(BaseSchema):
    """Contrato completo de pedido persistido."""

    id_pedido: int = Field(..., description="ID único do pedido")
    id_cliente: int = Field(..., description="ID do cliente")
    id_funcionario: int = Field(..., description="ID do funcionário")
    id_status: int = Field(..., description="ID do status")
    id_endereco: int = Field(..., description="ID do endereço de entrega")
    data_hora_pedido: datetime = Field(..., description="Data e hora da realização do pedido")
    forma_pagamento: str = Field(..., max_length=40, description="Forma de pagamento")
    taxa_entrega: float = Field(..., ge=0, description="Taxa de entrega")
    valor_total: float = Field(..., ge=0, description="Valor total consolidado")


class PedidoDetalhado(Pedido):
    """Contrato estendido de pedido incluindo sua lista de itens vinculados."""

    itens: List[ItemPedido] = Field(default_factory=list, description="Lista de itens do pedido")
