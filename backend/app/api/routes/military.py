"""Public read endpoints: polities, armed forces, unit hierarchy (time-aware), persons."""

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import models as m
from app.api.deps import date_param
from app.core.db import get_db
from app.core.errors import ApiError, not_found
from app.models.enums import ECHELON_ORDER, PublicationStatus
from app.services.serialize import documentation, point_lonlat, provenance, ref, temporal
from app.services.temporal import is_valid_on, valid_at

router = APIRouter(tags=["organização militar"])
PUB = PublicationStatus.published


def _unit_brief(u: m.Unit) -> dict:
    return {
        "id": u.id, "slug": u.slug, "name": u.name, "name_original": u.name_original, "nickname": u.nickname,
        "echelon": u.echelon.value, "type_label": u.type_label, "polity_id": u.polity_id, "force_id": u.force_id,
        "is_multinational": u.is_multinational,
        "formed_on": u.formed_on, "formed_precision": u.formed_precision.value,
        "disbanded_on": u.disbanded_on, "disbanded_precision": u.disbanded_precision.value,
    }


def _existence(u: m.Unit, at: date | None) -> str:
    if at is None:
        return "unknown_date"
    if u.formed_on and at < u.formed_on:
        return "not_yet_formed"
    if u.disbanded_on and at > u.disbanded_on:
        return "disbanded"
    if u.formed_on is None and u.disbanded_on is None:
        return "existence_undocumented"
    return "active"


def _subordinations_at(db: Session, at: date) -> list[m.UnitSubordination]:
    return db.scalars(select(m.UnitSubordination).where(valid_at(m.UnitSubordination, at))).all()


def build_tree(db: Session, at: date, *, root_force_ids: list[int] | None = None, root_unit_id: int | None = None, depth: int = 6) -> list[dict]:
    """Hierarchy valid at `at`, built only from documented subordination records."""
    subs = _subordinations_at(db, at)
    units = {u.id: u for u in db.scalars(select(m.Unit).where(m.Unit.status == PUB)).all()}
    children: dict[int, list[m.UnitSubordination]] = defaultdict(list)
    roots: list[m.UnitSubordination] = []
    for s in subs:
        if s.unit_id not in units:
            continue
        if s.parent_unit_id is not None:
            children[s.parent_unit_id].append(s)
        elif root_force_ids is not None and s.parent_force_id in root_force_ids:
            roots.append(s)

    commanders = defaultdict(list)
    for pp in db.scalars(select(m.PersonPosition).join(m.Person).where(m.PersonPosition.unit_id.is_not(None), m.Person.status == PUB, valid_at(m.PersonPosition, at))).all():
        commanders[pp.unit_id].append({"person": ref(pp.person, "person"), "kind": pp.kind.value, "title": pp.title, **temporal(pp)})

    def node(unit_id: int, relation: m.UnitSubordination | None, level: int, seen: frozenset) -> dict:
        u = units[unit_id]
        kids = sorted(children.get(unit_id, []), key=lambda s: (ECHELON_ORDER[units[s.unit_id].echelon.value], units[s.unit_id].name))
        return {
            **_unit_brief(u),
            "relation": {"kind": relation.relation.value, **temporal(relation), "notes": relation.notes} if relation else None,
            "commanders": commanders.get(unit_id, []),
            "children": [node(s.unit_id, s, level + 1, seen | {unit_id}) for s in kids if level < depth and s.unit_id not in seen],
            "has_more": level >= depth and bool(kids),
        }

    if root_unit_id is not None:
        if root_unit_id not in units:
            return []
        return [node(root_unit_id, None, 0, frozenset())]
    roots.sort(key=lambda s: (ECHELON_ORDER[units[s.unit_id].echelon.value], units[s.unit_id].name))
    return [node(s.unit_id, s, 0, frozenset()) for s in roots]


def _unplaced_units(db: Session, at: date, force_ids: list[int]) -> list[dict]:
    """Units of these forces existing at `at` with no documented subordination at that date."""
    placed = {s.unit_id for s in _subordinations_at(db, at)}
    q = select(m.Unit).where(m.Unit.force_id.in_(force_ids), m.Unit.status == PUB,
                             or_(m.Unit.formed_on.is_(None), m.Unit.formed_on <= at),
                             or_(m.Unit.disbanded_on.is_(None), m.Unit.disbanded_on >= at))
    return [_unit_brief(u) for u in db.scalars(q).all() if u.id not in placed]


