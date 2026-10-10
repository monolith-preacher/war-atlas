"""Temporal query helpers.

Rule of the platform: a relation is shown "at date D" only if D falls inside its
documented interval. NULL bounds are treated as open (unknown), and the API always
returns the bounds and their precision so the UI can label them. An ``attested`` bound
is never extended: if a subordination is only attested on 1 July 1916, it is not shown
for 2 July 1916.
"""

from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.sql import ColumnElement


def valid_at(model, at: date, start: str = "valid_from", end: str = "valid_to") -> ColumnElement[bool]:
    s = getattr(model, start)
    e = getattr(model, end)
    return and_(or_(s.is_(None), s <= at), or_(e.is_(None), e >= at))


def overlaps(model, start_d: date | None, end_d: date | None, start: str = "valid_from", end: str = "valid_to") -> ColumnElement[bool]:
    """Interval [start_d, end_d] intersects the row interval (NULL = open)."""
    s = getattr(model, start)
    e = getattr(model, end)
    conds = []
    if end_d is not None:
        conds.append(or_(s.is_(None), s <= end_d))
    if start_d is not None:
        conds.append(or_(e.is_(None), e >= start_d))
    return and_(*conds) if conds else and_(True)


def is_valid_on(at: date | None, start: date | None, end: date | None) -> bool:
    if at is None:
        return True
    return (start is None or start <= at) and (end is None or end >= at)
