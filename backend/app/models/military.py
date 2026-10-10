"""Armed forces, units, people and their time-bounded relations.

Temporal integrity is enforced in the database:
* a unit cannot have two overlapping *organic* parents;
* a unit cannot have two overlapping titular commanders.
(Exclusion constraints, see migration 0001 — requires btree_gist.)
"""

from datetime import date

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    ProvenanceMixin,
    PublicationMixin,
    TemporalMixin,
    TimestampMixin,
    enum_col,
    interval_check,
)
from app.models.enums import BranchKind, DatePrecision, Echelon, PositionKind, Side, SubordinationKind

_DATERANGE = sa.func.daterange(sa.literal_column("valid_from"), sa.literal_column("valid_to"), sa.literal_column("'[]'"))


class ArmedForce(TimestampMixin, PublicationMixin, ProvenanceMixin, TemporalMixin, Base):
    """A national military organisation (e.g. Imperial German Army, Royal Navy, Waffen-SS)."""

    __tablename__ = "armed_forces"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    polity_id: Mapped[int] = mapped_column(sa.ForeignKey("polities.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(sa.ForeignKey("armed_forces.id", ondelete="SET NULL"))
    branch: Mapped[BranchKind] = mapped_column(enum_col(BranchKind), nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    description: Mapped[str | None] = mapped_column(sa.Text)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)


class Unit(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    __tablename__ = "units"
    __table_args__ = (
        interval_check("formed_on", "disbanded_on"),
        sa.CheckConstraint("polity_id IS NOT NULL OR is_multinational", name="polity_or_multinational"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    # NULL only for multinational headquarters (e.g. SHAEF), see is_multinational.
    polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="RESTRICT"), index=True)
    is_multinational: Mapped[bool] = mapped_column(sa.Boolean, default=False, server_default=sa.false(), nullable=False)
    force_id: Mapped[int | None] = mapped_column(sa.ForeignKey("armed_forces.id", ondelete="SET NULL"), index=True)
    echelon: Mapped[Echelon] = mapped_column(enum_col(Echelon), nullable=False)
    type_label: Mapped[str | None] = mapped_column(sa.Text)  # national designation: "Reserve-Division", "Infantry Division"...
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)  # canonical display name
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    nickname: Mapped[str | None] = mapped_column(sa.Text)
    formed_on: Mapped[date | None] = mapped_column(sa.Date)
    formed_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "formed_precision"), default=DatePrecision.day, nullable=False)
    disbanded_on: Mapped[date | None] = mapped_column(sa.Date)
    disbanded_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "disbanded_precision"), default=DatePrecision.day, nullable=False)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    description: Mapped[str | None] = mapped_column(sa.Text)

    polity = relationship("Polity", lazy="joined")


