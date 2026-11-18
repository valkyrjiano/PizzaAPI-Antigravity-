"""Authentication router: /auth/login and /auth/me."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db, verify_password
from src.api.exceptions import UnauthorizedException
from src.api.models import UsuarioModel
from src.api.schemas import LoginRequestDTO, TokenResponseDTO, UserResponse
from src.api.security import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenResponseDTO,
    summary="Autenticar usuário e obter token JWT",
)
def login(credentials: LoginRequestDTO, db: Session = Depends(get_db)):
    """Valida email e senha e retorna o Bearer Token JWT."""
    user = db.scalar(
        select(UsuarioModel).where(UsuarioModel.email == credentials.email)
    )
    if not user or not verify_password(credentials.senha, user.senha):
        raise UnauthorizedException(
            detail="Credenciais inválidas: e-mail ou senha incorretos."
        )

    if not user.ativo:
        raise UnauthorizedException(
            detail="Conta de usuário inativa. Entre em contato com o suporte."
        )

    token = create_access_token(
        data={
            "sub": str(user.id_usuario),
            "email": user.email,
            "role": user.nome_perfil,
        }
    )
    return TokenResponseDTO(access_token=token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obter perfil do usuário autenticado",
)
def get_me(current_user: UsuarioModel = Depends(get_current_user)):
    """Retorna os dados do usuário atualmente autenticado via JWT."""
    return UserResponse.model_validate(current_user)
