"""Wikidata importer (CC0). Maps a small, explicit set of properties per entity type.

Only day-precision dates are proposed as dates; coarser precisions are reported as
warnings so that a human decides how to record them.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.importers.base import StagedRecord

ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

# entity_type -> {war_atlas_field: wikidata_property}
PROPERTY_MAP: dict[str, dict[str, str]] = {
    "person": {"birth_date": "P569", "death_date": "P570"},
    "battle": {"start_date": "P580", "end_date": "P582", "point_in_time": "P585", "location": "P625"},
    "campaign": {"start_date": "P580", "end_date": "P582"},
    "unit": {"formed_on": "P571", "disbanded_on": "P576"},
    "polity": {"valid_from": "P571", "valid_to": "P576"},
    "place": {"geom": "P625"},
    "equipment": {},
    "conflict": {"start_date": "P580", "end_date": "P582"},
}

PRECISION_LABEL = {9: "ano", 10: "mês", 11: "dia"}


class WikidataImporter:
    source_name = "wikidata"

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or httpx.Client(timeout=20, headers={"User-Agent": get_settings().wikidata_user_agent})

    def fetch(self, external_id: str, entity_type: str) -> StagedRecord:
        if entity_type not in PROPERTY_MAP:
            raise ValueError(f"Tipo não suportado pelo importador Wikidata: {entity_type}")
        qid = external_id.strip().upper()
        resp = self.client.get(ENTITY_URL.format(qid=qid))
        resp.raise_for_status()
        entity = resp.json()["entities"][qid]
        return self.map_entity(qid, entity, entity_type)

    @staticmethod
    def _claim(entity: dict, prop: str) -> Any:
        claims = entity.get("claims", {}).get(prop) or []
        for c in claims:
            if c.get("rank") == "deprecated":
                continue
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if v is not None:
                return v
        return None

    def map_entity(self, qid: str, entity: dict, entity_type: str) -> StagedRecord:
        labels = entity.get("labels", {})
        descs = entity.get("descriptions", {})
        name = (labels.get("pt") or labels.get("pt-br") or labels.get("en") or {}).get("value")
        warnings: list[str] = []
        proposed: dict[str, Any] = {"name": name, "wikidata_id": qid}
        desc = (descs.get("pt") or descs.get("en") or {}).get("value")
        if desc and entity_type not in ("place",):
            proposed["summary"] = desc
            warnings.append("Resumo proposto é a descrição curta do Wikidata; revise e substitua por texto com fonte.")
        if not name:
            warnings.append("Sem rótulo em português ou inglês.")
        for field_name, prop in PROPERTY_MAP[entity_type].items():
            v = self._claim(entity, prop)
            if v is None:
                continue
            if isinstance(v, dict) and "time" in v:
                precision = v.get("precision")
                iso = v["time"].lstrip("+")[:10]
                if precision == 11:
                    target = "start_date" if field_name == "point_in_time" else field_name
                    proposed.setdefault(target, iso)
                    if field_name == "point_in_time":
                        proposed.setdefault("end_date", iso)
                else:
                    warnings.append(f"{prop} ({field_name}) tem precisão de {PRECISION_LABEL.get(precision, precision)}: {iso}. Não aplicado automaticamente.")
            elif isinstance(v, dict) and "latitude" in v:
                proposed[field_name] = [round(v["longitude"], 6), round(v["latitude"], 6)]
                warnings.append("Coordenada do Wikidata é um ponto de referência; confirme o significado (localização exata ou aproximada).")
        return StagedRecord(
            entity_type=entity_type, external_source="wikidata", external_id=qid,
            external_url=f"https://www.wikidata.org/wiki/{qid}", license="CC0 1.0",
            payload={"labels": {k: v["value"] for k, v in labels.items() if k in ("pt", "en", "de", "fr")},
                     "descriptions": {k: v["value"] for k, v in descs.items() if k in ("pt", "en")},
                     "claims": {p: self._claim(entity, p) for p in PROPERTY_MAP[entity_type].values()}},
            proposed={k: v for k, v in proposed.items() if v is not None}, warnings=warnings,
        )