class UnitName(TimestampMixin, TemporalMixin, Base):
    """Names, translations and redesignations, each with its own validity."""

    __tablename__ = "unit_names"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(sa.ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    language: Mapped[str | None] = mapped_column(sa.String(10))
    kind: Mapped[str] = mapped_column(sa.String(30), default="official", nullable=False)  # official|translation|nickname|abbreviation
    notes: Mapped[str | None] = mapped_column(sa.Text)


class UnitSubordination(TimestampMixin, TemporalMixin, Base):
    """Unit → parent unit (or directly → armed force) during an interval."""

    __tablename__ = "unit_subordinations"
    __table_args__ = (
        interval_check(),
        sa.CheckConstraint(
            "(parent_unit_id IS NOT NULL) <> (parent_force_id IS NOT NULL)", name="exactly_one_parent"
        ),
        sa.CheckConstraint("parent_unit_id IS NULL OR parent_unit_id <> unit_id", name="not_self"),
        ExcludeConstraint(
            (sa.column("unit_id"), "="),
            (_DATERANGE, "&&"),
            name="ex_unit_subordinations_organic_overlap",
            using="gist",
            where=sa.text("relation = 'organic'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(sa.ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_unit_id: Mapped[int | None] = mapped_column(sa.ForeignKey("units.id", ondelete="CASCADE"), index=True)
    parent_force_id: Mapped[int | None] = mapped_column(sa.ForeignKey("armed_forces.id", ondelete="CASCADE"), index=True)
    relation: Mapped[SubordinationKind] = mapped_column(enum_col(SubordinationKind), default=SubordinationKind.organic, nullable=False)
    notes: Mapped[str | None] = mapped_column(sa.Text)


class BattleUnit(TimestampMixin, TemporalMixin, Base):
    __tablename__ = "battle_units"
    __table_args__ = (interval_check(), sa.UniqueConstraint("battle_id", "unit_id", name="uq_battle_units_battle_unit"))

    id: Mapped[int] = mapped_column(primary_key=True)
    battle_id: Mapped[int] = mapped_column(sa.ForeignKey("battles.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id: Mapped[int] = mapped_column(sa.ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    side: Mapped[Side] = mapped_column(enum_col(Side), nullable=False)
    role: Mapped[str | None] = mapped_column(sa.Text)
    notes: Mapped[str | None] = mapped_column(sa.Text)


class Person(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    __tablename__ = "persons"
    __table_args__ = (interval_check("birth_date", "death_date", "life_interval"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    birth_date: Mapped[date | None] = mapped_column(sa.Date)
    death_date: Mapped[date | None] = mapped_column(sa.Date)
    birth_place: Mapped[str | None] = mapped_column(sa.Text)
    death_place: Mapped[str | None] = mapped_column(sa.Text)
    nationality_polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="SET NULL"), index=True)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    biography: Mapped[str | None] = mapped_column(sa.Text)

    nationality = relationship("Polity", lazy="joined")


class PersonRank(TimestampMixin, TemporalMixin, Base):
    __tablename__ = "person_ranks"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    rank: Mapped[str] = mapped_column(sa.Text, nullable=False)
    rank_original: Mapped[str | None] = mapped_column(sa.Text)
    force_id: Mapped[int | None] = mapped_column(sa.ForeignKey("armed_forces.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(sa.Text)


class PersonPosition(TimestampMixin, TemporalMixin, Base):
    """A post held by a person (command of a unit, staff function, political office...)."""

    __tablename__ = "person_positions"
    __table_args__ = (
        interval_check(),
        ExcludeConstraint(
            (sa.column("unit_id"), "="),
            (_DATERANGE, "&&"),
            name="ex_person_positions_single_commander",
            using="gist",
            where=sa.text("kind = 'commander' AND unit_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id: Mapped[int | None] = mapped_column(sa.ForeignKey("units.id", ondelete="CASCADE"), index=True)
    force_id: Mapped[int | None] = mapped_column(sa.ForeignKey("armed_forces.id", ondelete="SET NULL"))
    polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="SET NULL"))
    kind: Mapped[PositionKind] = mapped_column(enum_col(PositionKind), default=PositionKind.commander, nullable=False)
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)  # e.g. "Commander-in-Chief, BEF"
    rank_at_time: Mapped[str | None] = mapped_column(sa.Text)
    notes: Mapped[str | None] = mapped_column(sa.Text)

    person = relationship("Person", lazy="joined")


class BattleCommander(TimestampMixin, Base):
    __tablename__ = "battle_commanders"
    __table_args__ = (sa.UniqueConstraint("battle_id", "person_id", name="uq_battle_commanders_battle_person"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    battle_id: Mapped[int] = mapped_column(sa.ForeignKey("battles.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id: Mapped[int] = mapped_column(sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    side: Mapped[Side] = mapped_column(enum_col(Side), nullable=False)
    role: Mapped[str | None] = mapped_column(sa.Text)
    notes: Mapped[str | None] = mapped_column(sa.Text)

    person = relationship("Person", lazy="joined")
