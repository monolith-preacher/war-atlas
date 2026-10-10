"""Public read endpoints: conflicts, theaters, campaigns, battles, events, places."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import models as m
from app.api.deps import date_param
from app.core.db import get_db
from app.core.errors import not_found
from app.models.enums import PublicationStatus
from app.services.serialize import documentation, geojson, point_lonlat, provenance, ref, temporal
from app.services.temporal import valid_at

router = APIRouter(tags=["história"])
PUB = PublicationStatus.published


def _published(db: Session, model, slug: str, label: str):
    obj = db.scalar(select(model).where(model.slug == slug, model.status == PUB))
    if obj is None:
        raise not_found(label, slug)
    return obj


def _conflict_summary(c: m.Conflict) -> dict:
    return {
        "id": c.id, "slug": c.slug, "name": c.name, "name_original": c.name_original, "short_name": c.short_name,
        "start_date": c.start_date, "end_date": c.end_date, "summary": c.summary, "color": c.color,
        "default_view": {"center": [c.default_center_lon, c.default_center_lat], "zoom": c.default_zoom}
        if c.default_center_lon is not None else None,
    }


def _battle_brief(b: m.Battle) -> dict:
    return {
        "id": b.id, "slug": b.slug, "name": b.name, "kind": b.kind.value, "start_date": b.start_date, "end_date": b.end_date,
        "start_precision": b.start_precision.value, "end_precision": b.end_precision.value,
        "location": point_lonlat(b.location), "parent_id": b.parent_id, "campaign_id": b.campaign_id, "theater_id": b.theater_id,
        "summary": b.summary, "zoom": b.zoom,
    }


def _campaign_brief(c: m.Campaign) -> dict:
    return {
        "id": c.id, "slug": c.slug, "name": c.name, "kind": c.kind.value, "codename": c.codename,
        "start_date": c.start_date, "end_date": c.end_date, "parent_id": c.parent_id, "theater_id": c.theater_id,
        "summary": c.summary, "center": [c.center_lon, c.center_lat] if c.center_lon is not None else None, "zoom": c.zoom,
    }


def _event_brief(e: m.Event) -> dict:
    return {
        "id": e.id, "slug": e.slug, "title": e.title, "kind": e.kind, "start_date": e.start_date, "end_date": e.end_date,
        "date_precision": e.date_precision.value, "time_of_day": e.time_of_day, "importance": e.importance,
        "location": point_lonlat(e.geom), "spatial_role": e.spatial_role.value, "precision_m": e.precision_m,
        "battle_id": e.battle_id, "campaign_id": e.campaign_id, "summary": e.summary, "certainty": e.certainty.value,
    }


@router.get("/conflicts", summary="Lista os conflitos publicados")
def list_conflicts(db: Session = Depends(get_db)):
    rows = db.scalars(select(m.Conflict).where(m.Conflict.status == PUB).order_by(m.Conflict.sort_order, m.Conflict.start_date))
    out = []
    for c in rows:
        d = _conflict_summary(c)
        d["counts"] = {
            "battles": db.scalar(select(func.count()).select_from(m.Battle).where(m.Battle.conflict_id == c.id, m.Battle.status == PUB)),
            "events": db.scalar(select(func.count()).select_from(m.Event).where(m.Event.conflict_id == c.id, m.Event.status == PUB)),
            "theaters": db.scalar(select(func.count()).select_from(m.Theater).where(m.Theater.conflict_id == c.id, m.Theater.status == PUB)),
        }
        out.append(d)
    return out


@router.get("/conflicts/{slug}", summary="Detalhes de um conflito com teatros, campanhas e participantes")
def get_conflict(slug: str, db: Session = Depends(get_db)):
    c = _published(db, m.Conflict, slug, "Conflito")
    theaters = db.scalars(select(m.Theater).where(m.Theater.conflict_id == c.id, m.Theater.status == PUB).order_by(m.Theater.sort_order)).all()
    campaigns = db.scalars(select(m.Campaign).where(m.Campaign.conflict_id == c.id, m.Campaign.status == PUB).order_by(m.Campaign.start_date, m.Campaign.sort_order)).all()
    battles = db.scalars(select(m.Battle).where(m.Battle.conflict_id == c.id, m.Battle.status == PUB).order_by(m.Battle.start_date)).all()
    alliances = db.scalars(select(m.Alliance).where(m.Alliance.conflict_id == c.id, m.Alliance.status == PUB)).all()
    parts = db.scalars(select(m.ConflictParticipation).join(m.Polity).where(m.ConflictParticipation.conflict_id == c.id, m.Polity.status == PUB).order_by(m.ConflictParticipation.valid_from)).all()

    def theater_node(t: m.Theater) -> dict:
        return {
            "id": t.id, "slug": t.slug, "name": t.name, "name_original": t.name_original, "start_date": t.start_date, "end_date": t.end_date,
            "summary": t.summary, "center": [t.center_lon, t.center_lat] if t.center_lon is not None else None, "zoom": t.zoom,
            "campaigns": [_campaign_brief(x) for x in campaigns if x.theater_id == t.id],
            "battles": [_battle_brief(b) for b in battles if b.theater_id == t.id],
        }

    out = _conflict_summary(c)
    out.update({
        "description": c.description,
        **provenance(c),
        "theaters": [theater_node(t) for t in theaters],
        "alliances": [{"id": a.id, "slug": a.slug, "name": a.name, "name_original": a.name_original, "side": a.side.value if a.side else None, "color": a.color, "summary": a.summary} for a in alliances],
        "participants": [{
            "polity": ref(p.polity, "polity", short_name=p.polity.short_name, color=p.polity.color),
            "alliance_id": p.alliance_id, "role": p.role, **temporal(p), "entry_note": p.entry_note, "exit_note": p.exit_note,
        } for p in parts],
        "boundary_datasets": [{
            "slug": d.slug, "name": d.name, "reference_date": d.reference_date, "valid_from": d.valid_from, "valid_to": d.valid_to,
        } for d in db.scalars(select(m.BoundaryDataset).where(
            or_(m.BoundaryDataset.valid_to.is_(None), m.BoundaryDataset.valid_to >= c.start_date),
            m.BoundaryDataset.reference_date <= c.end_date)).all()],
        **documentation(db, "conflict", c.id),
    })
    return out


@router.get("/conflicts/{slug}/timeline", summary="Eventos e batalhas do conflito para a linha do tempo")
def conflict_timeline(slug: str, db: Session = Depends(get_db)):
    c = _published(db, m.Conflict, slug, "Conflito")
    events = db.scalars(select(m.Event).where(m.Event.conflict_id == c.id, m.Event.status == PUB).order_by(m.Event.start_date, m.Event.id)).all()
    battles = db.scalars(select(m.Battle).where(m.Battle.conflict_id == c.id, m.Battle.status == PUB).order_by(m.Battle.start_date)).all()
    campaigns = db.scalars(select(m.Campaign).where(m.Campaign.conflict_id == c.id, m.Campaign.status == PUB).order_by(m.Campaign.start_date)).all()
    # Days that have at least one event with day precision: drives day-level navigation.
    detailed_days = sorted({e.start_date for e in events if e.date_precision.value == "day"})
    return {
        "conflict": _conflict_summary(c),
        "events": [_event_brief(e) for e in events],
        "battles": [_battle_brief(b) for b in battles],
        "campaigns": [_campaign_brief(x) for x in campaigns],
        "detailed_days": detailed_days,
    }


@router.get("/conflicts/{slug}/participants", summary="Participantes e alianças válidos numa data")
def conflict_participants(slug: str, at: date | None = Depends(date_param()), db: Session = Depends(get_db)):
    c = _published(db, m.Conflict, slug, "Conflito")
    q = select(m.ConflictParticipation).join(m.Polity).where(m.ConflictParticipation.conflict_id == c.id, m.Polity.status == PUB)
    if at:
        q = q.where(valid_at(m.ConflictParticipation, at))
    rows = db.scalars(q.order_by(m.ConflictParticipation.valid_from)).all()
    return [{"polity": ref(p.polity, "polity", short_name=p.polity.short_name, color=p.polity.color),
             "alliance": ref(p.alliance, "alliance", color=p.alliance.color) if p.alliance else None,
             "role": p.role, **temporal(p)} for p in rows]


@router.get("/theaters/{slug}", summary="Teatro de operações")
def get_theater(slug: str, db: Session = Depends(get_db)):
    t = _published(db, m.Theater, slug, "Teatro")
    conflict = db.get(m.Conflict, t.conflict_id)
    campaigns = db.scalars(select(m.Campaign).where(m.Campaign.theater_id == t.id, m.Campaign.status == PUB).order_by(m.Campaign.start_date)).all()
    battles = db.scalars(select(m.Battle).where(m.Battle.theater_id == t.id, m.Battle.status == PUB).order_by(m.Battle.start_date)).all()
    return {
        "id": t.id, "slug": t.slug, "name": t.name, "name_original": t.name_original, "start_date": t.start_date, "end_date": t.end_date,
        "summary": t.summary, "description": t.description, "center": [t.center_lon, t.center_lat] if t.center_lon is not None else None, "zoom": t.zoom,
        "conflict": ref(conflict, "conflict"), **provenance(t),
        "campaigns": [_campaign_brief(x) for x in campaigns], "battles": [_battle_brief(b) for b in battles],
        **documentation(db, "theater", t.id),
    }


def _commanders_for_battles(db: Session, battle_ids: list[int]) -> list[dict]:
    if not battle_ids:
        return []
    rows = db.scalars(select(m.BattleCommander).join(m.Person).where(m.BattleCommander.battle_id.in_(battle_ids), m.Person.status == PUB)).all()
    seen, out = set(), []
    for bc in rows:
        if bc.person_id in seen:
            continue
        seen.add(bc.person_id)
        out.append({"person": ref(bc.person, "person"), "side": bc.side.value, "role": bc.role})
    return out


@router.get("/campaigns/{slug}", summary="Campanha ou operação")
def get_campaign(slug: str, db: Session = Depends(get_db)):
    c = _published(db, m.Campaign, slug, "Campanha")
    children = db.scalars(select(m.Campaign).where(m.Campaign.parent_id == c.id, m.Campaign.status == PUB).order_by(m.Campaign.start_date)).all()
    scope_ids = [c.id] + [x.id for x in children]
    battles = db.scalars(select(m.Battle).where(m.Battle.campaign_id.in_(scope_ids), m.Battle.status == PUB).order_by(m.Battle.start_date)).all()
    events = db.scalars(select(m.Event).where(m.Event.campaign_id.in_(scope_ids), m.Event.status == PUB).order_by(m.Event.start_date, m.Event.id)).all()
    parent = db.get(m.Campaign, c.parent_id) if c.parent_id else None
    return {
        **_campaign_brief(c), "name_original": c.name_original, "description": c.description, "objectives": c.objectives, "outcome": c.outcome,
        "start_precision": c.start_precision.value, "end_precision": c.end_precision.value,
        "area": geojson(c.area), **provenance(c),
        "conflict": ref(db.get(m.Conflict, c.conflict_id), "conflict"),
        "theater": ref(db.get(m.Theater, c.theater_id), "theater") if c.theater_id else None,
        "parent": ref(parent, "campaign") if parent and parent.status == PUB else None,
        "operations": [_campaign_brief(x) for x in children],
        "battles": [_battle_brief(b) for b in battles],
        "events": [_event_brief(e) for e in events],
        "commanders": _commanders_for_battles(db, [b.id for b in battles]),
        **documentation(db, "campaign", c.id, figures=True),
    }


@router.get("/battles/{slug}", summary="Batalha com participantes, unidades, comandantes, fases e fontes")
def get_battle(slug: str, db: Session = Depends(get_db)):
    b = _published(db, m.Battle, slug, "Batalha")
    children = db.scalars(select(m.Battle).where(m.Battle.parent_id == b.id, m.Battle.status == PUB).order_by(m.Battle.start_date)).all()
    scope = [b.id] + [x.id for x in children]
    participants = db.scalars(select(m.BattleParticipant).join(m.Polity).where(m.BattleParticipant.battle_id == b.id, m.Polity.status == PUB)).all()
    units = db.execute(select(m.BattleUnit, m.Unit).join(m.Unit, m.Unit.id == m.BattleUnit.unit_id)
                       .where(m.BattleUnit.battle_id == b.id, m.Unit.status == PUB)).all()
    commanders = db.scalars(select(m.BattleCommander).join(m.Person).where(m.BattleCommander.battle_id == b.id, m.Person.status == PUB)).all()
    events = db.scalars(select(m.Event).where(m.Event.battle_id.in_(scope), m.Event.status == PUB).order_by(m.Event.start_date, m.Event.id)).all()
    parent = db.get(m.Battle, b.parent_id) if b.parent_id else None
    campaign = db.get(m.Campaign, b.campaign_id) if b.campaign_id else None
    return {
        **_battle_brief(b), "name_original": b.name_original,
        "location_role": b.location_role.value, "location_precision_m": b.location_precision_m, "area": geojson(b.area),
        "context": b.context, "objectives": b.objectives, "strategy": b.strategy, "result": b.result, "consequences": b.consequences,
        **provenance(b),
        "conflict": ref(db.get(m.Conflict, b.conflict_id), "conflict"),
        "theater": ref(db.get(m.Theater, b.theater_id), "theater") if b.theater_id else None,
        "campaign": ref(campaign, "campaign") if campaign and campaign.status == PUB else None,
        "parent": ref(parent, "battle") if parent and parent.status == PUB else None,
        "place": ref(b.place, "place") if b.place else None,
        "phases": [_battle_brief(x) for x in children],
        "participants": [{"polity": ref(p.polity, "polity", short_name=p.polity.short_name, color=p.polity.color), "side": p.side.value, "role": p.role} for p in participants],
        "units": [{"unit": ref(u, "unit", echelon=u.echelon.value, type_label=u.type_label), "side": bu.side.value, "role": bu.role, **temporal(bu)} for bu, u in units],
        "commanders": [{"person": ref(bc.person, "person"), "side": bc.side.value, "role": bc.role} for bc in commanders],
        "events": [_event_brief(e) for e in events],
        **documentation(db, "battle", b.id, figures=True),
    }


@router.get("/events/{slug}", summary="Evento")
def get_event(slug: str, db: Session = Depends(get_db)):
    e = _published(db, m.Event, slug, "Evento")
    units = db.execute(select(m.EventUnit, m.Unit).join(m.Unit, m.Unit.id == m.EventUnit.unit_id).where(m.EventUnit.event_id == e.id, m.Unit.status == PUB)).all()
    persons = db.execute(select(m.EventPerson, m.Person).join(m.Person, m.Person.id == m.EventPerson.person_id).where(m.EventPerson.event_id == e.id, m.Person.status == PUB)).all()
    battle = db.get(m.Battle, e.battle_id) if e.battle_id else None
    campaign = db.get(m.Campaign, e.campaign_id) if e.campaign_id else None
    return {
        **_event_brief(e), "description": e.description, "geometry": geojson(e.geom), **provenance(e),
        "conflict": ref(db.get(m.Conflict, e.conflict_id), "conflict"),
        "battle": ref(battle, "battle") if battle and battle.status == PUB else None,
        "campaign": ref(campaign, "campaign") if campaign and campaign.status == PUB else None,
        "place": ref(e.place, "place") if e.place else None,
        "units": [{"unit": ref(u, "unit"), "role": eu.role} for eu, u in units],
        "persons": [{"person": ref(p, "person"), "role": ep.role} for ep, p in persons],
        **documentation(db, "event", e.id),
    }


@router.get("/places/{slug}", summary="Localidade e acontecimentos associados")
def get_place(slug: str, db: Session = Depends(get_db)):
    p = db.scalar(select(m.Place).where(m.Place.slug == slug))
    if not p:
        raise not_found("Localidade", slug)
    battles = db.scalars(select(m.Battle).where(m.Battle.place_id == p.id, m.Battle.status == PUB)).all()
    events = db.scalars(select(m.Event).where(m.Event.place_id == p.id, m.Event.status == PUB).order_by(m.Event.start_date)).all()
    return {
        "id": p.id, "slug": p.slug, "name": p.name, "name_original": p.name_original, "historical_names": p.historical_names,
        "modern_country": p.modern_country, "kind": p.kind, "location": point_lonlat(p.geom), "spatial_role": p.spatial_role.value,
        "precision_m": p.precision_m, "notes": p.notes, **provenance(p),
        "battles": [_battle_brief(b) for b in battles], "events": [_event_brief(e) for e in events],
        **documentation(db, "place", p.id),
    }
