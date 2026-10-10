"""Users, revision log and import staging."""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, enum_col
from app.models.enums import ImportStatus, UserRole


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(sa.String(120))
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(enum_col(UserRole), default=UserRole.editor, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class Revision(Base):
    """Append-only audit log of administrative changes."""

    __tablename__ = "revisions"
    __table_args__ = (sa.Index("ix_revisions_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    entity_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    user_id: Mapped[int | None] = mapped_column(sa.ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(sa.String(30), nullable=False)  # create|update|delete|status
    changes: Mapped[dict | None] = mapped_column(JSONB)
    comment: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


class ImportBatch(TimestampMixin, Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(sa.String(80), nullable=False)  # wikidata, csv...
    description: Mapped[str | None] = mapped_column(sa.Text)
    created_by: Mapped[int | None] = mapped_column(sa.ForeignKey("users.id", ondelete="SET NULL"))


class ImportRecord(TimestampMixin, Base):
    """A staged external record. It never reaches public tables without human review."""

    __tablename__ = "import_records"
    __table_args__ = (sa.Index("ix_import_records_external", "external_source", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(sa.ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    external_source: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    external_id: Mapped[str] = mapped_column(sa.String(80), nullable=False)
    external_url: Mapped[str | None] = mapped_column(sa.Text)
    license: Mapped[str | None] = mapped_column(sa.String(80))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)  # raw data as received
    proposed: Mapped[dict | None] = mapped_column(JSONB)  # mapped fields proposed for the target entity
    warnings: Mapped[list | None] = mapped_column(JSONB)
    status: Mapped[ImportStatus] = mapped_column(enum_col(ImportStatus), default=ImportStatus.pending, nullable=False, index=True)
    target_entity_id: Mapped[int | None] = mapped_column(sa.Integer)
    reviewer_id: Mapped[int | None] = mapped_column(sa.ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(sa.Text)
