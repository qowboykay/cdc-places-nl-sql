from __future__ import annotations

import os

import snowflake.connector


def _connect() -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        role=os.environ["SNOWFLAKE_ROLE"],
    )


def get_schema_description() -> str:
    """Return a compact, human-readable description of the queryable schema.

    Pulls column metadata from INFORMATION_SCHEMA for the three schemas
    the assistant is allowed to query: MAIN_STAGING, MAIN_INTERMEDIATE,
    and MAIN_MARTS. Returns a plain-text block suitable for inclusion in
    a Claude prompt.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                table_schema,
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema IN (
                'MAIN_STAGING', 'MAIN_INTERMEDIATE', 'MAIN_MARTS'
            )
            ORDER BY table_schema, table_name, ordinal_position
            """
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return "No queryable tables found."

    lines: list[str] = [
        "Database: CDC_PLACES",
        "Queryable schemas: MAIN_STAGING, MAIN_INTERMEDIATE, MAIN_MARTS",
        "",
    ]
    current_table = ""
    for schema, table, column, dtype in rows:
        full_name = f"{schema}.{table}"
        if full_name != current_table:
            current_table = full_name
            lines.append(f"Table: {full_name}")
        lines.append(f"  {column}  ({dtype})")

    return "\n".join(lines)
