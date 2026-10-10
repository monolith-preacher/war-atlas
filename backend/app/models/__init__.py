"""ORM models. Importing this package registers every table on Base.metadata."""

from app.models.admin import ImportBatch, ImportRecord, Revision, User
from app.models.base import Base
from app.models.history import (
    Alliance,
    AllianceMembership,
    Battle,
    BattleParticipant,
    BoundaryDataset,
    Campaign,
    Conflict,
    ConflictParticipation,
    Event,
    EventPerson,
    EventUnit,
    HistoricalBoundary,
    MapFeature,
    Place,
    Polity,
    PolityPeriod,
    Theater,
)
from app.models.materiel import (
    CamouflagePattern,
    Equipment,
    EquipmentCamouflage,
    EquipmentUser,
    EquipmentVariant,
    Insignia,
    Uniform,
    UnitEquipment,
)
from app.models.military import (
    ArmedForce,
    BattleCommander,
    BattleUnit,
    Person,
    PersonPosition,
    PersonRank,
    Unit,
    UnitName,
    UnitSubordination,
)
from app.models.sources import Citation, Figure, Media, MediaLink, Source

__all__ = [
    "Alliance", "AllianceMembership", "ArmedForce", "Base", "Battle", "BattleCommander",
    "BattleParticipant", "BattleUnit", "BoundaryDataset", "CamouflagePattern", "Campaign",
    "Citation", "Conflict", "ConflictParticipation", "Equipment", "EquipmentCamouflage",
    "EquipmentUser", "EquipmentVariant", "Event", "EventPerson", "EventUnit", "Figure",
    "HistoricalBoundary", "ImportBatch", "ImportRecord", "Insignia", "MapFeature", "Media",
    "MediaLink", "Person", "PersonPosition", "PersonRank", "Place", "Polity", "PolityPeriod",
    "Revision", "Source", "Theater", "Uniform", "Unit", "UnitEquipment", "UnitName",
    "UnitSubordination", "User",
]
