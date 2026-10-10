"""Public read endpoints: equipment encyclopedia, uniforms, camouflage, sources."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import models as m
from app.api.deps import date_param
from app.core.db import get_db
from app.core.errors import not_found
from app.models.enums import EquipmentCategory, PublicationStatus
from app.models.registry import ENTITY_MODELS
from app.services.serialize import documentation, provenance, ref, source_dict, temporal
from app.services.temporal import is_valid_on, overlaps

router = APIRouter(tags=["equipamentos e uniformes"])
PUB = PublicationStatus.published


def _equipment_brief(e: m.Equipment, polities: dict) -> dict:
    origin = polities.get(e.origin_polity_id)
    return {
        "id": e.id, "slug": e.slug, "name": e.name, "name_original": e.name_original, "category": e.category.value,
        "type_label": e.type_label, "summary": e.summary,
        "origin": {"id": origin.id, "slug": origin.slug, "name": origin.short_name or origin.name} if origin else None,
        **temporal(e, "service_from", "service_to"),
    }


@router.get("/equipment", summary="Enciclopédia de equipamentos com filtros")
def list_equipment(
    category: EquipmentCategory | None = None,
    polity: str | None = Query(None, description="slug do país de origem ou usuário"),
    conflict: str | None = Query(None, description="slug do conflito (período de serviço sobreposto)"),
    q: str | None = Query(None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    stmt = select(m.Equipment).where(m.Equipment.status == PUB)
    if category:
        stmt = stmt.where(m.Equipment.category == category)
    if polity:
        pid = db.scalar(select(m.Polity.id).where(m.Polity.slug == polity))
        users = select(m.EquipmentUser.equipment_id).where(m.EquipmentUser.polity_id == pid)
        stmt = stmt.where(or_(m.Equipment.origin_polity_id == pid, m.Equipment.id.in_(users)))
    if conflict:
        # Documented, dated use only (national service or unit use) — never inferred from the service period alone.
        c = db.scalar(select(m.Conflict).where(m.Conflict.slug == conflict))
        if c:
            dated = lambda model: or_(model.valid_from.is_not(None), model.valid_to.is_not(None))  # noqa: E731
            used = select(m.EquipmentUser.equipment_id).where(overlaps(m.EquipmentUser, c.start_date, c.end_date), dated(m.EquipmentUser)).union(
                select(m.UnitEquipment.equipment_id).where(overlaps(m.UnitEquipment, c.start_date, c.end_date), dated(m.UnitEquipment)))
            stmt = stmt.where(m.Equipment.id.in_(used))
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(func.wa_unaccent(m.Equipment.name)).like(func.wa_unaccent(like)),
                              func.lower(func.coalesce(m.Equipment.name_original, "")).like(like)))
    polities = {p.id: p for p in db.scalars(select(m.Polity)).all()}
    rows = db.scalars(stmt.order_by(m.Equipment.category, m.Equipment.name)).all()
    return [_equipment_brief(e, polities) for e in rows]


@router.get("/equipment/{slug}", summary="Ficha de equipamento: especificações, usuários e unidades documentadas")
def get_equipment(slug: str, at: date | None = Depends(date_param()), db: Session = Depends(get_db)):
    e = db.scalar(select(m.Equipment).where(m.Equipment.slug == slug, m.Equipment.status == PUB))
    if not e:
        raise not_found("Equipamento", slug)
    polities = {p.id: p for p in db.scalars(select(m.Polity)).all()}
    variants = db.scalars(select(m.EquipmentVariant).where(m.EquipmentVariant.equipment_id == e.id, m.EquipmentVariant.status == PUB)).all()
    users = db.scalars(select(m.EquipmentUser).where(m.EquipmentUser.equipment_id == e.id).order_by(m.EquipmentUser.valid_from)).all()
    units = db.execute(select(m.UnitEquipment, m.Unit).join(m.Unit).where(m.UnitEquipment.equipment_id == e.id, m.Unit.status == PUB).order_by(m.UnitEquipment.valid_from)).all()
    camos = db.execute(select(m.EquipmentCamouflage, m.CamouflagePattern).join(m.CamouflagePattern)
                       .where(m.EquipmentCamouflage.equipment_id == e.id, m.CamouflagePattern.status == PUB)).all()
    return {
        **_equipment_brief(e, polities), "description": e.description, "operational_history": e.operational_history,
        "manufacturer": e.manufacturer, "designer": e.designer, "design_period": e.design_period,
        "production_period": e.production_period, "number_built": e.number_built, "specs": e.specs or [], **provenance(e),
        "variants": [{"slug": v.slug, "name": v.name, "name_original": v.name_original, "summary": v.summary, "specs": v.specs or []} for v in variants],
        "users": [{"polity": ref(polities[u.polity_id], "polity", short_name=polities[u.polity_id].short_name), "notes": u.notes, **temporal(u),
                   "valid_at_date": is_valid_on(at, u.valid_from, u.valid_to) if at else None} for u in users],
        "units": [{"unit": ref(un, "unit", echelon=un.echelon.value, polity=polities[un.polity_id].short_name if un.polity_id else None),
                   "quantity": ue.quantity, "quantity_note": ue.quantity_note, "certainty": ue.certainty.value, "notes": ue.notes, **temporal(ue),
                   "valid_at_date": is_valid_on(at, ue.valid_from, ue.valid_to) if at else None} for ue, un in units],
        "camouflages": [{"pattern": ref(cp, "camouflage_pattern"), "notes": ec.notes, **temporal(ec)} for ec, cp in camos],
        **documentation(db, "equipment", e.id),
    }


def _colors(c) -> list:
    return c or []


@router.get("/uniforms", summary="Uniformes (filtros por país e conflito)")
def list_uniforms(polity: str | None = None, conflict: str | None = None, db: Session = Depends(get_db)):
    stmt = select(m.Uniform).where(m.Uniform.status == PUB)
    if polity:
        stmt = stmt.join(m.Polity, m.Polity.id == m.Uniform.polity_id).where(m.Polity.slug == polity)
    if conflict:
        c = db.scalar(select(m.Conflict).where(m.Conflict.slug == conflict))
        if c:
            stmt = stmt.where(overlaps(m.Uniform, c.start_date, c.end_date))
    polities = {p.id: p for p in db.scalars(select(m.Polity)).all()}
    out = []
    for u in db.scalars(stmt.order_by(m.Uniform.valid_from)).all():
        d = {"id": u.id, "slug": u.slug, "name": u.name, "name_original": u.name_original, "role_note": u.role_note, "description": u.description,
             "colors": _colors(u.colors), **temporal(u), **provenance(u),
             "polity": ref(polities[u.polity_id], "polity", short_name=polities[u.polity_id].short_name)}
        d.update(documentation(db, "uniform", u.id))
        out.append(d)
    return out


@router.get("/camouflages", summary="Padrões de camuflagem e esquemas de pintura")
def list_camouflages(db: Session = Depends(get_db)):
    out = []
    for c in db.scalars(select(m.CamouflagePattern).where(m.CamouflagePattern.status == PUB).order_by(m.CamouflagePattern.valid_from)).all():
        d = {"id": c.id, "slug": c.slug, "name": c.name, "name_original": c.name_original, "applies_to": c.applies_to, "description": c.description,
             "usage_note": c.usage_note, "colors": _colors(c.colors), **temporal(c), **provenance(c)}
        d.update(documentation(db, "camouflage_pattern", c.id))
        out.append(d)
    return out


@router.get("/sources", summary="Fontes cadastradas")
def list_sources(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(m.Citation.source_id, func.count()).group_by(m.Citation.source_id)).all())
    return [{**source_dict(s), "citation_count": counts.get(s.id, 0)} for s in db.scalars(select(m.Source).order_by(m.Source.kind, m.Source.title)).all()]


@router.get("/sources/{slug}", summary="Fonte e registros que a citam")
def get_source(slug: str, db: Session = Depends(get_db)):
    s = db.scalar(select(m.Source).where(m.Source.slug == slug))
    if not s:
        raise not_found("Fonte", slug)
    cited = []
    for c in db.scalars(select(m.Citation).where(m.Citation.source_id == s.id).order_by(m.Citation.entity_type, m.Citation.entity_id)).all():
        model = ENTITY_MODELS.get(c.entity_type)
        obj = db.get(model, c.entity_id) if model else None
        if obj is None or getattr(obj, "status", PUB) != PUB or not hasattr(obj, "slug"):
            continue
        cited.append({"entity": ref(obj, c.entity_type), "field": c.field, "pages": c.pages, "note": c.note})
    return {**source_dict(s), "notes": s.notes, "cited_by": cited}
