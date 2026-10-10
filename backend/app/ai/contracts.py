"""Contracts for a future retrieval-augmented research assistant.

Guarantees the platform expects from any assistant implementation:
1. Read-only: assistants receive a read-only view (published records + sources).
   Proposed corrections must go through ``import_records`` (staging) for human review.
2. Grounded: every statement must cite an ``EvidenceItem`` returned by a ``Retriever``.
3. Honest absence: if no evidence is found, the assistant must say so instead of answering.
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class EvidenceCitation:
    source_slug: str
    source_title: str
    pages: str | None = None
    note: str | None = None
    url: str | None = None


@dataclass
class EvidenceItem:
    entity_type: str
    entity_slug: str
    title: str
    text: str  # textual content of the record (summary/description/...)
    period: tuple[str | None, str | None] = (None, None)
    certainty: str | None = None
    citations: list[EvidenceCitation] = field(default_factory=list)
    score: float = 0.0


class Retriever(Protocol):
    """Lexical today (see app.ai.evidence); can be swapped for vector search (pgvector) later."""

    def retrieve(self, query: str, *, conflict: str | None = None, limit: int = 10) -> list[EvidenceItem]: ...


class ResearchAssistant(Protocol):
    """Not implemented in phase 1. Must only use Retriever output and return citations."""

    def answer(self, question: str, evidence: list[EvidenceItem]) -> dict: ...
