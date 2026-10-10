"""Conflicts, political entities, alliances, theaters, campaigns, battles and events."""

from datetime import date

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
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
from app.models.enums import (
    BattleKind,
    CampaignKind,
    Certainty,
    DatePrecision,
    MapFeatureType,
    Side,
    SpatialRole,
)


class Conflict(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    __tablename__ = "conflicts"
    __table_args__ = (interval_check("start_date", "end_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    short_name: Mapped[str | None] = mapped_column(sa.String(40))
    parent_id: Mapped[int | None] = mapped_column(sa.ForeignKey("conflicts.id", ondelete="SET NULL"))
    start_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    end_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    description: Mapped[str | None] = mapped_column(sa.Text)
    color: Mapped[str | None] = mapped_column(sa.String(9))
    default_center_lon: Mapped[float | None] = mapped_column(sa.Float)
    default_center_lat: Mapped[float | None] = mapped_column(sa.Float)
    default_zoom: Mapped[float | None] = mapped_column(sa.Float)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)


class Polity(TimestampMixin, PublicationMixin, ProvenanceMixin, TemporalMixin, Base):
    """A historical political entity (empire, republic, dominion...).

    ``valid_from``/``valid_to`` express the existence of the entity itself.
    """

    __tablename__ = "polities"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    short_name: Mapped[str | None] = mapped_column(sa.String(80))
    kind: Mapped[str | None] = mapped_column(sa.String(60))  # empire, kingdom, republic, dominion...
    color: Mapped[str | None] = mapped_column(sa.String(9))
    summary: Mapped[str | None] = mapped_column(sa.Text)
    description: Mapped[str | None] = mapped_column(sa.Text)


class PolityPeriod(TimestampMixin, TemporalMixin, Base):
    """Government/regime information valid during an interval."""

    __tablename__ = "polity_periods"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    polity_id: Mapped[int] = mapped_column(sa.ForeignKey("polities.id", ondelete="CASCADE"), nullable=False, index=True)
    government_type: Mapped[str | None] = mapped_column(sa.Text)
    head_of_state: Mapped[str | None] = mapped_column(sa.Text)
    head_of_government: Mapped[str | None] = mapped_column(sa.Text)
    capital_name: Mapped[str | None] = mapped_column(sa.Text)
    notes: Mapped[str | None] = mapped_column(sa.Text)


class BoundaryDataset(TimestampMixin, Base):
    """A snapshot of borders (e.g. "world in 1914") with explicit applicability window."""

    __tablename__ = "boundary_datasets"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    reference_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    valid_from: Mapped[date | None] = mapped_column(sa.Date)
    valid_to: Mapped[date | None] = mapped_column(sa.Date)
    source_id: Mapped[int | None] = mapped_column(sa.ForeignKey("sources.id", ondelete="SET NULL"))
    license: Mapped[str | None] = mapped_column(sa.Text)
    precision_note: Mapped[str | None] = mapped_column(sa.Text)
    known_issues: Mapped[str | None] = mapped_column(sa.Text)
    certainty: Mapped[Certainty] = mapped_column(enum_col(Certainty), default=Certainty.reconstructed, nullable=False)


class HistoricalBoundary(Base):
    __tablename__ = "historical_boundaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(sa.ForeignKey("boundary_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="SET NULL"), index=True)
    label: Mapped[str] = mapped_column(sa.Text, nullable=False)  # name as given by the dataset
    subject_label: Mapped[str | None] = mapped_column(sa.Text)  # sovereign as given by the dataset
    border_precision: Mapped[int | None] = mapped_column(sa.SmallInteger)
    geom = mapped_column(Geometry("MULTIPOLYGON", srid=4326, spatial_index=True), nullable=False)
    properties: Mapped[dict | None] = mapped_column(JSONB)


