"""Provenance: bibliographic sources, citations, media and quantitative figures.

Citations, media links and figures use a polymorphic (entity_type, entity_id) pair so
that any registered entity can be documented without one join table per entity.
Valid ``entity_type`` values are the keys of ``app.models.registry.ENTITY_MODELS``.
"""

from datetime import date

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PublicationMixin, TimestampMixin, enum_col
from app.models.enums import Certainty, FigureMetric, MediaKind, Side, SourceKind


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    kind: Mapped[SourceKind] = mapped_column(enum_col(SourceKind), nullable=False)
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    authors: Mapped[str | None] = mapped_column(sa.Text)
    year: Mapped[int | None] = mapped_column(sa.Integer)
    publisher: Mapped[str | None] = mapped_column(sa.Text)
    place: Mapped[str | None] = mapped_column(sa.Text)
    series: Mapped[str | None] = mapped_column(sa.Text)
    isbn: Mapped[str | None] = mapped_column(sa.String(40))
    url: Mapped[str | None] = mapped_column(sa.Text)
    license: Mapped[str | None] = mapped_column(sa.Text)
    accessed_on: Mapped[date | None] = mapped_column(sa.Date)
    reliability_note: Mapped[str | None] = mapped_column(sa.Text)
    notes: Mapped[str | None] = mapped_column(sa.Text)


class Citation(TimestampMixin, Base):
    __tablename__ = "citations"
    __table_args__ = (sa.Index("ix_citations_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    entity_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    field: Mapped[str | None] = mapped_column(sa.String(80))  # which attribute the citation supports
    pages: Mapped[str | None] = mapped_column(sa.String(80))
    quote: Mapped[str | None] = mapped_column(sa.Text)
    note: Mapped[str | None] = mapped_column(sa.Text)

    source: Mapped[Source] = relationship(lazy="joined")


class Media(TimestampMixin, PublicationMixin, Base):
    """An image/document. Never published without license + attribution information."""

    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    kind: Mapped[MediaKind] = mapped_column(enum_col(MediaKind), nullable=False)
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text)
    file_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(sa.Text)
    source_url: Mapped[str | None] = mapped_column(sa.Text)
    author: Mapped[str | None] = mapped_column(sa.Text)
    date_created_text: Mapped[str | None] = mapped_column(sa.String(80))
    license: Mapped[str | None] = mapped_column(sa.String(120))
    license_url: Mapped[str | None] = mapped_column(sa.Text)
    attribution: Mapped[str | None] = mapped_column(sa.Text)
    license_verified: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    source_id: Mapped[int | None] = mapped_column(sa.ForeignKey("sources.id", ondelete="SET NULL"))

    __table_args__ = (
        # Publishing requires an explicit, verified license.
        sa.CheckConstraint(
            "status <> 'published' OR (license_verified AND license IS NOT NULL)",
            name="published_requires_license",
        ),
    )


class MediaLink(Base):
    __tablename__ = "media_links"
    __table_args__ = (sa.Index("ix_media_links_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    media_id: Mapped[int] = mapped_column(sa.ForeignKey("media.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    entity_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    caption: Mapped[str | None] = mapped_column(sa.Text)
    role: Mapped[str | None] = mapped_column(sa.String(40))  # e.g. portrait, insignia, gallery
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    media: Mapped[Media] = relationship(lazy="joined")


class Figure(TimestampMixin, Base):
    """A quantitative claim (strength, casualties...) attributed to one source.

    Several rows for the same entity/metric/side represent divergent figures.
    """

    __tablename__ = "figures"
    __table_args__ = (
        sa.Index("ix_figures_entity", "entity_type", "entity_id"),
        sa.CheckConstraint(
            "value_low IS NULL OR value_high IS NULL OR value_low <= value_high", name="value_range"
        ),
        sa.CheckConstraint(
            "value_low IS NOT NULL OR value_high IS NOT NULL OR value_text IS NOT NULL", name="has_value"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    entity_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    metric: Mapped[FigureMetric] = mapped_column(enum_col(FigureMetric), nullable=False)
    side: Mapped[Side | None] = mapped_column(enum_col(Side))
    polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="SET NULL"))
    value_low: Mapped[int | None] = mapped_column(sa.BigInteger)
    value_high: Mapped[int | None] = mapped_column(sa.BigInteger)
    value_text: Mapped[str | None] = mapped_column(sa.Text)
    scope_note: Mapped[str | None] = mapped_column(sa.Text)  # e.g. "1 July only", "British figures"
    as_of_date: Mapped[date | None] = mapped_column(sa.Date)
    source_id: Mapped[int | None] = mapped_column(sa.ForeignKey("sources.id", ondelete="RESTRICT"))
    pages: Mapped[str | None] = mapped_column(sa.String(80))
    certainty: Mapped[Certainty] = mapped_column(enum_col(Certainty), default=Certainty.estimated, nullable=False)
    notes: Mapped[str | None] = mapped_column(sa.Text)

    source: Mapped[Source | None] = relationship(lazy="joined")
