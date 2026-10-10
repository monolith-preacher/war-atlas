"""Command line utilities.

    python -m app.cli seed [--reset]          load curated seed data
    python -m app.cli create-user EMAIL --role admin|reviewer|editor
    python -m app.cli bootstrap               create ADMIN_EMAIL/ADMIN_PASSWORD admin if missing
    python -m app.cli wait-db [--timeout 60]  wait until the database accepts connections
"""

import argparse
import getpass
import logging
import pathlib
import sys
import time

from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.db import SessionLocal, engine
from app.core.security import hash_password
from app.models import User
from app.models.enums import UserRole
from app.services.seed import SeedError, run_seed


def cmd_seed(args: argparse.Namespace) -> int:
    settings = get_settings()
    data_dir = pathlib.Path(settings.data_dir) if settings.data_dir else None
    with SessionLocal() as db:
        try:
            stats = run_seed(db, reset=args.reset, data_dir=data_dir)
        except SeedError as exc:
            db.rollback()
            print(f"seed failed: {exc}", file=sys.stderr)
            return 1
    if stats is None:
        print("Database already seeded; nothing done (use --reset to reload content).")
    else:
        for k, v in sorted(stats.items()):
            print(f"  {k:28s} {v}")
    return 0


def _create_user(email: str, password: str, role: str) -> bool:
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email.lower())):
            return False
        db.add(User(email=email.lower(), password_hash=hash_password(password), role=UserRole(role)))
        db.commit()
        return True


def cmd_create_user(args: argparse.Namespace) -> int:
    password = args.password or getpass.getpass("Password: ")
    if len(password) < 10:
        print("password must have at least 10 characters", file=sys.stderr)
        return 1
    created = _create_user(args.email, password, args.role)
    print("user created" if created else "user already exists")
    return 0


def cmd_bootstrap(_: argparse.Namespace) -> int:
    s = get_settings()
    if s.admin_email and s.admin_password:
        created = _create_user(s.admin_email, s.admin_password, "admin")
        print(f"bootstrap admin {s.admin_email}: {'created' if created else 'already exists'}")
    else:
        print("ADMIN_EMAIL/ADMIN_PASSWORD not set; no admin bootstrapped")
    return 0


def cmd_wait_db(args: argparse.Namespace) -> int:
    deadline = time.time() + args.timeout
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return 0
        except Exception as exc:  # noqa: BLE001
            if time.time() > deadline:
                print(f"database not reachable: {exc}", file=sys.stderr)
                return 1
            time.sleep(1.5)


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser(prog="python -m app.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed")
    s.add_argument("--reset", action="store_true", help="delete all content before loading")
    s.set_defaults(func=cmd_seed)
    u = sub.add_parser("create-user")
    u.add_argument("email")
    u.add_argument("--role", choices=[r.value for r in UserRole], default="editor")
    u.add_argument("--password", help="omit to be prompted")
    u.set_defaults(func=cmd_create_user)
    b = sub.add_parser("bootstrap")
    b.set_defaults(func=cmd_bootstrap)
    w = sub.add_parser("wait-db")
    w.add_argument("--timeout", type=int, default=60)
    w.set_defaults(func=cmd_wait_db)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
