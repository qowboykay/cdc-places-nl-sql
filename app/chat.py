from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from cdc_places_nl_sql.cache import get_cached, save_to_cache
from cdc_places_nl_sql.executor import run_query
from cdc_places_nl_sql.llm import generate_sql, summarize_results
from cdc_places_nl_sql.schema import get_schema_description
from cdc_places_nl_sql.validator import UnsafeSQLError, validate_and_cap

load_dotenv()

st.set_page_config(page_title="CDC PLACES Health Data Assistant", layout="wide")

st.title("CDC PLACES Health Data Assistant")
st.caption(
    "Ask plain-English questions about county-level public health data. "
    "Powered by Anthropic Claude and Snowflake."
)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "schema" not in st.session_state:
    with st.spinner("Connecting to Snowflake..."):
        try:
            st.session_state["schema"] = get_schema_description()
        except Exception as exc:
            st.error(f"Could not load database schema: {exc}")
            st.stop()


def _render_assistant(msg: dict[str, Any]) -> None:
    if msg.get("cached"):
        st.caption("(cached)")
    st.markdown(str(msg["text"]))
    sql = msg.get("sql")
    if isinstance(sql, str) and sql:
        with st.expander("SQL"):
            st.code(sql, language="sql")
    df = msg.get("df")
    if isinstance(df, pd.DataFrame) and not df.empty:
        st.dataframe(df, use_container_width=True)


for msg in st.session_state["messages"]:
    role = msg["role"]
    with st.chat_message("assistant" if role == "error" else role):
        if role == "user":
            st.markdown(msg["text"])
        elif role == "error":
            st.error(msg["text"])
        else:
            _render_assistant(msg)

question = st.chat_input("Ask a question about CDC PLACES health data...")

if question:
    st.session_state["messages"].append({"role": "user", "text": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        cached = get_cached(question)
        if cached is not None:
            sql, df, summary = cached
            reply: dict[str, Any] = {
                "role": "assistant",
                "text": summary,
                "sql": sql,
                "df": df,
                "cached": True,
            }
            _render_assistant(reply)
            st.session_state["messages"].append(reply)
        else:
            try:
                with st.spinner("Generating SQL..."):
                    schema: str = st.session_state["schema"]
                    raw_sql = generate_sql(question, schema)
                    safe_sql = validate_and_cap(raw_sql)

                with st.spinner("Running query..."):
                    df = run_query(safe_sql)

                with st.spinner("Summarizing results..."):
                    summary = summarize_results(question, df)

                save_to_cache(question, safe_sql, df, summary)

                reply = {
                    "role": "assistant",
                    "text": summary,
                    "sql": safe_sql,
                    "df": df,
                    "cached": False,
                }
                _render_assistant(reply)
                st.session_state["messages"].append(reply)

            except UnsafeSQLError as exc:
                err = f"The generated query was rejected for safety reasons: {exc}"
                st.error(err)
                st.session_state["messages"].append({"role": "error", "text": err})

            except Exception as exc:
                err = f"Something went wrong: {exc}"
                st.error(err)
                st.session_state["messages"].append({"role": "error", "text": err})