def _force_dict(f: m.ArmedForce, at: date | None) -> dict:
    return {"id": f.id, "slug": f.slug, "name": f.name, "name_original": f.name_original, "branch": f.branch.value,
            "parent_id": f.parent_id, "summary": f.summary, **temporal(f), "valid_at_date": is_valid_on(at, f.valid_from, f.valid_to)}


@router.get("/polities", summary="Entidades políticas publicadas (filtro opcional por conflito)")
def list_polities(conflict: str | None = None, db: Session = Depends(get_db)):
    q = select(m.Polity).where(m.Polity.status == PUB)
    if conflict:
        q = q.join(m.ConflictParticipation, m.ConflictParticipation.polity_id == m.Polity.id).join(m.Conflict).where(m.Conflict.slug == conflict).distinct()
    return [{"id": p.id, "slug": p.slug, "name": p.name, "short_name": p.short_name, "color": p.color, "kind": p.kind, **temporal(p)}
            for p in db.scalars(q.order_by(m.Polity.name)).all()]


@router.get("/polities/{slug}", summary="País/entidade política numa data: participação, governo, forças, comandantes")
def get_polity(slug: str, at: date | None = Depends(date_param()), conflict: str | None = Query(None), db: Session = Depends(get_db)):
    p = db.scalar(select(m.Polity).where(m.Polity.slug == slug, m.Polity.status == PUB))
    if not p:
        raise not_found("Entidade política", slug)
    conflict_obj = db.scalar(select(m.Conflict).where(m.Conflict.slug == conflict)) if conflict else None

    periods = db.scalars(select(m.PolityPeriod).where(m.PolityPeriod.polity_id == p.id).order_by(m.PolityPeriod.valid_from)).all()
    parts = db.scalars(select(m.ConflictParticipation).where(m.ConflictParticipation.polity_id == p.id).order_by(m.ConflictParticipation.valid_from)).all()
    memberships = db.execute(select(m.AllianceMembership, m.Alliance).join(m.Alliance).where(m.AllianceMembership.polity_id == p.id).order_by(m.AllianceMembership.valid_from)).all()
    forces = db.scalars(select(m.ArmedForce).where(m.ArmedForce.polity_id == p.id, m.ArmedForce.status == PUB).order_by(m.ArmedForce.sort_order, m.ArmedForce.id)).all()
    conflicts = {c.id: c for c in db.scalars(select(m.Conflict)).all()}

    battle_q = select(m.BattleParticipant, m.Battle).join(m.Battle).where(m.BattleParticipant.polity_id == p.id, m.Battle.status == PUB)
    if conflict_obj:
        battle_q = battle_q.where(m.Battle.conflict_id == conflict_obj.id)
    battles = db.execute(battle_q.order_by(m.Battle.start_date)).all()
    campaign_ids = {b.campaign_id for _, b in battles if b.campaign_id}
    campaigns = db.scalars(select(m.Campaign).where(m.Campaign.id.in_(campaign_ids), m.Campaign.status == PUB)).all() if campaign_ids else []

    unit_ids = select(m.Unit.id).where(m.Unit.polity_id == p.id)
    pos_q = select(m.PersonPosition).join(m.Person).where(m.Person.status == PUB, or_(m.PersonPosition.unit_id.in_(unit_ids), m.PersonPosition.polity_id == p.id,
                                                                                     m.PersonPosition.force_id.in_([f.id for f in forces] or [-1])))
    if at:
        pos_q = pos_q.where(valid_at(m.PersonPosition, at))
    elif conflict_obj:
        pos_q = pos_q.where(or_(m.PersonPosition.valid_to.is_(None), m.PersonPosition.valid_to >= conflict_obj.start_date),
                            or_(m.PersonPosition.valid_from.is_(None), m.PersonPosition.valid_from <= conflict_obj.end_date))
    positions = db.scalars(pos_q.order_by(m.PersonPosition.valid_from)).all()
    unit_names = dict(db.execute(select(m.Unit.id, m.Unit.name)).all())
    unit_echelon = dict(db.execute(select(m.Unit.id, m.Unit.echelon)).all())
    positions = sorted(positions, key=lambda pp: (ECHELON_ORDER[unit_echelon[pp.unit_id].value] if pp.unit_id else -1, pp.valid_from or date.min))

    eq_q = select(m.EquipmentUser, m.Equipment).join(m.Equipment).where(m.EquipmentUser.polity_id == p.id, m.Equipment.status == PUB)
    if at:
        eq_q = eq_q.where(valid_at(m.EquipmentUser, at))
    equipment = db.execute(eq_q).all()

    force_out = []
    for f in forces:
        fd = _force_dict(f, at)
        if at:
            fd["tree"] = build_tree(db, at, root_force_ids=[f.id], depth=2)
            fd["unplaced_units"] = _unplaced_units(db, at, [f.id])
        force_out.append(fd)

    return {
        "id": p.id, "slug": p.slug, "name": p.name, "name_original": p.name_original, "short_name": p.short_name, "kind": p.kind,
        "color": p.color, "summary": p.summary, "description": p.description, **temporal(p), **provenance(p),
        "date": at, "exists_at_date": is_valid_on(at, p.valid_from, p.valid_to),
        "periods": [{"government_type": x.government_type, "head_of_state": x.head_of_state, "head_of_government": x.head_of_government,
                     "capital_name": x.capital_name, "notes": x.notes, **temporal(x), "valid_at_date": is_valid_on(at, x.valid_from, x.valid_to) if at else None} for x in periods],
        "participations": [{"conflict": ref(conflicts.get(x.conflict_id), "conflict"), "alliance_id": x.alliance_id, "role": x.role, "summary": x.summary,
                            "entry_note": x.entry_note, "exit_note": x.exit_note, **temporal(x),
                            "valid_at_date": is_valid_on(at, x.valid_from, x.valid_to) if at else None} for x in parts],
        "alliances": [{"alliance": ref(a, "alliance", color=a.color, side=a.side.value if a.side else None), "role": am.role, "notes": am.notes, **temporal(am),
                       "valid_at_date": is_valid_on(at, am.valid_from, am.valid_to) if at else None} for am, a in memberships],
        "armed_forces": force_out,
        "commanders": [{"person": ref(pp.person, "person"), "title": pp.title, "kind": pp.kind.value, "rank_at_time": pp.rank_at_time,
                        "unit": {"id": pp.unit_id, "name": unit_names.get(pp.unit_id)} if pp.unit_id else None, **temporal(pp)} for pp in positions],
        "battles": [{"battle": ref(b, "battle", start_date=b.start_date, end_date=b.end_date, location=point_lonlat(b.location)), "side": bp.side.value, "role": bp.role} for bp, b in battles],
        "campaigns": [ref(c, "campaign", start_date=c.start_date, end_date=c.end_date) for c in campaigns],
        "equipment": [{"equipment": ref(e, "equipment", category=e.category.value), **temporal(eu), "notes": eu.notes} for eu, e in equipment],
        **documentation(db, "polity", p.id),
    }


