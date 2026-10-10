"""Map endpoints (historical boundaries, time-filtered layers), campaign replay and search."""

import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app import models as m
from app.api.deps import date_param
from app.core.db import get_db
from app.core.errors import ApiError, not_found
from app.models.enums import MapFeatureType, PublicationStatus
from app.services.serialize import geojson, point_lonlat, source_dict, temporal
from app.services.temporal import valid_at

router = APIRouter(tags=["mapa"])
PUB = PublicationStatus.published

SEARCH_TYPES = ["conflict", "theater", "campaign", "battle", "event", "place", "polity", "unit", "person", "equipment"]


def _conflict(db: Session, slug: str) -> m.Conflict:
    c = db.scalar(select(m.Conflict).where(m.Conflict.slug == slug, m.Conflict.status == PUB))
    if not c:
        raise not_found("Conflito", slug)
    return c


def _dataset_meta(db: Session, d: m.BoundaryDataset, at: date | None) -> dict:
    src = db.get(m.Source, d.source_id) if d.source_id else None
    return {
        "slug": d.slug, "name": d.name, "reference_date": d.reference_date, "valid_from": d.valid_from, "valid_to": d.valid_to,
        "license": d.license, "precision_note": d.precision_note, "known_issues": d.known_issues, "certainty": d.certainty.value,
        "source": source_dict(src) if src else None,
        "stale": bool(at and d.valid_to and at > d.valid_to),
    }


@router.get("/map/boundary-datasets/{slug}/geojson", summary="Geometrias de um snapshot de fronteiras (cacheável)")
def boundary_geojson(slug: str, response: Response, db: Session = Depends(get_db)):
    d = db.scalar(select(m.BoundaryDataset).where(m.BoundaryDataset.slug == slug))
    if not d:
        raise not_found("Conjunto de fronteiras", slug)
    rows = db.execute(text("""
        SELECT b.id, b.label, b.subject_label, b.border_precision, b.polity_id, b.properties,
               p.slug AS polity_slug, p.name AS polity_name, p.color, ST_AsGeoJSON(b.geom, 4) AS gj,
               (SELECT ST_AsGeoJSON(ST_PointOnSurface(d.geom), 4) FROM ST_Dump(b.geom) d ORDER BY ST_Area(d.geom) DESC LIMIT 1) AS label_pt,
               ST_Area(b.geom) AS area
          FROM historical_boundaries b LEFT JOIN polities p ON p.id = b.polity_id AND p.status = 'published'
         WHERE b.dataset_id = :id"""), {"id": d.id}).mappings().all()
    features = []
    labelled: set[str] = set()
    # One label point per entity (on its largest landmass), largest entities first.
    for r in sorted(rows, key=lambda x: -(x["area"] or 0)):
        props = r["properties"] or {}
        common = {
            "id": r["id"], "label": r["label"], "subject_label": r["subject_label"], "border_precision": r["border_precision"],
            "polity_id": r["polity_id"] or -1, "subject_polity_id": props.get("subject_polity_id") or -1,
            "polity_slug": r["polity_slug"], "polity_name": r["polity_name"], "color": r["color"], "curated": r["polity_slug"] is not None,
        }
        features.append({"type": "Feature", "id": r["id"], "geometry": json.loads(r["gj"]), "properties": common})
        name = r["polity_name"] or r["label"]
        if r["label_pt"] and name not in labelled:
            labelled.add(name)
            features.append({"type": "Feature", "geometry": json.loads(r["label_pt"]), "properties": {**common, "is_label": True, "area": r["area"]}})
    response.headers["Cache-Control"] = "public, max-age=3600"
    return {"type": "FeatureCollection", "features": features}


