"""Importer contract.

Importers never write to curated tables. They produce *staged* records
(``import_records``) holding the raw payload, a proposed mapping to War Atlas fields,
license information and warnings. A reviewer approves (creating a draft entity that
still goes through the normal publication workflow) or rejects each record.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class StagedRecord:
    entity_type: str
    external_source: str
    external_id: str
    external_url: str | None
    license: str | None
    payload: dict[str, Any]
    proposed: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


class Importer(Protocol):
    source_name: str

    def fetch(self, external_id: str, entity_type: str) -> StagedRecord: ...