@router.get("/forces/{slug}", summary="Força armada e sua hierarquia documentada numa data")
def get_force(slug: str, at: date | None = Depends(date_param()), db: Session = Depends(get_db)):
    f = db.scalar(select(m.ArmedForce).where(m.ArmedForce.slug == slug, m.ArmedForce.status == PUB))
    if not f:
        raise not_found("Força armada", slug)
    out = {**_force_dict(f, at), "description": f.description, **provenance(f), "polity": ref(db.get(m.Polity, f.polity_id), "polity"), "date": at}
    if at:
        out["tree"] = build_tree(db, at, root_force_ids=[f.id], depth=8)
        out["unplaced_units"] = _unplaced_units(db, at, [f.id])
    out.update(documentation(db, "armed_force", f.id))
    return out


@router.get("/units/{slug}/tree", summary="Subárvore de uma unidade válida numa data")
def unit_tree(slug: str, at: date | None = Depends(date_param()), depth: int = Query(6, ge=1, le=12), db: Session = Depends(get_db)):
    if at is None:
        raise ApiError(422, "date_required", "Informe ?date=AAAA-MM-DD: a hierarquia só é exibida para uma data específica.")
    u = db.scalar(select(m.Unit).where(m.Unit.slug == slug, m.Unit.status == PUB))
    if not u:
        raise not_found("Unidade", slug)
    return build_tree(db, at, root_unit_id=u.id, depth=depth)[0]


