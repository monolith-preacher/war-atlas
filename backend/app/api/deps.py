"""FastAPI dependencies: DB session, optional date parsing, authentication and roles."""

from collections.abc import Callable
from datetime import date

import jwt
from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.core.security import decode_token
from app.models import User
from app.models.enums import UserRole

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

ROLE_RANK = {UserRole.editor: 1, UserRole.reviewer: 2, UserRole.admin: 3}


def date_param(description: str = "Data de referência (AAAA-MM-DD)") -> Callable:
    def _dep(date_: date | None = Query(None, alias="date", description=description)) -> date | None:
        return date_
    return _dep


def current_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    if not token:
        raise ApiError(401, "not_authenticated", "Autenticação necessária.")
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "token_expired", "Sessão expirada. Entre novamente.")
    except jwt.PyJWTError:
        raise ApiError(401, "invalid_token", "Token inválido.")
    user = db.scalar(select(User).where(User.email == payload.get("sub")))
    if not user or not user.is_active:
        raise ApiError(401, "invalid_user", "Usuário inexistente ou desativado.")
    return user


def require_role(minimum: UserRole) -> Callable:
    def _dep(user: User = Depends(current_user)) -> User:
        if ROLE_RANK[user.role] < ROLE_RANK[minimum]:
            raise ApiError(403, "forbidden", f"Permissão insuficiente (requer perfil '{minimum.value}' ou superior).")
        return user
    return _dep
