"""Test configuration.

Tests run against a dedicated PostgreSQL/PostGIS database (TEST_DATABASE_URL, default:
the DATABASE_URL database name suffixed with ``_test``). The schema is created with the
real Alembic migrations and loaded with the real seed data, so tests exercise the same
constraints, views and data as production.
"""

import os
import pathlib

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def _test_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    base = make_url(os.environ.get("DATABASE_URL", "postgresql+psycopg://waratlas:waratlas@localhost:5432/waratlas"))
    return base.set(database=f"{base.database}_test").render_as_string(hide_password=False)


TEST_URL = _test_url()
os.environ["DATABASE_URL"] = TEST_URL
os.environ["ENVIRONMENT"] = "test"
os.environ["IMPORTERS_ENABLED"] = "false"
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-123")


def _ensure_database() -> None:
    url = make_url(TEST_URL)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def database():
    _ensure_database()
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(pathlib.Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(pathlib.Path(__file__).resolve().parents[1] / "alembic"))
    command.upgrade(cfg, "head")

    from app.core.db import SessionLocal
    from app.services.seed import run_seed

    with SessionLocal() as db:
        run_seed(db, reset=True)
    yield


@pytest.fixture
def db():
    from app.core.db import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def client(database):
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def _make_user(email: str, role: str) -> None:
    from sqlalchemy import select

    from app.core.db import SessionLocal
    from app.core.security import hash_password
    from app.models import User
    from app.models.enums import UserRole

    with SessionLocal() as s:
        if not s.scalar(select(User).where(User.email == email)):
            s.add(User(email=email, password_hash=hash_password("senha-de-teste-123"), role=UserRole(role)))
            s.commit()


@pytest.fixture(scope="session")
def auth_headers(client):
    def _headers(role: str = "admin") -> dict:
        email = f"{role}@test.local"
        _make_user(email, role)
        r = client.post("/api/v1/auth/login", data={"username": email, "password": "senha-de-teste-123"})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _headers
