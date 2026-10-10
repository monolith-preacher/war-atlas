"""Health check and authentication."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import __version__
from app.api.deps import current_user
from app.core.db import get_db
from app.core.errors import ApiError
from app.core.security import create_access_token, verify_password
from app.models import Conflict, User

router = APIRouter(tags=["sistema"])


@router.get("/health", summary="Estado da API e do banco de dados")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        seeded = db.scalar(select(Conflict.id).limit(1)) is not None
        postgis = db.scalar(text("SELECT postgis_lib_version()"))
        return {"status": "ok", "version": __version__, "database": "ok", "postgis": postgis, "has_content": seeded}
    except Exception as exc:  # noqa: BLE001
        raise ApiError(503, "database_unavailable", "Banco de dados indisponível.", str(exc).split("\n")[0])


@router.post("/auth/login", summary="Autenticação administrativa (OAuth2 password)")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise ApiError(401, "invalid_credentials", "E-mail ou senha inválidos.")
    user.last_login_at = datetime.now(UTC)
    db.commit()
    token, expires_in = create_access_token(user.email, user.role.value)
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in,
            "user": {"email": user.email, "role": user.role.value, "display_name": user.display_name}}


@router.get("/auth/me", summary="Usuário autenticado")
def me(user: User = Depends(current_user)):
    return {"email": user.email, "role": user.role.value, "display_name": user.display_name}