class Alliance(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    __tablename__ = "alliances"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    conflict_id: Mapped[int | None] = mapped_column(sa.ForeignKey("conflicts.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    side: Mapped[Side | None] = mapped_column(enum_col(Side))
    color: Mapped[str | None] = mapped_column(sa.String(9))
    summary: Mapped[str | None] = mapped_column(sa.Text)


class AllianceMembership(TimestampMixin, TemporalMixin, Base):
    __tablename__ = "alliance_memberships"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    alliance_id: Mapped[int] = mapped_column(sa.ForeignKey("alliances.id", ondelete="CASCADE"), nullable=False, index=True)
    polity_id: Mapped[int] = mapped_column(sa.ForeignKey("polities.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(sa.String(60))  # member, co-belligerent, associated power...
    notes: Mapped[str | None] = mapped_column(sa.Text)


class ConflictParticipation(TimestampMixin, TemporalMixin, Base):
    """A polity's participation in a conflict (valid_from = entry, valid_to = exit)."""

    __tablename__ = "conflict_participations"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    conflict_id: Mapped[int] = mapped_column(sa.ForeignKey("conflicts.id", ondelete="CASCADE"), nullable=False, index=True)
    polity_id: Mapped[int] = mapped_column(sa.ForeignKey("polities.id", ondelete="CASCADE"), nullable=False, index=True)
    alliance_id: Mapped[int | None] = mapped_column(sa.ForeignKey("alliances.id", ondelete="SET NULL"))
    role: Mapped[str | None] = mapped_column(sa.String(60))  # belligerent, co-belligerent...
    entry_note: Mapped[str | None] = mapped_column(sa.Text)
    exit_note: Mapped[str | None] = mapped_column(sa.Text)
    summary: Mapped[str | None] = mapped_column(sa.Text)

    polity = relationship("Polity", lazy="joined")
    alliance = relationship("Alliance", lazy="joined")


class Theater(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    __tablename__ = "theaters"
    __table_args__ = (interval_check("start_date", "end_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    conflict_id: Mapped[int] = mapped_column(sa.ForeignKey("conflicts.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(sa.ForeignKey("theaters.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    start_date: Mapped[date | None] = mapped_column(sa.Date)
    end_date: Mapped[date | None] = mapped_column(sa.Date)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    description: Mapped[str | None] = mapped_column(sa.Text)
    center_lon: Mapped[float | None] = mapped_column(sa.Float)
    center_lat: Mapped[float | None] = mapped_column(sa.Float)
    zoom: Mapped[float | None] = mapped_column(sa.Float)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)


class Campaign(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    """Campaigns, operations and offensives (nestable through parent_id)."""

    __tablename__ = "campaigns"
    __table_args__ = (interval_check("start_date", "end_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    conflict_id: Mapped[int] = mapped_column(sa.ForeignKey("conflicts.id", ondelete="CASCADE"), nullable=False, index=True)
    theater_id: Mapped[int | None] = mapped_column(sa.ForeignKey("theaters.id", ondelete="SET NULL"), index=True)
    parent_id: Mapped[int | None] = mapped_column(sa.ForeignKey("campaigns.id", ondelete="SET NULL"), index=True)
    kind: Mapped[CampaignKind] = mapped_column(enum_col(CampaignKind), default=CampaignKind.campaign, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    codename: Mapped[str | None] = mapped_column(sa.String(120))
    start_date: Mapped[date | None] = mapped_column(sa.Date)
    start_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "start_precision"), default=DatePrecision.day, nullable=False)
    end_date: Mapped[date | None] = mapped_column(sa.Date)
    end_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "end_precision"), default=DatePrecision.day, nullable=False)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    description: Mapped[str | None] = mapped_column(sa.Text)
    objectives: Mapped[str | None] = mapped_column(sa.Text)
    outcome: Mapped[str | None] = mapped_column(sa.Text)
    area = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=True))
    center_lon: Mapped[float | None] = mapped_column(sa.Float)
    center_lat: Mapped[float | None] = mapped_column(sa.Float)
    zoom: Mapped[float | None] = mapped_column(sa.Float)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)


class Place(TimestampMixin, ProvenanceMixin, Base):
    """A locality. Its point is a *location*, distinct from areas of operations."""

    __tablename__ = "places"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    historical_names: Mapped[str | None] = mapped_column(sa.Text)
    modern_country: Mapped[str | None] = mapped_column(sa.String(80))
    kind: Mapped[str | None] = mapped_column(sa.String(60))
    geom = mapped_column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False)
    spatial_role: Mapped[SpatialRole] = mapped_column(enum_col(SpatialRole), default=SpatialRole.exact_location, nullable=False)
    precision_m: Mapped[int | None] = mapped_column(sa.Integer)
    notes: Mapped[str | None] = mapped_column(sa.Text)


class Battle(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    __tablename__ = "battles"
    __table_args__ = (interval_check("start_date", "end_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    conflict_id: Mapped[int] = mapped_column(sa.ForeignKey("conflicts.id", ondelete="CASCADE"), nullable=False, index=True)
    theater_id: Mapped[int | None] = mapped_column(sa.ForeignKey("theaters.id", ondelete="SET NULL"), index=True)
    campaign_id: Mapped[int | None] = mapped_column(sa.ForeignKey("campaigns.id", ondelete="SET NULL"), index=True)
    parent_id: Mapped[int | None] = mapped_column(sa.ForeignKey("battles.id", ondelete="SET NULL"), index=True)
    kind: Mapped[BattleKind] = mapped_column(enum_col(BattleKind), default=BattleKind.battle, nullable=False)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    name_original: Mapped[str | None] = mapped_column(sa.Text)
    start_date: Mapped[date | None] = mapped_column(sa.Date)
    start_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "start_precision"), default=DatePrecision.day, nullable=False)
    end_date: Mapped[date | None] = mapped_column(sa.Date)
    end_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "end_precision"), default=DatePrecision.day, nullable=False)
    place_id: Mapped[int | None] = mapped_column(sa.ForeignKey("places.id", ondelete="SET NULL"))
    location = mapped_column(Geometry("POINT", srid=4326, spatial_index=True))
    location_role: Mapped[SpatialRole] = mapped_column(enum_col(SpatialRole, "location_role"), default=SpatialRole.approximate_position, nullable=False)
    location_precision_m: Mapped[int | None] = mapped_column(sa.Integer)
    area = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=True))
    summary: Mapped[str | None] = mapped_column(sa.Text)
    context: Mapped[str | None] = mapped_column(sa.Text)
    objectives: Mapped[str | None] = mapped_column(sa.Text)
    strategy: Mapped[str | None] = mapped_column(sa.Text)
    result: Mapped[str | None] = mapped_column(sa.Text)
    consequences: Mapped[str | None] = mapped_column(sa.Text)
    zoom: Mapped[float | None] = mapped_column(sa.Float)

    place = relationship("Place", lazy="joined")


class BattleParticipant(TimestampMixin, Base):
    __tablename__ = "battle_participants"
    __table_args__ = (sa.UniqueConstraint("battle_id", "polity_id", name="uq_battle_participants_battle_polity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    battle_id: Mapped[int] = mapped_column(sa.ForeignKey("battles.id", ondelete="CASCADE"), nullable=False, index=True)
    polity_id: Mapped[int] = mapped_column(sa.ForeignKey("polities.id", ondelete="CASCADE"), nullable=False, index=True)
    side: Mapped[Side] = mapped_column(enum_col(Side), nullable=False)
    role: Mapped[str | None] = mapped_column(sa.String(80))
    notes: Mapped[str | None] = mapped_column(sa.Text)

    polity = relationship("Polity", lazy="joined")


class Event(TimestampMixin, PublicationMixin, ProvenanceMixin, Base):
    """A dated, documented happening. The backbone of timelines and campaign replay."""

    __tablename__ = "events"
    __table_args__ = (interval_check("start_date", "end_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    conflict_id: Mapped[int] = mapped_column(sa.ForeignKey("conflicts.id", ondelete="CASCADE"), nullable=False, index=True)
    theater_id: Mapped[int | None] = mapped_column(sa.ForeignKey("theaters.id", ondelete="SET NULL"))
    campaign_id: Mapped[int | None] = mapped_column(sa.ForeignKey("campaigns.id", ondelete="SET NULL"), index=True)
    battle_id: Mapped[int | None] = mapped_column(sa.ForeignKey("battles.id", ondelete="SET NULL"), index=True)
    kind: Mapped[str] = mapped_column(sa.String(60), nullable=False)  # attack, landing, capture, command_change...
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    start_date: Mapped[date] = mapped_column(sa.Date, nullable=False, index=True)
    end_date: Mapped[date | None] = mapped_column(sa.Date)
    date_precision: Mapped[DatePrecision] = mapped_column(enum_col(DatePrecision, "date_precision"), default=DatePrecision.day, nullable=False)
    time_of_day: Mapped[str | None] = mapped_column(sa.String(120))  # e.g. "07:30" when documented
    place_id: Mapped[int | None] = mapped_column(sa.ForeignKey("places.id", ondelete="SET NULL"))
    geom = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=True))
    spatial_role: Mapped[SpatialRole] = mapped_column(enum_col(SpatialRole), default=SpatialRole.approximate_position, nullable=False)
    precision_m: Mapped[int | None] = mapped_column(sa.Integer)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    description: Mapped[str | None] = mapped_column(sa.Text)
    importance: Mapped[int] = mapped_column(sa.SmallInteger, default=3, nullable=False)

    place = relationship("Place", lazy="joined")


class EventUnit(Base):
    __tablename__ = "event_units"
    __table_args__ = (sa.UniqueConstraint("event_id", "unit_id", name="uq_event_units_event_unit"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id: Mapped[int] = mapped_column(sa.ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(sa.String(80))


class EventPerson(Base):
    __tablename__ = "event_persons"
    __table_args__ = (sa.UniqueConstraint("event_id", "person_id", name="uq_event_persons_event_person"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id: Mapped[int] = mapped_column(sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(sa.String(80))


class MapFeature(TimestampMixin, PublicationMixin, TemporalMixin, Base):
    """Military cartography: front lines, axes of advance, positions, fortifications...

    Every feature declares what its geometry *means* (spatial_role) and how certain it is.
    Schematic/reconstructed features are rendered differently and explained to the user.
    Features are never interpolated between dates by the application.
    """

    __tablename__ = "map_features"
    __table_args__ = (interval_check(),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(160), unique=True, nullable=False)
    conflict_id: Mapped[int] = mapped_column(sa.ForeignKey("conflicts.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id: Mapped[int | None] = mapped_column(sa.ForeignKey("campaigns.id", ondelete="SET NULL"), index=True)
    battle_id: Mapped[int | None] = mapped_column(sa.ForeignKey("battles.id", ondelete="SET NULL"), index=True)
    event_id: Mapped[int | None] = mapped_column(sa.ForeignKey("events.id", ondelete="SET NULL"))
    unit_id: Mapped[int | None] = mapped_column(sa.ForeignKey("units.id", ondelete="SET NULL"), index=True)
    polity_id: Mapped[int | None] = mapped_column(sa.ForeignKey("polities.id", ondelete="SET NULL"))
    side: Mapped[Side | None] = mapped_column(enum_col(Side))
    feature_type: Mapped[MapFeatureType] = mapped_column(enum_col(MapFeatureType), nullable=False, index=True)
    label: Mapped[str] = mapped_column(sa.Text, nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text)
    geom = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=True), nullable=False)
    spatial_role: Mapped[SpatialRole] = mapped_column(enum_col(SpatialRole), nullable=False)
    certainty: Mapped[Certainty] = mapped_column(enum_col(Certainty), default=Certainty.unverified, nullable=False)
    precision_m: Mapped[int | None] = mapped_column(sa.Integer)
    method_note: Mapped[str | None] = mapped_column(sa.Text)  # how the geometry was produced
    style: Mapped[dict | None] = mapped_column(JSONB)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
