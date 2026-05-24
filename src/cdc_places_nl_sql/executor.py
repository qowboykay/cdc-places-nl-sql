from __future__ import annotations

import os

import pandas as pd
import snowflake.connector


def run_query(sql: str) -> pd.DataFrame:
    """Execute a validated SQL string against Snowflake and return a DataFrame."""
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        role=os.environ["SNOWFLAKE_ROLE"],
    )
    try:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()
