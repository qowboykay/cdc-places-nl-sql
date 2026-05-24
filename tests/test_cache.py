from __future__ import annotations

import pandas as pd
import pytest

from cdc_places_nl_sql.cache import get_cached, save_to_cache


@pytest.fixture(autouse=True)
def _tmp_cache(
    tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CACHE_DB_PATH", str(tmp_path / "test_cache.sqlite"))


def test_cache_miss_returns_none() -> None:
    assert get_cached("what is the diabetes rate?") is None


def test_round_trip() -> None:
    question = "What are the top 5 counties by obesity rate?"
    sql = "SELECT county_name, obesity_pct FROM MAIN_MARTS.MART_COUNTY_HEALTH LIMIT 500"
    df = pd.DataFrame({"county_name": ["County A"], "obesity_pct": [35.1]})
    summary = "County A has the highest obesity rate at 35.1%."

    save_to_cache(question, sql, df, summary)
    result = get_cached(question)

    assert result is not None
    returned_sql, returned_df, returned_summary = result
    assert returned_sql == sql
    assert returned_summary == summary
    assert list(returned_df.columns) == ["county_name", "obesity_pct"]
    assert returned_df["obesity_pct"].iloc[0] == pytest.approx(35.1)


def test_cache_is_case_insensitive() -> None:
    question = "What is the diabetes rate?"
    df = pd.DataFrame({"val": [1]})
    save_to_cache(question, "SELECT 1 LIMIT 500", df, "summary")

    assert get_cached("what is the diabetes rate?") is not None
    assert get_cached("WHAT IS THE DIABETES RATE?") is not None


def test_save_overwrites_existing_entry() -> None:
    question = "repeat question"
    df = pd.DataFrame({"x": [1]})
    save_to_cache(question, "SELECT 1 LIMIT 500", df, "first")
    save_to_cache(question, "SELECT 2 LIMIT 500", df, "second")

    result = get_cached(question)
    assert result is not None
    _, _, summary = result
    assert summary == "second"
