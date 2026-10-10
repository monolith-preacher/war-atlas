"""Declarative base and reusable column mixins.

Conventions
-----------
* Temporal validity is expressed with ``valid_from``/``valid_to`` (inclusive) plus a
  precision for each bound. ``NULL`` means "not documented" and is treated as an open
  bound by temporal queries, *except* that the UI always labels it as undocumented.
* Every curated entity carries a publication status and provenance metadata.
"""

from datetime import date, datetime
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.enums import Certainty, DatePrecision, PublicationStatus

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = sa.MetaData(naming_convention=NAMING_CONVENTION)


def enum_col(enum_cls: type[StrEnum], name: str | None = None) -> sa.Enum:
    return sa.Enum(
        enum_cls,
        name=name or enum_cls.__name__.lower(),
        native_enum=False,
        create_constraint=True,
        length=40,
        values_callable=lambda e: [x.value for x in e],
        validate_strings=True,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )


class PublicationMixin:
    status: Mapped[PublicationStatus] = mapped_column(
        enum_col(PublicationStatus), default=PublicationStatus.draft, nullable=False, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(sa.Text)


class ProvenanceMixin:
    certainty: Mapped[Certainty] = mapped_column(
        enum_col(Certainty), default=Certainty.unverified, nullable=False
    )
    provenance_note: Mapped[str | None] = mapped_column(sa.Text)
    wikidata_id: Mapped[str | None] = mapped_column(sa.String(20), index=True)


class TemporalMixin:
    """Inclusive validity interval with per-bound precision."""

    valid_from: Mapped[date | None] = mapped_column(sa.Date)
    valid_from_precision: Mapped[DatePrecision] = mapped_column(
        enum_col(DatePrecision, "valid_from_precision"), default=DatePrecision.day, nullable=False
    )
    valid_to: Mapped[date | None] = mapped_column(sa.Date)
    valid_to_precision: Mapped[DatePrecision] = mapped_column(
        enum_col(DatePrecision, "valid_to_precision"), default=DatePrecision.day, nullable=False
    )



def interval_check(start: str = "valid_from", end: str = "valid_to", name: str = "valid_interval"):
    """CHECK constraint ensuring start <= end when both are known."""
    return sa.CheckConstraint(f"{start} IS NULL OR {end} IS NULL OR {start} <= {end}", name=name)


def daterange_sql(table: str = "") -> str:
    """SQL expression for the inclusive daterange of a TemporalMixin row (used in constraints)."""
    p = f"{table}." if table else ""
    return f"daterange({p}valid_from, {p}valid_to, '[]')"
