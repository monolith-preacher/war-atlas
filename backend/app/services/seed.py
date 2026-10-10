"""Loader for the curated JSON seed files (backend/seed/*.json).

Records reference each other by slug (e.g. ``"polity": "imperio-alemao"``); the loader
resolves those to foreign keys. Inline ``cite`` and ``figures`` arrays become rows in
the polymorphic ``citations`` and ``figures`` tables.

The loader is intentionally strict: an unknown key or an unresolvable reference aborts
the whole load (single transaction), so a typo can never produce a silently wrong link.
"""

from __future__ import annotations

import json
import logging
import pathlib
from datetime import date
from typing import Any

from geoalchemy2.shape import from_shape
from shapely.geometry import MultiPolygon, Point, shape
from shapely.validation import make_valid
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import models as m
from app.models.enums import Certainty, PublicationStatus
from app.models.registry import MODEL_ENTITY_TYPES

log = logging.getLogger(__name__)

SEED_DIR = pathlib.Path(__file__).resolve().parents[2] / "seed"
DEFAULT_DATA_DIR = pathlib.Path(__file__).resolve().parents[3] / "data"


class SeedError(RuntimeError):
    pass


# section -> (model, natural key or None, {ref_key: (column, model)})
SECTIONS: list[tuple[str, type, str | None, dict[str, tuple[str, type]]]] = [
    ("sources", m.Source, "slug", {}),
    ("polities", m.Polity, "slug", {}),
    ("polity_periods", m.PolityPeriod, None, {"polity": ("polity_id", m.Polity)}),
    ("armed_forces", m.ArmedForce, "slug", {"polity": ("polity_id", m.Polity), "parent": ("parent_id", m.ArmedForce)}),
    ("conflicts", m.Conflict, "slug", {"parent": ("parent_id", m.Conflict)}),
    ("alliances", m.Alliance, "slug", {"conflict": ("conflict_id", m.Conflict)}),
    ("alliance_memberships", m.AllianceMembership, None, {"alliance": ("alliance_id", m.Alliance), "polity": ("polity_id", m.Polity)}),
    ("conflict_participations", m.ConflictParticipation, None, {"conflict": ("conflict_id", m.Conflict), "polity": ("polity_id", m.Polity), "alliance": ("alliance_id", m.Alliance)}),
    ("theaters", m.Theater, "slug", {"conflict": ("conflict_id", m.Conflict), "parent": ("parent_id", m.Theater)}),
    ("campaigns", m.Campaign, "slug", {"conflict": ("conflict_id", m.Conflict), "theater": ("theater_id", m.Theater), "parent": ("parent_id", m.Campaign)}),
    ("places", m.Place, "slug", {}),
    ("battles", m.Battle, "slug", {"conflict": ("conflict_id", m.Conflict), "theater": ("theater_id", m.Theater), "campaign": ("campaign_id", m.Campaign), "parent": ("parent_id", m.Battle), "place": ("place_id", m.Place)}),
    ("battle_participants", m.BattleParticipant, None, {"battle": ("battle_id", m.Battle), "polity": ("polity_id", m.Polity)}),
    ("persons", m.Person, "slug", {"nationality": ("nationality_polity_id", m.Polity)}),
    ("units", m.Unit, "slug", {"polity": ("polity_id", m.Polity), "force": ("force_id", m.ArmedForce)}),
    ("unit_subordinations", m.UnitSubordination, None, {"unit": ("unit_id", m.Unit), "parent_unit": ("parent_unit_id", m.Unit), "parent_force": ("parent_force_id", m.ArmedForce)}),
    ("person_positions", m.PersonPosition, None, {"person": ("person_id", m.Person), "unit": ("unit_id", m.Unit), "force": ("force_id", m.ArmedForce), "polity": ("polity_id", m.Polity)}),
    ("battle_units", m.BattleUnit, None, {"battle": ("battle_id", m.Battle), "unit": ("unit_id", m.Unit)}),
    ("battle_commanders", m.BattleCommander, None, {"battle": ("battle_id", m.Battle), "person": ("person_id", m.Person)}),
    ("events", m.Event, "slug", {"conflict": ("conflict_id", m.Conflict), "theater": ("theater_id", m.Theater), "campaign": ("campaign_id", m.Campaign), "battle": ("battle_id", m.Battle), "place": ("place_id", m.Place)}),
    ("event_units", m.EventUnit, None, {"event": ("event_id", m.Event), "unit": ("unit_id", m.Unit)}),
    ("event_persons", m.EventPerson, None, {"event": ("event_id", m.Event), "person": ("person_id", m.Person)}),
    ("map_features", m.MapFeature, "slug", {"conflict": ("conflict_id", m.Conflict), "campaign": ("campaign_id", m.Campaign), "battle": ("battle_id", m.Battle), "event": ("event_id", m.Event), "unit": ("unit_id", m.Unit), "polity": ("polity_id", m.Polity)}),
    ("equipment", m.Equipment, "slug", {"origin_polity": ("origin_polity_id", m.Polity)}),
    ("equipment_users", m.EquipmentUser, None, {"equipment": ("equipment_id", m.Equipment), "polity": ("polity_id", m.Polity), "force": ("force_id", m.ArmedForce)}),
    ("unit_equipment", m.UnitEquipment, None, {"unit": ("unit_id", m.Unit), "equipment": ("equipment_id", m.Equipment)}),
    ("camouflage_patterns", m.CamouflagePattern, "slug", {"polity": ("polity_id", m.Polity), "force": ("force_id", m.ArmedForce)}),
    ("uniforms", m.Uniform, "slug", {"polity": ("polity_id", m.Polity), "force": ("force_id", m.ArmedForce), "unit": ("unit_id", m.Unit), "camouflage": ("camouflage_id", m.CamouflagePattern)}),
]

