from __future__ import annotations

import os

import anthropic
import pandas as pd

_SQL_MODEL = "claude-sonnet-4-6"
_SUMMARY_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 1024

_SQL_SYSTEM = """You are a Snowflake SQL expert. The user will ask a question about
CDC PLACES county-level public health data. You will be given the database schema.

Rules:
- Return ONLY the raw SQL query, no explanation, no markdown fences.
- Use only SELECT statements.
- Always qualify table names with schema (e.g. MAIN_MARTS.MART_COUNTY_HEALTH).
- Prefer MAIN_MARTS.MART_COUNTY_HEALTH for broad county comparisons.
- Prefer MAIN_INTERMEDIATE.INT_PLACES_MEASURES for measure-level detail.
- All prevalence values are percentages (0-100).
- Column names in MART_COUNTY_HEALTH follow the pattern <measure>_pct
  (e.g. diabetes_pct).
"""

_SUMMARY_SYSTEM = """You are a public health data analyst. The user asked a question
about CDC PLACES health data and a SQL query was run to answer it. Summarize the
results in 2-4 plain-English sentences. Be specific: include numbers and county or
state names where relevant. Do not mention SQL."""


def generate_sql(question: str, schema: str) -> str:
    """Call Claude Sonnet to translate a natural-language question into SQL."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=_SQL_MODEL,
        max_tokens=_MAX_TOKENS,
        system=_SQL_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": f"Schema:\n{schema}\n\nQuestion: {question}",
            }
        ],
    )
    content = message.content[0]
    if content.type != "text":
        raise ValueError(f"Unexpected response type: {content.type}")
    return content.text.strip()


def summarize_results(question: str, df: pd.DataFrame) -> str:
    """Call Claude Haiku to summarize a DataFrame result in plain English."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    table_text = df.to_string(index=False, max_rows=50)
    message = client.messages.create(
        model=_SUMMARY_MODEL,
        max_tokens=_MAX_TOKENS,
        system=_SUMMARY_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (f"Question: {question}\n\nResults:\n{table_text}"),
            }
        ],
    )
    content = message.content[0]
    if content.type != "text":
        raise ValueError(f"Unexpected response type: {content.type}")
    return content.text.strip()
