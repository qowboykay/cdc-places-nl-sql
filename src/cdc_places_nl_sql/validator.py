from __future__ import annotations

import re

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import DDL, DML, Keyword

_MAX_ROWS = 500
_LIMIT_RE = re.compile(r"\bLIMIT\s+\d+", re.IGNORECASE)


class UnsafeSQLError(ValueError):
    pass


def validate_and_cap(sql: str) -> str:
    """Validate that sql is a single SELECT and cap its row limit.

    Raises UnsafeSQLError if the query is not a plain SELECT statement.
    Injects or replaces LIMIT to cap results at _MAX_ROWS rows.
    """
    stripped = sql.strip().rstrip(";")
    parsed = sqlparse.parse(stripped)

    if not parsed:
        raise UnsafeSQLError("Empty SQL.")

    stmt: Statement = parsed[0]

    first_token = None
    for token in stmt.flatten():  # type: ignore[no-untyped-call]
        if token.ttype in (DDL, DML, Keyword):
            first_token = token.normalized.upper()
            break

    if first_token != "SELECT":
        raise UnsafeSQLError(
            f"Only SELECT statements are allowed. Got: {first_token!r}"
        )

    if _LIMIT_RE.search(stripped):
        capped = _LIMIT_RE.sub(f"LIMIT {_MAX_ROWS}", stripped)
    else:
        capped = f"{stripped} LIMIT {_MAX_ROWS}"

    return capped