@router.get("/units/{slug}", summary="Ficha da unidade: situação na data e histórico completo")
def get_unit(slug: str, at: date | None = Depends(date_param()), db: Session = Depends(get_db)):
    u = db.scalar(select(m.Unit).where(m.Unit.slug == slug, m.Unit.status == PUB))
    if not u:
        raise not_found("Unidade", slug)
    units = {x.id: x for x in db.scalars(select(m.Unit)).all()}
    forces = {x.id: x for x in db.scalars(select(m.ArmedForce)).all()}

    names = db.scalars(select(m.UnitName).where(m.UnitName.unit_id == u.id).order_by(m.UnitName.valid_from)).all()
    up = db.scalars(select(m.UnitSubordination).where(m.UnitSubordination.unit_id == u.id).order_by(m.UnitSubordination.valid_from)).all()
    down = db.scalars(select(m.UnitSubordination).where(m.UnitSubordination.parent_unit_id == u.id).order_by(m.UnitSubordination.valid_from)).all()
    positions = db.scalars(select(m.PersonPosition).join(m.Person).where(m.PersonPosition.unit_id == u.id, m.Person.status == PUB).order_by(m.PersonPosition.valid_from)).all()
    equipment = db.execute(select(m.UnitEquipment, m.Equipment).join(m.Equipment).where(m.UnitEquipment.unit_id == u.id, m.Equipment.status == PUB).order_by(m.UnitEquipment.valid_from)).all()
    battles = db.execute(select(m.BattleUnit, m.Battle).join(m.Battle).where(m.BattleUnit.unit_id == u.id, m.Battle.status == PUB).order_by(m.Battle.start_date)).all()
    events = db.execute(select(m.EventUnit, m.Event).join(m.Event).where(m.EventUnit.unit_id == u.id, m.Event.status == PUB).order_by(m.Event.start_date)).all()
    uniforms = db.scalars(select(m.Uniform).where(m.Uniform.unit_id == u.id, m.Uniform.status == PUB)).all()

    def parent_ref(s: m.UnitSubordination) -> dict:
        if s.parent_unit_id:
            pu = units[s.parent_unit_id]
            return ref(pu, "unit", echelon=pu.echelon.value)
        return ref(forces[s.parent_force_id], "armed_force")

    def sub_dict(s: m.UnitSubordination, direction: str) -> dict:
        target = parent_ref(s) if direction == "up" else ref(units[s.unit_id], "unit", echelon=units[s.unit_id].echelon.value)
        return {"target": target, "kind": s.relation.value, **temporal(s), "notes": s.notes, "valid_at_date": is_valid_on(at, s.valid_from, s.valid_to) if at else None}

    def visible(s: m.UnitSubordination, direction: str) -> bool:
        other = s.parent_unit_id if direction == "up" else s.unit_id
        return other is None or units[other].status == PUB

    pos = [{"person": ref(pp.person, "person"), "kind": pp.kind.value, "title": pp.title, "rank_at_time": pp.rank_at_time, "notes": pp.notes,
            **temporal(pp), "valid_at_date": is_valid_on(at, pp.valid_from, pp.valid_to) if at else None} for pp in positions]
    eq = [{"equipment": ref(e, "equipment", category=e.category.value), "quantity": ue.quantity, "quantity_note": ue.quantity_note,
           "certainty": ue.certainty.value, "notes": ue.notes, **temporal(ue), "valid_at_date": is_valid_on(at, ue.valid_from, ue.valid_to) if at else None}
          for ue, e in equipment]
    ups = [sub_dict(s, "up") for s in up if visible(s, "up")]
    downs = [sub_dict(s, "down") for s in down if visible(s, "down")]
    nm = [{"name": n.name, "language": n.language, "kind": n.kind, "notes": n.notes, **temporal(n),
           "valid_at_date": is_valid_on(at, n.valid_from, n.valid_to) if at else None} for n in names]

    return {
        **_unit_brief(u), "summary": u.summary, "description": u.description, **provenance(u),
        "polity": ref(u.polity, "polity", short_name=u.polity.short_name) if u.polity else None,
        "force": ref(forces.get(u.force_id), "armed_force", branch=forces[u.force_id].branch.value) if u.force_id else None,
        "date": at, "existence_at_date": _existence(u, at),
        # Snapshot at the requested date (only records whose interval contains it)
        "at_date": None if at is None else {
            "names": [n for n in nm if n["valid_at_date"]],
            "parents": [s for s in ups if s["valid_at_date"]],
            "children": [s for s in downs if s["valid_at_date"]],
            "commanders": [p for p in pos if p["valid_at_date"]],
            "equipment": [e for e in eq if e["valid_at_date"]],
        },
        # Complete documented history, each item with its own validity interval
        "names": nm, "subordination_history": ups, "subordinate_history": downs, "command_history": pos, "equipment_history": eq,
        "battles": [{"battle": ref(b, "battle", start_date=b.start_date, end_date=b.end_date), "side": bu.side.value, "role": bu.role, **temporal(bu)} for bu, b in battles],
        "events": [{"event": ref(e, "event", start_date=e.start_date), "role": eu.role} for eu, e in events],
        "uniforms": [ref(x, "uniform") for x in uniforms],
        **documentation(db, "unit", u.id, figures=True),
    }


