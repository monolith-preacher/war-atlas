"""Shared serialization helpers for API responses.

Responses are plain dicts built here (rather than ORM objects) so that every endpoint
exposes the same shapes for temporal bounds, provenance, citations and geometry.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models as m
from app.models.enums import PublicationStatus


def geojson(geom) -> dict | None:
    if geom is None:
        return None
    return mapping(to_shape(geom))


def point_lonlat(geom) -> list[float] | None:
    if geom is None:
        return None
    shp = to_shape(geom)
    p = shp if shp.geom_type == "Point" else shp.representative_point()
    return [round(p.x, 6), round(p.y, 6)]


def temporal(obj, start: str = "valid_from", end: str = "valid_to") -> dict[str, Any]:
    sp = getattr(obj, f"{start}_precision", None)
    ep = getattr(obj, f"{end}_precision", None)
    return {
        "valid_from": getattr(obj, start),
        "valid_from_precision": sp.value if sp is not None else None,
        "valid_to": getattr(obj, end),
        "valid_to_precision": ep.value if ep is not None else None,
    }


def provenance(obj) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if hasattr(obj, "certainty"):
        out["certainty"] = obj.certainty.value
    if hasattr(obj, "provenance_note"):
        out["provenance_note"] = obj.provenance_note
    if hasattr(obj, "wikidata_id"):
        out["wikidata_id"] = obj.wikidata_id
    return out


def ref(obj, entity_type: str, **extra) -> dict[str, Any] | None:
    """Compact reference to another entity, used for navigation links."""
    if obj is None:
        return None
    name = getattr(obj, "name", None) or getattr(obj, "title", None)
    out = {"type": entity_type, "id": obj.id, "slug": getattr(obj, "slug", None), "name": name}
    out.update(extra)
    return out


def source_dict(s: m.Source) -> dict[str, Any]:
    return {
        "id": s.id, "slug": s.slug, "kind": s.kind.value, "title": s.title, "authors": s.authors, "year": s.year,
        "publisher": s.publisher, "place": s.place, "series": s.series, "isbn": s.isbn, "url": s.url,
        "license": s.license, "accessed_on": s.accessed_on, "reliability_note": s.reliability_note,
    }


def citations_for(db: Session, entity_type: str, ids: list[int]) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = defaultdict(list)
    if not ids:
        return out
    rows = db.scalars(select(m.Citation).where(m.Citation.entity_type == entity_type, m.Citation.entity_id.in_(ids)).order_by(m.Citation.id))
    for c in rows:
        out[c.entity_id].append({"source": source_dict(c.source), "field": c.field, "pages": c.pages, "quote": c.quote, "note": c.note})
    return out


def figures_for(db: Session, entity_type: str, entity_id: int) -> list[dict]:
    rows = db.scalars(select(m.Figure).where(m.Figure.entity_type == entity_type, m.Figure.entity_id == entity_id).order_by(m.Figure.metric, m.Figure.side, m.Figure.id))
    polity_names = dict(db.execute(select(m.Polity.id, m.Polity.short_name)).all())
    out = []
    for f in rows:
        out.append({
            "id": f.id, "metric": f.metric.value, "side": f.side.value if f.side else None,
            "polity": {"id": f.polity_id, "name": polity_names.get(f.polity_id)} if f.polity_id else None,
            "value_low": f.value_low, "value_high": f.value_high, "value_text": f.value_text,
            "scope_note": f.scope_note, "as_of_date": f.as_of_date, "certainty": f.certainty.value,
            "pages": f.pages, "notes": f.notes, "source": source_dict(f.source) if f.source else None,
        })
    return out


def media_for(db: Session, entity_type: str, entity_id: int) -> list[dict]:
    """Only published media with verified license are ever exposed."""
    rows = db.scalars(
        select(m.MediaLink).join(m.Media).where(
            m.MediaLink.entity_type == entity_type, m.MediaLink.entity_id == entity_id,
            m.Media.status == PublicationStatus.published, m.Media.license_verified.is_(True),
        ).order_by(m.MediaLink.sort_order)
    )
    return [{
        "id": ml.media.id, "kind": ml.media.kind.value, "title": ml.media.title, "caption": ml.caption, "role": ml.role,
        "file_url": ml.media.file_url, "thumbnail_url": ml.media.thumbnail_url, "source_url": ml.media.source_url,
        "author": ml.media.author, "license": ml.media.license, "license_url": ml.media.license_url,
        "attribution": ml.media.attribution, "date_created_text": ml.media.date_created_text,
    } for ml in rows]


def documentation(db: Session, entity_type: str, entity_id: int, *, figures: bool = False) -> dict[str, Any]:
    out = {"citations": citations_for(db, entity_type, [entity_id]).get(entity_id, []), "media": media_for(db, entity_type, entity_id)}
    if figures:
        out["figures"] = figures_for(db, entity_type, entity_id)
    return out