# Inline geometry helpers: key -> (column, kind)
GEOMETRY_KEYS = {
    "point": ("geom", "point"),
    "location": ("location", "point"),
    "geom": ("geom", "geojson"),
    "area": ("area", "geojson"),
}

DATE_SUFFIXES = ("_date", "_on", "valid_from", "valid_to", "service_from", "service_to")


def _is_date_field(key: str) -> bool:
    return key.endswith(DATE_SUFFIXES) and not key.endswith("_precision")


def _geometry(value: Any, kind: str):
    if kind == "point":
        lon, lat = value
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise SeedError(f"invalid coordinate {value}")
        return from_shape(Point(lon, lat), srid=4326)
    geom = shape(value)
    if not geom.is_valid:
        geom = make_valid(geom)
    return from_shape(geom, srid=4326)


class SeedLoader:
    def __init__(self, db: Session, data_dir: pathlib.Path | None = None):
        self.db = db
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.cache: dict[tuple[type, str], int] = {}
        self.stats: dict[str, int] = {}

    # -- reference resolution -------------------------------------------------
    def ref(self, model: type, slug: str) -> int:
        key = (model, slug)
        if key not in self.cache:
            row_id = self.db.scalar(select(model.id).where(model.slug == slug))
            if row_id is None:
                raise SeedError(f"unresolved reference {model.__name__}:{slug}")
            self.cache[key] = row_id
        return self.cache[key]

    # -- loading --------------------------------------------------------------
    def load_files(self, files: list[pathlib.Path]) -> dict[str, int]:
        bundles = [json.loads(f.read_text(encoding="utf-8")) for f in files]
        for section, model, natural_key, refs in SECTIONS:
            for bundle in bundles:
                for record in bundle.get(section, []):
                    self._load_record(section, model, natural_key, refs, record)
        for bundle in bundles:
            for ds in bundle.get("boundary_datasets", []):
                self._load_boundary_dataset(ds)
        self.db.flush()
        return self.stats

    def _load_record(self, section, model, natural_key, refs, record: dict) -> None:
        record = dict(record)
        cites = record.pop("cite", [])
        figures = record.pop("figures", [])
        names = record.pop("names", [])
        values: dict[str, Any] = {}
        columns = set(model.__table__.columns.keys())

        for key, value in record.items():
            if key in refs:
                col, ref_model = refs[key]
                values[col] = self.ref(ref_model, value) if value is not None else None
            elif key in GEOMETRY_KEYS:
                col, kind = GEOMETRY_KEYS[key]
                if col not in columns:
                    raise SeedError(f"{section}: geometry key '{key}' not supported")
                values[col] = _geometry(value, kind)
            elif key in columns:
                values[key] = date.fromisoformat(value) if (_is_date_field(key) and isinstance(value, str)) else value
            else:
                raise SeedError(f"{section}: unknown key '{key}' in {record.get('slug', record)}")

        if "status" in columns and "status" not in values:
            values["status"] = PublicationStatus.published
        if "certainty" in columns and "certainty" not in values and model is not m.Figure:
            values["certainty"] = Certainty.verified if cites else Certainty.unverified

        obj = model(**values)
        self.db.add(obj)
        self.db.flush()
        if natural_key:
            self.cache[(model, values[natural_key])] = obj.id
        self.stats[section] = self.stats.get(section, 0) + 1

        entity_type = MODEL_ENTITY_TYPES[model]
        for c in cites:
            self.db.add(m.Citation(source_id=self.ref(m.Source, c["source"]), entity_type=entity_type, entity_id=obj.id,
                                   field=c.get("field"), pages=c.get("pages"), quote=c.get("quote"), note=c.get("note")))
            self.stats["citations"] = self.stats.get("citations", 0) + 1
        for f in figures:
            self._load_figure(entity_type, obj.id, f)
        for n in names:
            n = dict(n)
            for k in ("valid_from", "valid_to"):
                if isinstance(n.get(k), str):
                    n[k] = date.fromisoformat(n[k])
            self.db.add(m.UnitName(unit_id=obj.id, **n))
            self.stats["unit_names"] = self.stats.get("unit_names", 0) + 1

    def _load_figure(self, entity_type: str, entity_id: int, f: dict) -> None:
        f = dict(f)
        fig = m.Figure(
            entity_type=entity_type,
            entity_id=entity_id,
            metric=f.pop("metric"),
            side=f.pop("side", None),
            polity_id=self.ref(m.Polity, f.pop("polity")) if f.get("polity") else None,
            value_low=f.pop("value_low", None),
            value_high=f.pop("value_high", None),
            value_text=f.pop("value_text", None),
            scope_note=f.pop("scope_note", None),
            as_of_date=date.fromisoformat(f.pop("as_of_date")) if f.get("as_of_date") else None,
            source_id=self.ref(m.Source, f.pop("source")) if f.get("source") else None,
            pages=f.pop("pages", None),
            certainty=f.pop("certainty", Certainty.estimated),
            notes=f.pop("notes", None),
        )
        f.pop("polity", None)
        f.pop("as_of_date", None)
        f.pop("source", None)
        if f:
            raise SeedError(f"figure: unknown keys {sorted(f)}")
        self.db.add(fig)
        self.stats["figures"] = self.stats.get("figures", 0) + 1

    def _load_boundary_dataset(self, ds: dict) -> None:
        path = self.data_dir / ds["file"]
        if not path.exists():
            raise SeedError(f"boundary file not found: {path} (run scripts/prepare_geodata.py)")
        dataset = m.BoundaryDataset(
            slug=ds["slug"], name=ds["name"], reference_date=date.fromisoformat(ds["reference_date"]),
            valid_from=date.fromisoformat(ds["valid_from"]) if ds.get("valid_from") else None,
            valid_to=date.fromisoformat(ds["valid_to"]) if ds.get("valid_to") else None,
            source_id=self.ref(m.Source, ds["source"]) if ds.get("source") else None,
            license=ds.get("license"), precision_note=ds.get("precision_note"), known_issues=ds.get("known_issues"),
        )
        self.db.add(dataset)
        self.db.flush()
        polity_map = {label: self.ref(m.Polity, slug) for label, slug in ds.get("polity_map", {}).items()}
        fc = json.loads(path.read_text(encoding="utf-8"))
        count = 0
        for feat in fc["features"]:
            props = feat.get("properties") or {}
            geom = make_valid(shape(feat["geometry"]))
            polys = [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "Polygon"]
            if geom.geom_type == "Polygon":
                polys = [geom]
            if not polys:
                continue
            label = props.get("NAME") or "?"
            subject = props.get("SUBJECTO")
            extra = {"part_of": props.get("PARTOF")}
            if subject and subject in polity_map and label not in polity_map:
                extra["subject_polity_id"] = polity_map[subject]
            self.db.add(m.HistoricalBoundary(
                dataset_id=dataset.id, polity_id=polity_map.get(label), label=label, subject_label=subject,
                border_precision=props.get("BORDERPRECISION"), geom=from_shape(MultiPolygon(polys), srid=4326), properties=extra,
            ))
            count += 1
        self.stats["historical_boundaries"] = self.stats.get("historical_boundaries", 0) + count


CONTENT_TABLES = [t for t in reversed(m.Base.metadata.sorted_tables) if t.name not in {"users", "revisions"}]


def is_seeded(db: Session) -> bool:
    return db.scalar(select(m.Conflict.id).limit(1)) is not None


def reset_content(db: Session) -> None:
    """Delete every content row (keeps users and the revision log)."""
    names = ", ".join(t.name for t in CONTENT_TABLES)
    db.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


def run_seed(db: Session, *, reset: bool = False, data_dir: pathlib.Path | None = None) -> dict[str, int] | None:
    if reset:
        reset_content(db)
    elif is_seeded(db):
        log.info("database already contains content; skipping seed (use --reset to reload)")
        return None
    files = sorted(SEED_DIR.glob("*.json"))
    stats = SeedLoader(db, data_dir).load_files(files)
    db.commit()
    return stats
