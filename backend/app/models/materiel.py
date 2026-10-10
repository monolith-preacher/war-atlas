"""Equipment, variants, users, uniforms, camouflage patterns and insignia.

Important rule: national service (EquipmentUser) never implies that a given unit used
the equipment. Unit-level use must be recorded explicitly in UnitEquipment.
"""

from datetime import date

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    Base,
    ProvenanceMixin,
    PublicationMixin,
    TemporalMixin,
    TimestampMixin,
    enum_col,
    interval_check,
)
from app.models.enums import Certainty, DatePrecision, EquipmentCategory


class Equipment(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    __tablename__ = "equipment"
    __table_args__ = (interval_check("service_from", "service_to", "service_interval"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    category: Mapped[EquipmentCategory] = mapped_column(enum_col(EquipmentCategory), nullable=False, index=True)
    type_label: Mapped[str | None] = mapped_column(sa.Text)  # "Heavy tank", "Bolt-action rifle"...
    origin_polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="SET NULL"), index=True)
    manufacturer: Mapped[str | None] = mapped_column(sa.Text)
    designer: Mapped[str | None] = mapped_column(sa.Text)
    design_period: Mapped[str | None] = mapped_column(sa.String(60))
    production_period: Mapped[str | None] = mapped_column(sa.String(60))
    number_built: Mapped[str | None] = mapped_column(sa.String(80))
    service_from: Mapped[date | None] = mapped_column(sa.Date)
    service_from_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "service_from_precision"), default=DatePrecision.year, nullable=False)
    service_to: Mapped[date | None] = mapped_column(sa.Date)
    service_to_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "service_to_precision"), default=DatePrecision.year, nullable=False)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    description: Mapped[str | None] = mapped_column(sa.Text)
    operational_history: Mapped[str | None] = mapped_column(sa.Text)
    # [{"key": "weight", "label": "Peso", "value": "28", "unit": "t (longas)", "note": "Male"}]
    specs: Mapped[list | None] = mapped_column(JSONB)


class EquipmentVariant(TimestampMixin, PublicationMixin, Base):
    __tablename__ = "equipment_variants"
    __table_args__ = (interval_check("service_from", "service_to", "service_interval"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    equipment_id: Mapped[int] = mapped_column(sa.ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    service_from: Mapped[date | None] = mapped_column(sa.Date)
    service_to: Mapped[date | None] = mapped_column(sa.Date)
    specs: Mapped[list | None] = mapped_column(JSONB)


class EquipmentUser(TimestampMixin, TemporalMixin, Base):
    """National service of an equipment (polity level)."""

    __tablename__ = "equipment_users"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(sa.ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    polity_id: Mapped[int] = mapped_column(sa.ForeignKey("polities.id", ondelete="CASCADE"), nullable=False, index=True)
    force_id: Mapped[int | None] = mapped_column(sa.ForeignKey("armed_forces.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(sa.Text)


class UnitEquipment(TimestampMixin, TemporalMixin, Base):
    """Documented use of an equipment by a specific unit during an interval."""

    __tablename__ = "unit_equipment"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(sa.ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    equipment_id: Mapped[int] = mapped_column(sa.ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id: Mapped[int | None] = mapped_column(sa.ForeignKey("equipment_variants.id", ondelete="SET NULL"))
    quantity: Mapped[int | None] = mapped_column(sa.Integer)
    quantity_note: Mapped[str | None] = mapped_column(sa.Text)
    certainty: Mapped[Certainty] = mapped_column(enum_col(Certainty), default=Certainty.unverified, nullable=False)
    notes: Mapped[str | None] = mapped_column(sa.Text)


class CamouflagePattern(TimestampMixin, PublicationMixin, ProvenanceMixin, TemporalMixin, Base):
    """Camouflage pattern or paint scheme (for uniforms or equipment)."""

    __tablename__ = "camouflage_patterns"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    applies_to: Mapped[str] = mapped_column(sa.String(30), default="uniform", nullable=False)  # uniform|equipment|both
    polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="SET NULL"), index=True)
    force_id: Mapped[int | None] = mapped_column(sa.ForeignKey("armed_forces.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(sa.Text)
    usage_note: Mapped[str | None] = mapped_column(sa.Text)
    # [{"name": "Feldgrau", "hex": "#5d6450", "note": "approximate rendering"}]
    colors: Mapped[list | None] = mapped_column(JSONB)


class EquipmentCamouflage(TimestampMixin, TemporalMixin, Base):
    __tablename__ = "equipment_camouflages"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(sa.ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    pattern_id: Mapped[int] = mapped_column(sa.ForeignKey("camouflage_patterns.id", ondelete="CASCADE"), nullable=False, index=True)
    theater_id: Mapped[int | None] = mapped_column(sa.ForeignKey("theaters.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(sa.Text)


class Uniform(TimestampMixin, PublicationMixin, ProvenanceMixin, TemporalMixin, Base):
    __tablename__ = "uniforms"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    polity_id: Mapped[int] = mapped_column(sa.ForeignKey("polities.id", ondelete="CASCADE"), nullable=False, index=True)
    force_id: Mapped[int | None] = mapped_column(sa.ForeignKey("armed_forces.id", ondelete="SET NULL"))
    unit_id: Mapped[int | None] = mapped_column(sa.ForeignKey("units.id", ondelete="SET NULL"))
    theater_id: Mapped[int | None] = mapped_column(sa.ForeignKey("theaters.id", ondelete="SET NULL"))
    camouflage_id: Mapped[int | None] = mapped_column(sa.ForeignKey("camouflage_patterns.id", ondelete="SET NULL"))
    role_note: Mapped[str | None] = mapped_column(sa.Text)  # function / conditions (e.g. infantry, tank crews)
    description: Mapped[str | None] = mapped_column(sa.Text)
    colors: Mapped[list | None] = mapped_column(JSONB)


class Insignia(TimestampMixin, PublicationMixin, ProvenanceMixin, TemporalMixin, Base):
    __tablename__ = "insignia"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(30), nullable=False)  # unit|rank|branch|award
    polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="SET NULL"))
    unit_id: Mapped[int | None] = mapped_column(sa.ForeignKey("units.id", ondelete="SET NULL"), index=True)
    description: Mapped[str | None] = mapped_column(sa.Text)
