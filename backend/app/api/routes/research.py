"""Evidence retrieval endpoint: foundation for a future grounded research assistant."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai.evidence import LexicalRetriever
from app.core.db import get_db

router = APIRouter(tags=["pesquisa assistida (fundação)"])


@router.get("/research/evidence", summary="Recupera registros publicados e suas fontes para uma consulta (sem IA)")
def evidence(q: str = Query(..., min_length=2, max_length=200), conflict: str | None = None, limit: int = Query(10, le=30), db: Session = Depends(get_db)):
    items = LexicalRetriever(db).retrieve(q, conflict=conflict, limit=limit)
    return {
        "query": q,
        "items": [asdict(i) for i in items],
        "note": "Recuperação lexical determinística sobre registros publicados. Nenhum modelo de IA é usado nesta fase."
        if items else "Nenhuma evidência encontrada nos registros publicados. Ausência de dados cadastrados não implica ausência histórica.",
    }
