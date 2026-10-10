"""Entity-type registry used by polymorphic tables (citations, media links, figures),
search results and the generic admin CRUD."""

from app import models as m

# Entities that can be cited / illustrated / referenced by type name.
ENTITY_MODELS: dict[str, type] = {
    "conflict": m.Conflict,
    "polity": m.Polity,
    "polity_period": m.PolityPeriod,
    "alliance": m.Alliance,
    "alliance_membership": m.AllianceMembership,
    "conflict_participation": m.ConflictParticipation,
    "theater": m.Theater,
    "campaign": m.Campaign,
    "battle": m.Battle,
    "battle_participant": m.BattleParticipant,
    "battle_unit": m.BattleUnit,
    "battle_commander": m.BattleCommander,
    "event": m.Event,
    "event_unit": m.EventUnit,
    "event_person": m.EventPerson,
    "place": m.Place,
    "map_feature": m.MapFeature,
    "armed_force": m.ArmedForce,
    "unit": m.Unit,
    "unit_name": m.UnitName,
    "unit_subordination": m.UnitSubordination,
    "person": m.Person,
    "person_rank": m.PersonRank,
    "person_position": m.PersonPosition,
    "equipment": m.Equipment,
    "equipment_variant": m.EquipmentVariant,
    "equipment_user": m.EquipmentUser,
    "unit_equipment": m.UnitEquipment,
    "camouflage_pattern": m.CamouflagePattern,
    "equipment_camouflage": m.EquipmentCamouflage,
    "uniform": m.Uniform,
    "insignia": m.Insignia,
    "source": m.Source,
    "citation": m.Citation,
    "figure": m.Figure,
    "media": m.Media,
    "media_link": m.MediaLink,
}

MODEL_ENTITY_TYPES: dict[type, str] = {v: k for k, v in ENTITY_MODELS.items()}