@router.get("/map/state", summary="Estado político na data: snapshot de fronteiras aplicável e alinhamentos")
def map_state(conflict: str, at: date | None = Depends(date_param()), db: Session = Depends(get_db)):
    c = _conflict(db, conflict)
    at = at or c.start_date
    ds = db.scalar(select(m.BoundaryDataset).where(m.BoundaryDataset.reference_date <= at).order_by(m.BoundaryDataset.reference_date.desc()).limit(1))
    rows = db.execute(
        select(m.ConflictParticipation, m.Polity).join(m.Polity).where(m.ConflictParticipation.conflict_id == c.id, m.Polity.status == PUB, valid_at(m.ConflictParticipation, at))
    ).all()
    alliances = {a.id: a for a in db.scalars(select(m.Alliance).where(m.Alliance.conflict_id == c.id)).all()}
    polities = []
    for cp, p in rows:
        a = alliances.get(cp.alliance_id)
        polities.append({"polity_id": p.id, "slug": p.slug, "name": p.short_name or p.name, "color": p.color, "role": cp.role,
                         "alliance_id": a.id if a else None, "alliance_name": a.name if a else None,
                         "side": a.side.value if a and a.side else None, "alliance_color": a.color if a else None})
    return {
        "date": at, "conflict": {"slug": c.slug, "start_date": c.start_date, "end_date": c.end_date},
        "boundary_dataset": _dataset_meta(db, ds, at) if ds else None,
        "participants": polities,
        "alliances": [{"id": a.id, "name": a.name, "side": a.side.value if a.side else None, "color": a.color} for a in alliances.values()],
    }


@router.get("/map/features", summary="Camadas temporais: batalhas, eventos e cartografia militar válidos na data")
def map_features(
    conflict: str,
    at: date | None = Depends(date_param()),
    window: int = Query(3, ge=0, le=60, description="Dias anteriores à data para eventos recentes"),
    db: Session = Depends(get_db),
):
    c = _conflict(db, conflict)
    at = at or c.start_date
    feats = []
    battles = db.scalars(select(m.Battle).where(m.Battle.conflict_id == c.id, m.Battle.status == PUB, m.Battle.location.is_not(None),
                                                or_(m.Battle.start_date.is_(None), m.Battle.start_date <= at))).all()
    for b in battles:
        state = "active" if (b.end_date is None or b.end_date >= at) else "past"
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": point_lonlat(b.location)}, "properties": {
            "layer": "battle", "id": b.id, "slug": b.slug, "name": b.name, "kind": b.kind.value, "state": state,
            "is_phase": b.parent_id is not None, "start_date": str(b.start_date) if b.start_date else None,
            "end_date": str(b.end_date) if b.end_date else None, "precision_m": b.location_precision_m, "spatial_role": b.location_role.value,
        }})
    since = at - timedelta(days=window)
    events = db.scalars(select(m.Event).where(
        m.Event.conflict_id == c.id, m.Event.status == PUB, m.Event.geom.is_not(None),
        or_(m.Event.start_date.between(since, at), (m.Event.start_date <= at) & (m.Event.end_date >= at)),
    )).all()
    for e in events:
        feats.append({"type": "Feature", "geometry": geojson(e.geom), "properties": {
            "layer": "event", "id": e.id, "slug": e.slug, "name": e.title, "kind": e.kind, "importance": e.importance,
            "start_date": str(e.start_date), "days_ago": (at - e.start_date).days if e.start_date <= at else 0,
            "spatial_role": e.spatial_role.value, "precision_m": e.precision_m, "certainty": e.certainty.value, "time_of_day": e.time_of_day,
        }})
    mfs = db.scalars(select(m.MapFeature).where(m.MapFeature.conflict_id == c.id, m.MapFeature.status == PUB, valid_at(m.MapFeature, at)).order_by(m.MapFeature.sort_order)).all()
    unit_branch = dict(db.execute(select(m.Unit.id, m.ArmedForce.branch).join(m.ArmedForce, m.ArmedForce.id == m.Unit.force_id)).all())
    for f in mfs:
        feats.append({"type": "Feature", "geometry": geojson(f.geom), "properties": {
            "layer": f.feature_type.value, "id": f.id, "slug": f.slug, "name": f.label, "side": f.side.value if f.side else None,
            "spatial_role": f.spatial_role.value, "certainty": f.certainty.value, "precision_m": f.precision_m,
            "approximate": f.spatial_role.value in ("schematic", "approximate_position") or f.certainty.value in ("reconstructed", "estimated"),
            "battle_id": f.battle_id, "unit_id": f.unit_id,
            "branch": unit_branch[f.unit_id].value if f.unit_id in unit_branch else None,
        }})
    # Localities referenced by this conflict's published battles/events (context labels; not time-filtered).
    place_ids = select(m.Event.place_id).where(m.Event.conflict_id == c.id, m.Event.status == PUB, m.Event.place_id.is_not(None)).union(
        select(m.Battle.place_id).where(m.Battle.conflict_id == c.id, m.Battle.status == PUB, m.Battle.place_id.is_not(None)))
    for p in db.scalars(select(m.Place).where(m.Place.id.in_(place_ids))).all():
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": point_lonlat(p.geom)}, "properties": {
            "layer": "place", "id": p.id, "slug": p.slug, "name": p.name, "spatial_role": p.spatial_role.value,
        }})
    return {"type": "FeatureCollection", "features": feats, "meta": {"date": at, "window_days": window}}


