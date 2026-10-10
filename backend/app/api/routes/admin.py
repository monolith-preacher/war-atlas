"""Administrative API (authentication required).

Roles: editor < reviewer < admin.
* editors create records (always as draft), edit draft/in-review records and submit them for review;
* reviewers/admins can edit anything, publish, archive and delete;
* publishing a main historical entity requires at least one citation;
* every change is written to the append-only revision log.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app import models as m
from app.api.deps import ROLE_RANK, current_user, require_role
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import ApiError
from app.importers.wikidata import WikidataImporter
from app.models.enums import ImportStatus, PublicationStatus, UserRole
from app.models.registry import ENTITY_MODELS
from app.services.admin_registry import (
    PRIMARY,
    REQUIRES_CITATION,
    TABLE_TO_ENTITY,
    ValidationErrors,
    all_meta,
    convert_values,
    entity_meta,
    row_dict,
    serialize_value,
    slugify,
)

router = APIRouter(prefix="/admin", tags=["administração"], dependencies=[Depends(require_role(UserRole.editor))])


class SavePayload(BaseModel):
    values: dict[str, Any]
    comment: str | None = Field(None, max_length=2000)
    confirm_duplicate: bool = False


class StatusPayload(BaseModel):
    status: PublicationStatus
    note: str | None = Field(None, max_length=2000)


def _model(entity: str):
    model = ENTITY_MODELS.get(entity)
    if model is None:
        raise ApiError(404, "unknown_entity", f"Tipo de registro desconhecido: {entity}")
    return model


def _get(db: Session, entity: str, obj_id: int):
    obj = db.get(_model(entity), obj_id)
    if obj is None:
        raise ApiError(404, "not_found", f"{entity} #{obj_id} não encontrado.")
    return obj


def _is_reviewer(user: m.User) -> bool:
    return ROLE_RANK[user.role] >= ROLE_RANK[UserRole.reviewer]


def display_title(db: Session, obj) -> str:
    for attr in ("name", "title", "label", "rank"):
        val = getattr(obj, attr, None)
        if val:
            return str(val)
    parts = []
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if col.foreign_keys and val is not None:
            target = TABLE_TO_ENTITY.get(next(iter(col.foreign_keys)).column.table.name)
            ref_obj = db.get(ENTITY_MODELS[target], val) if target else None
            label = getattr(ref_obj, "name", None) or getattr(ref_obj, "title", None) or getattr(ref_obj, "slug", None) if ref_obj else None
            parts.append(label or f"{target}#{val}")
    vf, vt = getattr(obj, "valid_from", None), getattr(obj, "valid_to", None)
    if vf or vt:
        parts.append(f"[{vf or '…'} → {vt or '…'}]")
    return " → ".join(parts) or f"#{obj.id}"


def _log(db: Session, user: m.User, entity: str, obj_id: int, action: str, changes: dict | None = None, comment: str | None = None) -> None:
    db.add(m.Revision(entity_type=entity, entity_id=obj_id, user_id=user.id, action=action, changes=changes, comment=comment))


def _duplicates(db: Session, entity: str, values: dict, exclude_id: int | None = None) -> list[dict]:
    model = _model(entity)
    cols = model.__table__.columns
    conds = []
    if "name" in cols and values.get("name"):
        conds.append(func.similarity(func.lower(func.wa_unaccent(model.name)), func.lower(func.wa_unaccent(values["name"]))) > 0.6)
    if "wikidata_id" in cols and values.get("wikidata_id"):
        conds.append(model.wikidata_id == values["wikidata_id"])
    if not conds:
        return []
    q = select(model).where(or_(*conds))
    if exclude_id:
        q = q.where(model.id != exclude_id)
    return [{"id": o.id, "title": display_title(db, o), "slug": getattr(o, "slug", None), "wikidata_id": getattr(o, "wikidata_id", None)}
            for o in db.scalars(q.limit(10)).all()]


def _unique_slug(db: Session, model, base: str, exclude_id: int | None = None) -> str:
    slug, n = base, 2
    while True:
        q = select(model.id).where(model.slug == slug)
        if exclude_id:
            q = q.where(model.id != exclude_id)
        if db.scalar(q) is None:
            return slug
        slug, n = f"{base}-{n}", n + 1


def _check_refs(db: Session, entity: str, values: dict) -> None:
    errors = []
    for f in entity_meta(entity).fields:
        if f.type == "ref" and values.get(f.name) is not None and f.ref:
            if db.get(ENTITY_MODELS[f.ref], values[f.name]) is None:
                errors.append({"field": f.name, "message": f"Registro referenciado não existe ({f.ref} #{values[f.name]})."})
    if entity in ("citation", "figure", "media_link") and values.get("entity_type") and values.get("entity_id"):
        target = ENTITY_MODELS.get(values["entity_type"])
        if target is None or db.get(target, values["entity_id"]) is None:
            errors.append({"field": "entity_id", "message": "Registro alvo inexistente."})
    if errors:
        raise ValidationErrors(errors)


def _validation_error(exc: ValidationErrors) -> ApiError:
    return ApiError(422, "validation_error", "Corrija os campos indicados.", exc.errors)


# ---------------------------------------------------------------- metadata & lists

@router.get("/meta", summary="Metadados dos formulários administrativos")
def meta(user: m.User = Depends(current_user)):
    return {"entities": all_meta(), "primary": PRIMARY, "user": {"email": user.email, "role": user.role.value}}


@router.get("/stats", summary="Contagens por status")
def stats(db: Session = Depends(get_db)):
    out = {}
    for key in PRIMARY:
        model = ENTITY_MODELS[key]
        if "status" in model.__table__.columns:
            rows = db.execute(select(model.status, func.count()).group_by(model.status)).all()
            out[key] = {s.value: c for s, c in rows}
        else:
            out[key] = {"total": db.scalar(select(func.count()).select_from(model))}
    out["imports_pending"] = db.scalar(select(func.count()).select_from(m.ImportRecord).where(m.ImportRecord.status == ImportStatus.pending))
    return out


@router.get("/review-queue", summary="Registros aguardando revisão")
def review_queue(db: Session = Depends(get_db)):
    items = []
    for key, model in ENTITY_MODELS.items():
        if "status" not in model.__table__.columns:
            continue
        for o in db.scalars(select(model).where(model.status == PublicationStatus.in_review).order_by(model.updated_at.desc()).limit(100)).all():
            items.append({"entity": key, "id": o.id, "title": display_title(db, o), "updated_at": o.updated_at, "review_note": getattr(o, "review_note", None)})
    return sorted(items, key=lambda x: x["updated_at"], reverse=True)


@router.get("/revisions", summary="Histórico de alterações")
def revisions(entity: str | None = None, entity_id: int | None = None, limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    q = select(m.Revision, m.User.email).outerjoin(m.User, m.User.id == m.Revision.user_id)
    if entity:
        q = q.where(m.Revision.entity_type == entity)
    if entity_id:
        q = q.where(m.Revision.entity_id == entity_id)
    rows = db.execute(q.order_by(m.Revision.created_at.desc()).limit(limit)).all()
    return [{"id": r.id, "entity_type": r.entity_type, "entity_id": r.entity_id, "action": r.action, "changes": r.changes,
             "comment": r.comment, "user": email, "created_at": r.created_at} for r, email in rows]


@router.get("/lookup/{entity}", summary="Busca rápida para campos de referência")
def lookup(entity: str, q: str = "", limit: int = Query(20, le=50), db: Session = Depends(get_db)):
    model = _model(entity)
    cols = model.__table__.columns
    stmt = select(model)
    title_col = next((cols[c] for c in ("name", "title", "label", "slug") if c in cols), None)
    if q and title_col is not None:
        stmt = stmt.where(func.lower(func.wa_unaccent(title_col)).like(func.lower(func.wa_unaccent(f"%{q}%"))))
    if title_col is not None:
        stmt = stmt.order_by(title_col)
    return [{"id": o.id, "title": display_title(db, o), "status": getattr(o, "status", None) and o.status.value} for o in db.scalars(stmt.limit(limit)).all()]


# ---------------------------------------------------------------- imports (staging)

class WikidataImportPayload(BaseModel):
    qid: str = Field(..., pattern=r"^[Qq]\d+$")
    entity_type: str


class BatchImportPayload(BaseModel):
    entity_type: str
    source_name: str = Field(..., min_length=2, max_length=80)
    description: str | None = None
    records: list[dict[str, Any]] = Field(..., min_length=1, max_length=1000)


class ApprovePayload(BaseModel):
    overrides: dict[str, Any] = {}
    note: str | None = None


def _import_dict(r: m.ImportRecord) -> dict:
    return {"id": r.id, "batch_id": r.batch_id, "entity_type": r.entity_type, "external_source": r.external_source, "external_id": r.external_id,
            "external_url": r.external_url, "license": r.license, "payload": r.payload, "proposed": r.proposed, "warnings": r.warnings,
            "status": r.status.value, "target_entity_id": r.target_entity_id, "review_note": r.review_note, "created_at": r.created_at}


@router.get("/imports/records", summary="Registros importados em área de preparação")
def list_imports(status: ImportStatus | None = None, db: Session = Depends(get_db)):
    q = select(m.ImportRecord)
    if status:
        q = q.where(m.ImportRecord.status == status)
    return [_import_dict(r) for r in db.scalars(q.order_by(m.ImportRecord.created_at.desc()).limit(200)).all()]


@router.post("/imports/wikidata", status_code=201, summary="Busca uma entidade do Wikidata e a coloca em preparação")
def import_wikidata(payload: WikidataImportPayload, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if not get_settings().importers_enabled:
        raise ApiError(503, "importers_disabled", "Importadores externos estão desativados (IMPORTERS_ENABLED=false).")
    try:
        staged = WikidataImporter().fetch(payload.qid, payload.entity_type)
    except ValueError as exc:
        raise ApiError(422, "unsupported", str(exc))
    except Exception as exc:  # noqa: BLE001 - network errors are reported to the user
        raise ApiError(502, "import_failed", "Falha ao consultar o Wikidata.", str(exc))
    batch = m.ImportBatch(source_name="wikidata", description=f"Importação manual de {staged.external_id}", created_by=user.id)
    db.add(batch)
    db.flush()
    rec = m.ImportRecord(batch_id=batch.id, entity_type=staged.entity_type, external_source=staged.external_source, external_id=staged.external_id,
                         external_url=staged.external_url, license=staged.license, payload=staged.payload, proposed=staged.proposed, warnings=staged.warnings)
    model = ENTITY_MODELS[staged.entity_type]
    if "wikidata_id" in model.__table__.columns:
        existing = db.scalar(select(model).where(model.wikidata_id == staged.external_id))
        if existing:
            rec.warnings = (rec.warnings or []) + [f"Já existe registro com este QID: {display_title(db, existing)} (#{existing.id})."]
    db.add(rec)
    db.commit()
    return _import_dict(rec)


@router.post("/imports/batch", status_code=201, summary="Importação em lote (JSON) para a área de preparação")
def import_batch(payload: BatchImportPayload, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    _model(payload.entity_type)
    batch = m.ImportBatch(source_name=payload.source_name, description=payload.description, created_by=user.id)
    db.add(batch)
    db.flush()
    for i, rec in enumerate(payload.records):
        db.add(m.ImportRecord(batch_id=batch.id, entity_type=payload.entity_type, external_source=payload.source_name,
                              external_id=str(rec.get("external_id") or rec.get("wikidata_id") or i), payload=rec,
                              proposed={k: v for k, v in rec.items() if k != "external_id"}))
    db.commit()
    return {"batch_id": batch.id, "records": len(payload.records)}


@router.post("/imports/records/{record_id}/approve", summary="Aprova registro importado, criando rascunho para revisão")
def approve_import(record_id: int, payload: ApprovePayload = Body(default_factory=ApprovePayload), user: m.User = Depends(require_role(UserRole.reviewer)), db: Session = Depends(get_db)):
    rec = db.get(m.ImportRecord, record_id)
    if not rec or rec.status != ImportStatus.pending:
        raise ApiError(404, "not_found", "Registro importado inexistente ou já processado.")
    model = _model(rec.entity_type)
    raw = {**(rec.proposed or {}), **payload.overrides}
    raw = {k: v for k, v in raw.items() if k in model.__table__.columns}
    try:
        values = convert_values(rec.entity_type, raw, partial=False)
        _check_refs(db, rec.entity_type, values)
    except ValidationErrors as exc:
        raise _validation_error(exc)
    cols = model.__table__.columns
    if "slug" in cols:
        values["slug"] = _unique_slug(db, model, slugify(values.get("slug") or values.get("name") or rec.external_id))
    if "status" in cols:
        values["status"] = PublicationStatus.draft
    if "provenance_note" in cols:
        values["provenance_note"] = f"Importado de {rec.external_source} ({rec.external_id}) em {datetime.now(UTC).date()}; requer revisão."
    obj = model(**values)
    db.add(obj)
    db.flush()
    src = db.scalar(select(m.Source).where(m.Source.slug == rec.external_source))
    if src:
        db.add(m.Citation(source_id=src.id, entity_type=rec.entity_type, entity_id=obj.id, note=f"Importado de {rec.external_url or rec.external_id}"))
    rec.status = ImportStatus.approved
    rec.target_entity_id = obj.id
    rec.reviewer_id = user.id
    rec.reviewed_at = datetime.now(UTC)
    rec.review_note = payload.note
    _log(db, user, rec.entity_type, obj.id, "create", {"import_record": rec.id}, f"Aprovado da importação #{rec.id}")
    db.commit()
    return {"entity": rec.entity_type, "id": obj.id}


@router.post("/imports/records/{record_id}/reject", summary="Rejeita registro importado")
def reject_import(record_id: int, payload: ApprovePayload = Body(default_factory=ApprovePayload), user: m.User = Depends(require_role(UserRole.reviewer)), db: Session = Depends(get_db)):
    rec = db.get(m.ImportRecord, record_id)
    if not rec or rec.status != ImportStatus.pending:
        raise ApiError(404, "not_found", "Registro importado inexistente ou já processado.")
    rec.status = ImportStatus.rejected
    rec.reviewer_id = user.id
    rec.reviewed_at = datetime.now(UTC)
    rec.review_note = payload.note
    db.commit()
    return {"id": rec.id, "status": rec.status.value}


@router.get("/integrity/report", summary="Verificações de integridade (registros publicados sem fonte, etc.)")
def integrity_report(db: Session = Depends(get_db)):
    report = {}
    for key in sorted(REQUIRES_CITATION):
        model = ENTITY_MODELS[key]
        table = model.__tablename__
        rows = db.execute(text(f"""SELECT t.id, t.slug FROM {table} t WHERE t.status = 'published'
            AND NOT EXISTS (SELECT 1 FROM citations c WHERE c.entity_type = :et AND c.entity_id = t.id) ORDER BY t.id"""), {"et": key}).all()
        if rows:
            report[f"{key}_published_without_citation"] = [{"id": r.id, "slug": r.slug} for r in rows]
    orphan = db.execute(text("""SELECT u.id, u.slug FROM units u WHERE u.status='published'
        AND NOT EXISTS (SELECT 1 FROM unit_subordinations s WHERE s.unit_id = u.id) ORDER BY u.id""")).all()
    report["units_without_any_subordination"] = [{"id": r.id, "slug": r.slug} for r in orphan]
    return report


# ---------------------------------------------------------------- generic CRUD (declared last: catch-all paths)

@router.get("/{entity}", summary="Lista registros de um tipo")
def list_rows(entity: str, q: str = "", status: PublicationStatus | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, le=200),
              filter_field: str | None = None, filter_value: int | None = None, db: Session = Depends(get_db)):
    model = _model(entity)
    cols = model.__table__.columns
    stmt = select(model)
    title_col = next((cols[c] for c in ("name", "title", "label", "slug") if c in cols), None)
    if q and title_col is not None:
        stmt = stmt.where(func.lower(func.wa_unaccent(title_col)).like(func.lower(func.wa_unaccent(f"%{q}%"))))
    if status and "status" in cols:
        stmt = stmt.where(model.status == status)
    if filter_field and filter_field in cols and filter_value is not None:
        stmt = stmt.where(cols[filter_field] == filter_value)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    order = model.updated_at.desc() if "updated_at" in cols else model.id.desc()
    rows = db.scalars(stmt.order_by(order).offset((page - 1) * page_size).limit(page_size)).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [{
        "id": o.id, "title": display_title(db, o), "slug": getattr(o, "slug", None),
        "status": serialize_value(getattr(o, "status", None)), "certainty": serialize_value(getattr(o, "certainty", None)),
        "updated_at": serialize_value(getattr(o, "updated_at", None)),
    } for o in rows]}


@router.get("/{entity}/{obj_id}", summary="Registro completo, citações, relações e histórico")
def get_row(entity: str, obj_id: int, db: Session = Depends(get_db)):
    obj = _get(db, entity, obj_id)
    table = obj.__table__.name
    related = []
    for key, model in ENTITY_MODELS.items():
        for col in model.__table__.columns:
            if any(fk.column.table.name == table for fk in col.foreign_keys):
                rows = db.scalars(select(model).where(col == obj_id).limit(200)).all()
                if rows:
                    related.append({"entity": key, "field": col.name, "items": [{"id": r.id, "title": display_title(db, r)} for r in rows]})
    citations = db.scalars(select(m.Citation).where(m.Citation.entity_type == entity, m.Citation.entity_id == obj_id)).all()
    figures = db.scalars(select(m.Figure).where(m.Figure.entity_type == entity, m.Figure.entity_id == obj_id)).all()
    ref_titles = {}
    for f in entity_meta(entity).fields:
        val = getattr(obj, f.name, None)
        if f.type == "ref" and val is not None and f.ref:
            target = db.get(ENTITY_MODELS[f.ref], val)
            ref_titles[f.name] = display_title(db, target) if target else None
    return {
        "entity": entity, "values": row_dict(obj), "title": display_title(db, obj), "ref_titles": ref_titles, "related": related,
        "citations": [{"id": c.id, "source": {"id": c.source.id, "title": c.source.title, "slug": c.source.slug}, "field": c.field, "pages": c.pages, "note": c.note} for c in citations],
        "figures": [{"id": f.id, **row_dict(f)} for f in figures],
    }


# ---------------------------------------------------------------- create / update / delete

@router.post("/{entity}", status_code=201, summary="Cria registro (sempre como rascunho)")
def create_row(entity: str, payload: SavePayload, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    model = _model(entity)
    try:
        values = convert_values(entity, payload.values, partial=False)
        _check_refs(db, entity, values)
    except ValidationErrors as exc:
        raise _validation_error(exc)
    cols = model.__table__.columns
    if not payload.confirm_duplicate:
        dups = _duplicates(db, entity, values)
        if dups:
            raise ApiError(409, "possible_duplicate", "Possíveis registros duplicados encontrados. Confirme para criar mesmo assim.", dups)
    if "slug" in cols:
        base = values.get("slug") or slugify(values.get("name") or values.get("title") or values.get("label") or entity)
        values["slug"] = _unique_slug(db, model, slugify(base))
    if "status" in cols:
        values["status"] = PublicationStatus.draft
    obj = model(**values)
    db.add(obj)
    db.flush()
    _log(db, user, entity, obj.id, "create", {k: serialize_value(v) for k, v in values.items() if k not in ("geom", "location", "area")}, payload.comment)
    db.commit()
    return {"id": obj.id, "values": row_dict(obj)}


@router.patch("/{entity}/{obj_id}", summary="Atualiza registro")
def update_row(entity: str, obj_id: int, payload: SavePayload, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    obj = _get(db, entity, obj_id)
    status = getattr(obj, "status", None)
    if status in (PublicationStatus.published, PublicationStatus.archived) and not _is_reviewer(user):
        raise ApiError(403, "forbidden", "Registros publicados ou arquivados só podem ser editados por revisores. Solicite a devolução para revisão.")
    try:
        values = convert_values(entity, payload.values, partial=True)
        _check_refs(db, entity, values)
    except ValidationErrors as exc:
        raise _validation_error(exc)
    if "slug" in values:
        if not values["slug"]:
            raise ApiError(422, "validation_error", "Corrija os campos indicados.", [{"field": "slug", "message": "Campo obrigatório."}])
        values["slug"] = _unique_slug(db, type(obj), slugify(values["slug"]), exclude_id=obj.id)
    if not payload.confirm_duplicate and ("name" in values or "wikidata_id" in values):
        dups = _duplicates(db, entity, {**row_dict(obj), **{k: serialize_value(v) for k, v in values.items()}}, exclude_id=obj.id)
        if dups:
            raise ApiError(409, "possible_duplicate", "Possíveis registros duplicados encontrados. Confirme para salvar mesmo assim.", dups)
    changes = {}
    for k, v in values.items():
        old = serialize_value(getattr(obj, k))
        new = serialize_value(v)
        if old != new:
            changes[k] = [old, new] if k not in ("geom", "location", "area") else ["(geometria)", "(geometria)"]
            setattr(obj, k, v)
    if changes:
        _log(db, user, entity, obj.id, "update", changes, payload.comment)
    db.commit()
    db.refresh(obj)
    return {"id": obj.id, "values": row_dict(obj), "changed": list(changes)}


@router.delete("/{entity}/{obj_id}", summary="Remove registro (revisores; editores apenas rascunhos)")
def delete_row(entity: str, obj_id: int, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    obj = _get(db, entity, obj_id)
    status = getattr(obj, "status", None)
    if not _is_reviewer(user) and status not in (None, PublicationStatus.draft):
        raise ApiError(403, "forbidden", "Editores só podem remover rascunhos.")
    snapshot = {k: v for k, v in row_dict(obj).items() if k not in ("geom", "location", "area")}
    db.delete(obj)
    db.flush()
    _log(db, user, entity, obj_id, "delete", snapshot)
    db.commit()
    return {"deleted": True}


@router.post("/{entity}/{obj_id}/status", summary="Transição de status (rascunho → revisão → publicado/arquivado)")
def change_status(entity: str, obj_id: int, payload: StatusPayload, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    obj = _get(db, entity, obj_id)
    if not hasattr(obj, "status"):
        raise ApiError(422, "no_workflow", "Este tipo de registro não possui fluxo de publicação.")
    target = payload.status
    if target in (PublicationStatus.published, PublicationStatus.archived) and not _is_reviewer(user):
        raise ApiError(403, "forbidden", "Somente revisores podem publicar ou arquivar.")
    if not _is_reviewer(user) and obj.status in (PublicationStatus.published, PublicationStatus.archived):
        raise ApiError(403, "forbidden", "Somente revisores podem alterar registros publicados ou arquivados.")
    if target == PublicationStatus.published and entity in REQUIRES_CITATION:
        n = db.scalar(select(func.count()).select_from(m.Citation).where(m.Citation.entity_type == entity, m.Citation.entity_id == obj_id))
        if not n:
            raise ApiError(422, "citation_required", "Para publicar, associe ao menos uma fonte (citação) ao registro.")
    if target == PublicationStatus.published and entity == "media" and not (obj.license_verified and obj.license):
        raise ApiError(422, "license_required", "Mídia só pode ser publicada com licença informada e verificada.")
    old = obj.status.value
    obj.status = target
    if target in (PublicationStatus.published, PublicationStatus.archived):
        obj.reviewed_at = datetime.now(UTC)
    if payload.note:
        obj.review_note = payload.note
    _log(db, user, entity, obj_id, "status", {"status": [old, target.value]}, payload.note)
    db.commit()
    return {"id": obj_id, "status": target.value}
