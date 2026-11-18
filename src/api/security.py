"""Security, JWT authentication, password hashing, and RBAC authorization dependencies.

Follows RFC 9457 for all authentication (401) and authorization (403) failures.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Union
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.database import get_db, hash_password, verify_password
from src.api.exceptions import ForbiddenException, UnauthorizedException
from src.api.models import UsuarioModel

# JWT Configuration
SECRET_KEY = "pizzaria-super-secret-jwt-signing-key-for-sdd-project"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# Use auto_error=False to catch missing authorization header and return RFC 9457 401 instead of FastAPI's default 403
security_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed JWT token with standard claims (sub, email, role, iat, exp)."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Ensure subject is string
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str, instance: Optional[str] = None) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(
            detail="Token de acesso expirado. Por favor, realize novo login.",
            instance=instance,
        )
    except jwt.PyJWTError:
        raise UnauthorizedException(
            detail="Token de acesso inválido ou malformado.",
            instance=instance,
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> UsuarioModel:
    """Dependency that authenticates the user from the Bearer token."""
    instance = request.url.path

    if not credentials or not credentials.credentials:
        raise UnauthorizedException(
            detail="Cabeçalho de autorização ausente ou token não fornecido.",
            instance=instance,
        )

    token = credentials.credentials
    payload = decode_access_token(token, instance=instance)

    sub: Optional[str] = payload.get("sub")
    if not sub:
        raise UnauthorizedException(
            detail="Token não contém identificação de usuário (sub).",
            instance=instance,
        )

    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise UnauthorizedException(
            detail="Identificador de usuário inválido contido no token.",
            instance=instance,
        )

    user = db.scalar(select(UsuarioModel).where(UsuarioModel.id_usuario == user_id))
    if not user:
        raise UnauthorizedException(
            detail="Usuário associado ao token não encontrado.",
            instance=instance,
        )

    if not user.ativo:
        raise UnauthorizedException(
            detail="Conta de usuário inativa.",
            instance=instance,
        )

    return user


def require_roles(*roles: Union[str, Iterable[str]]):
    """Factory dependency for Role-Based Access Control (RBAC).

    Accepts single or multiple roles (e.g. require_roles('ADMIN') or
    require_roles('ADMIN', 'FUNCIONARIO') or require_roles(['ADMIN', 'FUNCIONARIO'])).
    Raises RFC 9457 403 ForbiddenException if current_user's role is not authorized.
    """
    flat_roles: List[str] = []
    for r in roles:
        if isinstance(r, (list, tuple, set)):
            flat_roles.extend([str(item).strip().upper() for item in r])
        else:
            flat_roles.append(str(r).strip().upper())

    async def role_checker(
        request: Request,
        current_user: UsuarioModel = Depends(get_current_user),
    ) -> UsuarioModel:
        user_role = (current_user.nome_perfil or "").strip().upper()
        if user_role not in flat_roles:
            instance = request.url.path
            allowed_str = ", ".join(flat_roles)
            raise ForbiddenException(
                detail=(
                    f"Acesso negado: Perfil '{current_user.nome_perfil}' não possui permissão "
                    f"para esta operação. Papéis permitidos: [{allowed_str}]."
                ),
                instance=instance,
            )
        return current_user

    return role_checker


# Aliases for flexibility and styleguide naming
require_role = require_roles
