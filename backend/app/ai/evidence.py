"""Deterministic lexical retriever over published records and their citations.

This is real, working infrastructure for a future RAG pipeline: given a query it returns
the matching records with their text and bibliographic citations. No AI model involved.
"""

import re

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.ai.contracts import EvidenceCitation, EvidenceItem
from app.models.registry import ENTITY_MODELS
from app.services.serialize import citations_for

# Generic words that must not, on their own, make a record match ("batalha de X" ≠ "batalha de Y").
STOPWORDS = {"a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "na", "no", "the", "of", "and", "batalha", "battle", "operacao", "operação",
             "operation", "campanha", "campaign", "guerra", "war", "divisao", "divisão", "division", "exercito", "exército", "army", "general"}

TEXT_FIELDS = ("summary", "description", "context", "objectives", "strategy", "result", "consequences", "biography", "operational_history", "outcome")


class LexicalRetriever:
    def __init__(self, db: Session):
        self.db = db

    def retrieve(self, query: str, *, conflict: str | None = None, limit: int = 10) -> list[EvidenceItem]:
        tokens = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2 and t not in STOPWORDS] or [query.lower()]
        params: dict = {"q": query, "limit": limit}
        clauses = []
        for i, tok in enumerate(tokens[:6]):
            params[f"t{i}"] = tok
            params[f"l{i}"] = f"%{tok}%"
            clauses.append(f"(lower(wa_unaccent(title || ' ' || coalesce(alt_names, ''))) LIKE lower(wa_unaccent(:l{i}))"
                           f" OR word_similarity(lower(wa_unaccent(:t{i})), lower(wa_unaccent(title))) > 0.7)")
        where = " AND ".join(clauses)
        if conflict:
            params["cid"] = self.db.scalar(text("SELECT id FROM conflicts WHERE slug = :s"), {"s": conflict}) or -1
            where += " AND :cid = ANY(conflict_ids)"
        rows = self.db.execute(text(f"""SELECT entity_type, entity_id, slug, title, start_date, end_date,
                similarity(lower(wa_unaccent(title)), lower(wa_unaccent(:q))) AS score
                FROM search_documents WHERE {where} ORDER BY score DESC LIMIT :limit"""), params).mappings().all()
        items = []
        for r in rows:
            model = ENTITY_MODELS[r["entity_type"]]
            obj = self.db.scalar(select(model).where(model.id == r["entity_id"]))
            body = "\n\n".join(f"{f}: {getattr(obj, f)}" for f in TEXT_FIELDS if getattr(obj, f, None))
            cites = citations_for(self.db, r["entity_type"], [r["entity_id"]]).get(r["entity_id"], [])
            items.append(EvidenceItem(
                entity_type=r["entity_type"], entity_slug=r["slug"], title=r["title"], text=body,
                period=(str(r["start_date"]) if r["start_date"] else None, str(r["end_date"]) if r["end_date"] else None),
                certainty=getattr(getattr(obj, "certainty", None), "value", None), score=float(r["score"] or 0),
                citations=[EvidenceCitation(source_slug=c["source"]["slug"], source_title=c["source"]["title"], pages=c["pages"], note=c["note"], url=c["source"]["url"]) for c in cites],
            ))
        return items
