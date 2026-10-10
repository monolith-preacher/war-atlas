"""Controlled vocabularies.

Stored as VARCHAR + CHECK constraint (non-native enums) so that new values can be
added with a simple migration, without ALTER TYPE gymnastics.
"""

from enum import StrEnum


class PublicationStatus(StrEnum):
    draft = "draft"
    in_review = "in_review"
    published = "published"
    archived = "archived"


class Certainty(StrEnum):
    """Epistemic status of a record or of a geometry."""

    verified = "verified"  # stated by identifiable, reliable sources
    estimated = "estimated"  # numeric/positional estimate made by a source
    interpreted = "interpreted"  # historiographical interpretation
    reconstructed = "reconstructed"  # cartographic reconstruction / schematic
    disputed = "disputed"  # sources disagree, see figures/citations
    unverified = "unverified"  # imported or entered, not yet checked


class DatePrecision(StrEnum):
    day = "day"
    month = "month"
    year = "year"
    circa = "circa"
    # "attested": the record is known to be valid at this date, but the real
    # boundary of validity is not documented. Queries never extend validity
    # beyond an attested bound.
    attested = "attested"


class SpatialRole(StrEnum):
    """What a geometry means. A battle location is not an area of operations."""

    exact_location = "exact_location"
    approximate_position = "approximate_position"
    area_of_operations = "area_of_operations"
    route = "route"
    territorial_extent = "territorial_extent"
    schematic = "schematic"


class MapFeatureType(StrEnum):
    front_line = "front_line"
    advance_axis = "advance_axis"
    withdrawal_axis = "withdrawal_axis"
    defensive_line = "defensive_line"
    objective = "objective"
    unit_position = "unit_position"
    fortification = "fortification"
    airfield = "airfield"
    naval_base = "naval_base"
    landing_zone = "landing_zone"
    drop_zone = "drop_zone"
    area_of_operations = "area_of_operations"
    territorial_control = "territorial_control"
    route = "route"


class BranchKind(StrEnum):
    army = "army"
    navy = "navy"
    air_force = "air_force"
    marines = "marines"
    combined = "combined"
    paramilitary = "paramilitary"
    other = "other"


class Echelon(StrEnum):
    """Generic echelon used for ordering. The national designation lives in Unit.type_label."""

    supreme_command = "supreme_command"
    theater_command = "theater_command"
    army_group = "army_group"
    field_force = "field_force"
    army = "army"
    corps = "corps"
    division = "division"
    brigade = "brigade"
    regiment = "regiment"
    battalion = "battalion"
    company = "company"
    platoon = "platoon"
    fleet = "fleet"
    squadron = "squadron"
    flotilla = "flotilla"
    air_command = "air_command"
    wing = "wing"
    group = "group"
    other = "other"


ECHELON_ORDER = {e.value: i for i, e in enumerate(Echelon)}


class CampaignKind(StrEnum):
    campaign = "campaign"
    operation = "operation"
    offensive = "offensive"


class BattleKind(StrEnum):
    battle = "battle"
    landing = "landing"
    siege = "siege"
    engagement = "engagement"
    airborne_operation = "airborne_operation"
    naval_battle = "naval_battle"
    liberation = "liberation"


class EquipmentCategory(StrEnum):
    small_arm = "small_arm"
    machine_gun = "machine_gun"
    artillery = "artillery"
    tank = "tank"
    armored_vehicle = "armored_vehicle"
    transport_vehicle = "transport_vehicle"
    aircraft = "aircraft"
    ship = "ship"
    submarine = "submarine"
    landing_craft = "landing_craft"
    communications = "communications"
    personal_equipment = "personal_equipment"
    other = "other"


class SourceKind(StrEnum):
    book = "book"
    official_history = "official_history"
    article = "article"
    archive = "archive"
    website = "website"
    dataset = "dataset"
    encyclopedia = "encyclopedia"
    map = "map"
    other = "other"


class FigureMetric(StrEnum):
    strength = "strength"
    casualties = "casualties"
    killed = "killed"
    wounded = "wounded"
    missing = "missing"
    captured = "captured"
    tanks_lost = "tanks_lost"
    aircraft_lost = "aircraft_lost"
    civilian_deaths = "civilian_deaths"
    other = "other"


class Side(StrEnum):
    a = "a"
    b = "b"
    other = "other"


class PositionKind(StrEnum):
    commander = "commander"
    acting_commander = "acting_commander"
    chief_of_staff = "chief_of_staff"
    deputy = "deputy"
    staff = "staff"
    political = "political"
    other = "other"


class SubordinationKind(StrEnum):
    organic = "organic"
    attached = "attached"
    operational_control = "operational_control"
    administrative = "administrative"


class UserRole(StrEnum):
    admin = "admin"
    reviewer = "reviewer"
    editor = "editor"


class ImportStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class MediaKind(StrEnum):
    photo = "photo"
    illustration = "illustration"
    map = "map"
    document = "document"
    insignia = "insignia"
    scheme = "scheme"
    other = "other"
