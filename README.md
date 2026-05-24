# cdc-places-nl-sql

Natural-language SQL assistant for CDC PLACES health data. Translates plain-English questions into Snowflake SQL using the Anthropic Claude API, executes them, and returns plain-English answers.

[![CI](https://github.com/qowboykay/cdc-places-nl-sql/actions/workflows/ci.yml/badge.svg)](https://github.com/qowboykay/cdc-places-nl-sql/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-Phase%201%20complete-green)

> **Depends on [cdc-places-pipeline](https://github.com/qowboykay/cdc-places-pipeline).** The Snowflake schema this project queries is built and maintained by that pipeline.

---

## Architecture

> Full diagram coming in Phase 6. Planned request flow:

```
User question  (Streamlit chat or CLI)
        |
        v
  Schema introspection  (INFORMATION_SCHEMA -> compact schema description)
        |
        v
  Claude Sonnet  (question + schema -> read-only Snowflake SQL)
        |
        v
  SQL safety validator  (sqlparse: reject non-SELECT, inject LIMIT cap)
        |
        v
  Snowflake  (execute validated query -> DataFrame)
        |
        v
  Claude Haiku  (DataFrame + question -> plain-English answer)
        |
        v
  Streamlit chat interface  (SQL collapsible, result table, answer)
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| LLM | Anthropic Claude API (`anthropic` SDK) |
| SQL generation | Claude Sonnet |
| Result summarization | Claude Haiku |
| Warehouse | Snowflake (same schema as cdc-places-pipeline) |
| SQL safety | `sqlparse` + custom validator |
| Response cache | SQLite (`cache.sqlite`) |
| Interface | Streamlit |
| Testing | `pytest` |
| Linting / formatting | `ruff` |
| Type checking | `mypy` |
| Package manager | `uv` |

---

## Setup

> Full setup instructions coming after Phase 5. Quick start below.

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/), Anthropic API key, Snowflake account with the cdc-places-pipeline schema loaded.

```bash
# Clone and install dependencies
git clone https://github.com/qowboykay/cdc-places-nl-sql.git
cd cdc-places-nl-sql
uv sync --all-groups

# Copy environment template and fill in values
cp .env.example .env

# Install pre-commit hooks
uv run pre-commit install

# Ask a question via CLI
uv run python -m cdc_places_nl_sql.cli ask "What 5 counties have the highest diabetes prevalence?"

# Launch the Streamlit chat interface
uv run streamlit run app/chat.py
```

---

## Example Questions

```
What 5 counties have the highest diabetes prevalence?
Which states have the lowest rates of colorectal cancer screening?
Compare obesity rates between rural and urban counties in Texas.
Show me counties where both smoking and diabetes prevalence exceed 20%.
```

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| 1 | NL-SQL foundation: schema introspection, Claude integration, SQL safety, CLI | Done |
| 2 | Streamlit chat interface, error recovery, SQLite cache | Pending |
| 3 | Polish, docs, tagged release | Pending |

---

## Related Project

[cdc-places-pipeline](https://github.com/qowboykay/cdc-places-pipeline): The ELT pipeline that builds and maintains the Snowflake schema this assistant queries.