@router.get("/map/features/{slug}", summary="Detalhe de feição cartográfica (método e incerteza)")
def map_feature_detail(slug: str, db: Session = Depends(get_db)):
    f = db.scalar(select(m.MapFeature).where(m.MapFeature.slug == slug, m.MapFeature.status == PUB))
    if not f:
        raise not_found("Feição", slug)
    from app.services.serialize import documentation, ref
    return {
        "id": f.id, "slug": f.slug, "label": f.label, "feature_type": f.feature_type.value, "description": f.description,
        "side": f.side.value if f.side else None, "spatial_role": f.spatial_role.value, "certainty": f.certainty.value,
        "precision_m": f.precision_m, "method_note": f.method_note, **temporal(f), "geometry": geojson(f.geom),
        "battle": ref(db.get(m.Battle, f.battle_id), "battle") if f.battle_id else None,
        "unit": ref(db.get(m.Unit, f.unit_id), "unit") if f.unit_id else None,
        "campaign": ref(db.get(m.Campaign, f.campaign_id), "campaign") if f.campaign_id else None,
        **documentation(db, "map_feature", f.id),
    }


@router.get("/replay/{scope}/{slug}", summary="Roteiro de reprodução histórica baseado em eventos documentados")
def replay(scope: str, slug: str, db: Session = Depends(get_db)):
    """Returns ordered *documented* steps. The client must not interpolate movement between steps."""
    if scope == "campaign":
        root = db.scalar(select(m.Campaign).where(m.Campaign.slug == slug, m.Campaign.status == PUB))
        if not root:
            raise not_found("Campanha", slug)
        ids = [root.id] + list(db.scalars(select(m.Campaign.id).where(m.Campaign.parent_id == root.id)))
        battle_ids = list(db.scalars(select(m.Battle.id).where(m.Battle.campaign_id.in_(ids))))
        ev_filter = or_(m.Event.campaign_id.in_(ids), m.Event.battle_id.in_(battle_ids or [-1]))
        mf_filter = or_(m.MapFeature.campaign_id.in_(ids), m.MapFeature.battle_id.in_(battle_ids or [-1]))
        center = [root.center_lon, root.center_lat] if root.center_lon is not None else None
        zoom = root.zoom
    elif scope == "battle":
        root = db.scalar(select(m.Battle).where(m.Battle.slug == slug, m.Battle.status == PUB))
        if not root:
            raise not_found("Batalha", slug)
        battle_ids = [root.id] + list(db.scalars(select(m.Battle.id).where(m.Battle.parent_id == root.id)))
        ev_filter = m.Event.battle_id.in_(battle_ids)
        mf_filter = m.MapFeature.battle_id.in_(battle_ids)
        center = point_lonlat(root.location)
        zoom = root.zoom
    else:
        raise ApiError(422, "invalid_scope", "Escopo deve ser 'campaign' ou 'battle'.")

    conflict = db.get(m.Conflict, root.conflict_id)
    events = db.scalars(select(m.Event).where(ev_filter, m.Event.status == PUB).order_by(m.Event.start_date, m.Event.id)).all()
    features = db.scalars(select(m.MapFeature).where(mf_filter, m.MapFeature.status == PUB)).all()
    dates = sorted({e.start_date for e in events} | {f.valid_from for f in features if f.valid_from})
    steps = []
    for d in dates:
        steps.append({
            "date": d,
            "events": [{"id": e.id, "slug": e.slug, "title": e.title, "summary": e.summary, "kind": e.kind, "importance": e.importance,
                        "time_of_day": e.time_of_day, "date_precision": e.date_precision.value, "certainty": e.certainty.value,
                        "location": point_lonlat(e.geom), "spatial_role": e.spatial_role.value, "precision_m": e.precision_m}
                       for e in events if e.start_date == d],
            "features_starting": [f.slug for f in features if f.valid_from == d],
        })
    return {
        "scope": {"type": scope, "slug": root.slug, "name": root.name, "start_date": root.start_date, "end_date": root.end_date,
                  "center": center, "zoom": zoom, "conflict": conflict.slug},
        "method": "Reconstrução baseada em eventos documentados. Não há interpolação de movimentos entre passos; "
                  "geometrias esquemáticas ou aproximadas são sinalizadas individualmente.",
        "steps": steps,
        "features": [{"slug": f.slug, "label": f.label, "feature_type": f.feature_type.value, **temporal(f), "spatial_role": f.spatial_role.value,
                      "certainty": f.certainty.value, "method_note": f.method_note} for f in features],
    }


