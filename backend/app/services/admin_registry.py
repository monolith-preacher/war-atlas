"""Metadata-driven administration.

Form fields are derived from the SQLAlchemy models (so a new column automatically shows
up in the admin panel) and enriched with Portuguese labels. Values coming from the admin
UI are validated and converted here before reaching the ORM.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date
from enum import Enum
from typing import Any

import sqlalchemy as sa
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point, mapping, shape
from sqlalchemy.dialects.postgresql import JSONB

from app.models.registry import ENTITY_MODELS

LABELS = {
    "slug": "Identificador (slug)", "name": "Nome", "name_original": "Nome original", "short_name": "Nome curto", "title": "Título",
    "label": "Rótulo", "kind": "Tipo", "summary": "Resumo", "description": "Descrição", "context": "Contexto", "objectives": "Objetivos",
    "strategy": "Estratégia", "result": "Resultado", "consequences": "Consequências", "outcome": "Desfecho", "codename": "Codinome",
    "start_date": "Data inicial", "end_date": "Data final", "start_precision": "Precisão da data inicial", "end_precision": "Precisão da data final",
    "valid_from": "Válido de", "valid_to": "Válido até", "valid_from_precision": "Precisão (início)", "valid_to_precision": "Precisão (fim)",
    "formed_on": "Formação", "disbanded_on": "Dissolução", "formed_precision": "Precisão (formação)", "disbanded_precision": "Precisão (dissolução)",
    "birth_date": "Nascimento", "death_date": "Morte", "birth_place": "Local de nascimento", "death_place": "Local de morte",
    "certainty": "Grau de certeza", "provenance_note": "Nota de proveniência", "wikidata_id": "Wikidata (QID)", "status": "Status",
    "review_note": "Nota de revisão", "color": "Cor (#hex)", "geom": "Geometria (GeoJSON)", "location": "Localização (ponto)", "area": "Área (GeoJSON)",
    "spatial_role": "Significado da geometria", "location_role": "Significado da localização", "precision_m": "Precisão (m)",
    "location_precision_m": "Precisão da localização (m)", "echelon": "Escalão genérico", "type_label": "Designação nacional do tipo",
    "nickname": "Apelido", "branch": "Ramo", "side": "Lado", "role": "Papel", "notes": "Notas", "relation": "Tipo de relação",
    "importance": "Importância (1–5)", "time_of_day": "Horário", "date_precision": "Precisão da data", "feature_type": "Tipo de feição",
    "method_note": "Método de produção da geometria", "category": "Categoria", "specs": "Especificações (JSON)", "colors": "Cores (JSON)",
    "manufacturer": "Fabricante", "designer": "Projetista", "number_built": "Unidades produzidas", "service_from": "Em serviço desde",
    "service_to": "Em serviço até", "operational_history": "Histórico operacional", "biography": "Biografia", "rank": "Posto",
    "rank_at_time": "Posto na época", "quantity": "Quantidade", "pages": "Páginas", "quote": "Citação literal", "field": "Campo sustentado",
    "entity_type": "Tipo de registro", "entity_id": "ID do registro", "metric": "Métrica", "value_low": "Valor mínimo", "value_high": "Valor máximo",
    "value_text": "Valor (texto)", "scope_note": "Escopo do número", "as_of_date": "Data de referência", "authors": "Autores", "year": "Ano",
    "publisher": "Editora", "place": "Local", "series": "Série", "isbn": "ISBN", "url": "URL", "license": "Licença", "accessed_on": "Acessado em",
    "reliability_note": "Nota de confiabilidade", "is_multinational": "Comando multinacional", "zoom": "Zoom sugerido",
    "center_lon": "Centro (longitude)", "center_lat": "Centro (latitude)", "default_center_lon": "Centro padrão (lon)", "default_center_lat": "Centro padrão (lat)",
    "default_zoom": "Zoom padrão", "conflict_id": "Conflito", "theater_id": "Teatro", "campaign_id": "Campanha/operação", "parent_id": "Registro superior",
    "battle_id": "Batalha", "place_id": "Localidade", "unit_id": "Unidade", "person_id": "Pessoa", "polity_id": "Entidade política", "force_id": "Força armada",
    "alliance_id": "Aliança", "event_id": "Evento", "equipment_id": "Equipamento", "variant_id": "Variante", "source_id": "Fonte", "media_id": "Mídia",
    "nationality_polity_id": "Nacionalidade", "origin_polity_id": "País de origem", "parent_unit_id": "Unidade superior", "parent_force_id": "Força armada superior",
    "camouflage_id": "Camuflagem", "pattern_id": "Padrão de camuflagem", "dataset_id": "Conjunto de fronteiras", "government_type": "Forma de governo",
    "head_of_state": "Chefe de Estado", "head_of_government": "Chefe de governo", "capital_name": "Capital", "historical_names": "Nomes históricos",
    "modern_country": "País atual", "language": "Idioma", "design_period": "Período de projeto", "production_period": "Período de produção",
    "rank_original": "Posto (original)", "quantity_note": "Nota sobre quantidade", "applies_to": "Aplica-se a", "usage_note": "Nota de uso", "sort_order": "Ordem", "file_url": "URL do arquivo", "license_verified": "Licença verificada", "attribution": "Atribuição",
}

TEXTAREA = {"summary", "description", "context", "objectives", "strategy", "result", "consequences", "outcome", "biography", "operational_history",
            "notes", "provenance_note", "method_note", "review_note", "reliability_note", "quote", "entry_note", "exit_note", "usage_note", "role_note", "known_issues"}
SKIP = {"id", "created_at", "updated_at", "reviewed_at", "status"}

ENTITY_LABELS: dict[str, tuple[str, str]] = {
    "conflict": ("Conflito", "Conflitos"), "polity": ("Entidade política", "Entidades políticas"), "polity_period": ("Período de governo", "Períodos de governo"),
    "alliance": ("Aliança", "Alianças"), "alliance_membership": ("Membro de aliança", "Membros de alianças"),
    "conflict_participation": ("Participação em conflito", "Participações em conflitos"), "theater": ("Teatro", "Teatros"),
    "campaign": ("Campanha/Operação", "Campanhas e operações"), "battle": ("Batalha", "Batalhas"), "battle_participant": ("Participante de batalha", "Participantes de batalhas"),
    "battle_unit": ("Unidade em batalha", "Unidades em batalhas"), "battle_commander": ("Comandante em batalha", "Comandantes em batalhas"),
    "event": ("Evento", "Eventos"), "event_unit": ("Unidade em evento", "Unidades em eventos"), "event_person": ("Pessoa em evento", "Pessoas em eventos"),
    "place": ("Localidade", "Localidades"), "map_feature": ("Feição cartográfica", "Feições cartográficas"), "armed_force": ("Força armada", "Forças armadas"),
    "unit": ("Unidade militar", "Unidades militares"), "unit_name": ("Nome de unidade", "Nomes de unidades"),
    "unit_subordination": ("Subordinação", "Subordinações"), "person": ("Pessoa", "Pessoas"), "person_rank": ("Posto", "Postos"),
    "person_position": ("Função/comando", "Funções e comandos"), "equipment": ("Equipamento", "Equipamentos"), "equipment_variant": ("Variante", "Variantes"),
    "equipment_user": ("Usuário nacional", "Usuários nacionais"), "unit_equipment": ("Equipamento de unidade", "Equipamentos de unidades"),
    "camouflage_pattern": ("Camuflagem", "Camuflagens"), "equipment_camouflage": ("Camuflagem de equipamento", "Camuflagens de equipamentos"),
    "uniform": ("Uniforme", "Uniformes"), "insignia": ("Insígnia", "Insígnias"), "source": ("Fonte", "Fontes"), "citation": ("Citação", "Citações"),
    "figure": ("Número/estatística", "Números e estatísticas"), "media": ("Mídia", "Mídias"), "media_link": ("Vínculo de mídia", "Vínculos de mídia"),
}

# Main entities: shown in the admin navigation and subject to the "publish requires a citation" rule.
PRIMARY = ["conflict", "polity", "alliance", "theater", "campaign", "battle", "event", "place", "map_feature", "armed_force", "unit", "person",
           "equipment", "uniform", "camouflage_pattern", "source", "media"]
REQUIRES_CITATION = {"conflict", "polity", "theater", "campaign", "battle", "event", "map_feature", "unit", "person", "equipment", "uniform", "camouflage_pattern"}

TABLE_TO_ENTITY = {model.__tablename__: key for key, model in ENTITY_MODELS.items()}


@dataclass
class FieldMeta:
    name: str
    label: str
    type: str  # text | textarea | date | enum | ref | int | float | bool | geometry | json
    required: bool = False
    options: list[str] | None = None
    ref: str | None = None
    geometry_type: str | None = None


@dataclass
class EntityMeta:
    key: str
    label: str
    label_plural: str
    primary: bool
    has_status: bool
    title_fields: list[str]
    fields: list[FieldMeta] = field(default_factory=list)


def _column_meta(col: sa.Column) -> FieldMeta | None:
    if col.name in SKIP:
        return None
    label = LABELS.get(col.name, col.name.replace("_", " ").capitalize())
    required = not col.nullable and col.default is None and col.server_default is None
    t = col.type
    if col.foreign_keys:
        target = next(iter(col.foreign_keys)).column.table.name
        return FieldMeta(col.name, label, "ref", required, ref=TABLE_TO_ENTITY.get(target))
    if isinstance(t, Geometry):
        return FieldMeta(col.name, label, "geometry", required, geometry_type=t.geometry_type)
    if isinstance(t, sa.Enum):
        return FieldMeta(col.name, label, "enum", required, options=list(t.enums))
    if isinstance(t, sa.Date):
        return FieldMeta(col.name, label, "date", required)
    if isinstance(t, sa.Boolean):
        return FieldMeta(col.name, label, "bool", False)
    if isinstance(t, sa.Integer | sa.SmallInteger | sa.BigInteger):
        return FieldMeta(col.name, label, "int", required)
    if isinstance(t, sa.Float):
        return FieldMeta(col.name, label, "float", required)
    if isinstance(t, JSONB):
        return FieldMeta(col.name, label, "json", required)
    if col.name == "entity_type":
        return FieldMeta(col.name, label, "enum", required, options=sorted(ENTITY_MODELS))
    return FieldMeta(col.name, label, "textarea" if col.name in TEXTAREA else "text", required)


def entity_meta(key: str) -> EntityMeta:
    model = ENTITY_MODELS[key]
    cols = model.__table__.columns
    fields = [f for f in (_column_meta(c) for c in cols) if f]
    if "slug" in cols:
        for f in fields:
            if f.name == "slug":
                f.required = False  # auto-generated from the name when omitted
    title_fields = [c for c in ("name", "title", "label", "rank") if c in cols] or [f.name for f in fields if f.type == "ref"][:2]
    label, plural = ENTITY_LABELS.get(key, (key, key))
    return EntityMeta(key, label, plural, key in PRIMARY, "status" in cols, title_fields, fields)


def all_meta() -> list[dict]:
    return [asdict(entity_meta(k)) for k in ENTITY_MODELS]


# --- value conversion ---------------------------------------------------------

def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:150] or "registro"


class ValidationErrors(Exception):
    def __init__(self, errors: list[dict]):
        super().__init__("validation failed")
        self.errors = errors


def convert_values(key: str, values: dict[str, Any], *, partial: bool) -> dict[str, Any]:
    meta = entity_meta(key)
    by_name = {f.name: f for f in meta.fields}
    out: dict[str, Any] = {}
    errors: list[dict] = []
    for name, raw in values.items():
        f = by_name.get(name)
        if f is None:
            errors.append({"field": name, "message": "Campo desconhecido ou não editável."})
            continue
        if raw in ("", None):
            if f.required:
                errors.append({"field": name, "message": "Campo obrigatório."})
            else:
                out[name] = None
            continue
        try:
            out[name] = _convert(f, raw)
        except (ValueError, TypeError, KeyError) as exc:
            errors.append({"field": name, "message": str(exc) or "Valor inválido."})
    if not partial:
        for f in meta.fields:
            if f.required and f.name not in values and not (f.name == "slug"):
                errors.append({"field": f.name, "message": "Campo obrigatório."})
    # cross-field checks: interval coherence
    for a, b in (("valid_from", "valid_to"), ("start_date", "end_date"), ("formed_on", "disbanded_on"), ("birth_date", "death_date"), ("service_from", "service_to")):
        if isinstance(out.get(a), date) and isinstance(out.get(b), date) and out[a] > out[b]:
            errors.append({"field": b, "message": "A data final deve ser posterior ou igual à inicial."})
    if errors:
        raise ValidationErrors(errors)
    return out


def _convert(f: FieldMeta, raw: Any) -> Any:
    if f.type == "date":
        try:
            return date.fromisoformat(str(raw))
        except ValueError:
            raise ValueError("Data inválida (use AAAA-MM-DD).")
    if f.type == "enum":
        if raw not in (f.options or []):
            raise ValueError(f"Valor inválido. Opções: {', '.join(f.options or [])}")
        return raw
    if f.type in ("int", "ref"):
        return int(raw)
    if f.type == "float":
        return float(raw)
    if f.type == "bool":
        return bool(raw)
    if f.type == "json":
        if not isinstance(raw, list | dict):
            raise ValueError("JSON deve ser lista ou objeto.")
        return raw
    if f.type == "geometry":
        if isinstance(raw, list | tuple) and len(raw) == 2:
            geom = Point(float(raw[0]), float(raw[1]))
        elif isinstance(raw, dict):
            geom = shape(raw.get("geometry", raw))
        else:
            raise ValueError("Geometria deve ser GeoJSON ou [longitude, latitude].")
        if not geom.is_valid:
            raise ValueError("Geometria inválida (auto-interseção ou anel aberto).")
        minx, miny, maxx, maxy = geom.bounds
        if minx < -180 or maxx > 180 or miny < -90 or maxy > 90:
            raise ValueError("Coordenadas fora do intervalo (lon −180..180, lat −90..90).")
        expected = (f.geometry_type or "GEOMETRY").upper()
        if expected not in ("GEOMETRY", geom.geom_type.upper()):
            if expected == "MULTIPOLYGON" and geom.geom_type == "Polygon":
                from shapely.geometry import MultiPolygon
                geom = MultiPolygon([geom])
            else:
                raise ValueError(f"Tipo de geometria esperado: {expected}.")
        return from_shape(geom, srid=4326)
    s = str(raw).strip()
    if f.name == "wikidata_id" and not re.fullmatch(r"Q\d+", s):
        raise ValueError("QID inválido (ex.: Q132568).")
    if f.name == "color" and not re.fullmatch(r"#[0-9a-fA-F]{6}", s):
        raise ValueError("Cor inválida (use #RRGGBB).")
    return s


def serialize_value(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, date):
        return v.isoformat()
    if hasattr(v, "desc") and hasattr(v, "srid"):  # WKBElement
        return mapping(to_shape(v))
    return v


def row_dict(obj) -> dict[str, Any]:
    return {c.name: serialize_value(getattr(obj, c.name)) for c in obj.__table__.columns}