@router.get("/persons/{slug}", summary="Ficha de comandante/personalidade")
def get_person(slug: str, at: date | None = Depends(date_param()), db: Session = Depends(get_db)):
    p = db.scalar(select(m.Person).where(m.Person.slug == slug, m.Person.status == PUB))
    if not p:
        raise not_found("Pessoa", slug)
    units = {x.id: x for x in db.scalars(select(m.Unit)).all()}
    forces = {x.id: x for x in db.scalars(select(m.ArmedForce)).all()}
    positions = db.scalars(select(m.PersonPosition).where(m.PersonPosition.person_id == p.id).order_by(m.PersonPosition.valid_from)).all()
    ranks = db.scalars(select(m.PersonRank).where(m.PersonRank.person_id == p.id).order_by(m.PersonRank.valid_from)).all()
    battles = db.execute(select(m.BattleCommander, m.Battle).join(m.Battle).where(m.BattleCommander.person_id == p.id, m.Battle.status == PUB).order_by(m.Battle.start_date)).all()
    events = db.execute(select(m.EventPerson, m.Event).join(m.Event).where(m.EventPerson.person_id == p.id, m.Event.status == PUB).order_by(m.Event.start_date)).all()
    return {
        "id": p.id, "slug": p.slug, "name": p.name, "name_original": p.name_original, "birth_date": p.birth_date, "death_date": p.death_date,
        "birth_place": p.birth_place, "death_place": p.death_place, "summary": p.summary, "biography": p.biography, **provenance(p),
        "nationality": ref(p.nationality, "polity", short_name=p.nationality.short_name) if p.nationality else None,
        "date": at, "alive_at_date": None if at is None else ((p.birth_date is None or p.birth_date <= at) and (p.death_date is None or p.death_date >= at)),
        "ranks": [{"rank": r.rank, "rank_original": r.rank_original, **temporal(r), "notes": r.notes} for r in ranks],
        "positions": [{
            "title": pp.title, "kind": pp.kind.value, "rank_at_time": pp.rank_at_time, "notes": pp.notes,
            "unit": ref(units[pp.unit_id], "unit", echelon=units[pp.unit_id].echelon.value) if pp.unit_id and units[pp.unit_id].status == PUB else None,
            "force": ref(forces[pp.force_id], "armed_force") if pp.force_id else None,
            **temporal(pp), "valid_at_date": is_valid_on(at, pp.valid_from, pp.valid_to) if at else None,
        } for pp in positions],
        "battles": [{"battle": ref(b, "battle", start_date=b.start_date, end_date=b.end_date), "side": bc.side.value, "role": bc.role} for bc, b in battles],
        "events": [{"event": ref(e, "event", start_date=e.start_date), "role": ep.role} for ep, e in events],
        **documentation(db, "person", p.id),
    }