@router.get("/search", summary="Pesquisa global sobre os registros publicados")
def search(
    q: str = Query(..., min_length=2, max_length=100),
    types: str | None = Query(None, description="lista separada por vírgulas: " + ",".join(SEARCH_TYPES)),
    conflict: str | None = None,
    polity: str | None = None,
    theater: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = Query(None, description="categoria de equipamento, escalão de unidade, tipo de batalha..."),
    branch: str | None = Query(None, description="ramo (army, navy, air_force...) para unidades"),
    limit: int = Query(40, ge=1, le=100),
    db: Session = Depends(get_db),
):
    type_list = [t for t in (types.split(",") if types else SEARCH_TYPES) if t in SEARCH_TYPES]
    if not type_list:
        raise ApiError(422, "invalid_types", "Nenhum tipo válido informado.")
    params: dict = {"q": q.strip(), "like": f"%{q.strip()}%", "types": type_list, "limit": limit}
    where = ["entity_type = ANY(:types)",
             "(lower(wa_unaccent(title)) LIKE lower(wa_unaccent(:like)) OR lower(wa_unaccent(coalesce(alt_names, ''))) LIKE lower(wa_unaccent(:like))"
             " OR similarity(lower(wa_unaccent(title)), lower(wa_unaccent(:q))) > 0.35)"]
    if conflict:
        params["cid"] = db.scalar(select(m.Conflict.id).where(m.Conflict.slug == conflict)) or -1
        where.append(":cid = ANY(conflict_ids)")
    if polity:
        params["pid"] = db.scalar(select(m.Polity.id).where(m.Polity.slug == polity)) or -1
        where.append("polity_id = :pid")
    if theater:
        params["tid"] = db.scalar(select(m.Theater.id).where(m.Theater.slug == theater)) or -1
        where.append("theater_id = :tid")
    if date_from:
        params["dfrom"] = date_from
        where.append("(end_date IS NULL OR end_date >= :dfrom)")
    if date_to:
        params["dto"] = date_to
        where.append("(start_date IS NULL OR start_date <= :dto)")
    if category:
        params["category"] = category
        where.append("category = :category")
    if branch:
        params["branch"] = branch
        where.append("branch = :branch")
    sql = f"""
        SELECT entity_type, entity_id, slug, title, subtitle, start_date, end_date, lon, lat, category, branch,
               similarity(lower(wa_unaccent(title)), lower(wa_unaccent(:q))) AS score,
               (lower(wa_unaccent(title)) LIKE lower(wa_unaccent(:q)) || '%') AS prefix
          FROM search_documents
         WHERE {' AND '.join(where)}
         ORDER BY prefix DESC, score DESC, title
         LIMIT :limit"""
    rows = db.execute(text(sql), params).mappings().all()
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["entity_type"], []).append({
            "type": r["entity_type"], "id": r["entity_id"], "slug": r["slug"], "title": r["title"], "subtitle": r["subtitle"],
            "start_date": r["start_date"], "end_date": r["end_date"], "category": r["category"], "branch": r["branch"],
            "location": [r["lon"], r["lat"]] if r["lon"] is not None else None,
        })
    return {"query": q, "total": len(rows), "groups": [{"type": t, "items": groups[t]} for t in SEARCH_TYPES if t in groups]}


@router.get("/meta/feature-types", summary="Tipos de feição cartográfica suportados")
def feature_types():
    return [t.value for t in MapFeatureType]
