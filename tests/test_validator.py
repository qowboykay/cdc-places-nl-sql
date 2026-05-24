from __future__ import annotations

import pytest

from cdc_places_nl_sql.validator import UnsafeSQLError, validate_and_cap


def test_select_gets_limit_appended() -> None:
    sql = "SELECT * FROM MAIN_MARTS.MART_COUNTY_HEALTH"
    result = validate_and_cap(sql)
    assert result.endswith("LIMIT 500")


def test_existing_limit_is_replaced() -> None:
    sql = "SELECT * FROM MAIN_MARTS.MART_COUNTY_HEALTH LIMIT 10"
    result = validate_and_cap(sql)
    assert "LIMIT 500" in result
    assert "LIMIT 10" not in result


def test_trailing_semicolon_stripped() -> None:
    sql = "SELECT 1;"
    result = validate_and_cap(sql)
    assert ";" not in result


def test_non_select_raises() -> None:
    with pytest.raises(UnsafeSQLError):
        validate_and_cap("DROP TABLE foo")


def test_insert_raises() -> None:
    with pytest.raises(UnsafeSQLError):
        validate_and_cap("INSERT INTO foo VALUES (1)")


def test_empty_sql_raises() -> None:
    with pytest.raises(UnsafeSQLError):
        validate_and_cap("")


def test_select_with_where_passes() -> None:
    sql = (
        "SELECT county_name, diabetes_pct"
        " FROM MAIN_MARTS.MART_COUNTY_HEALTH"
        " WHERE state_abbr = 'TX'"
    )
    result = validate_and_cap(sql)
    assert "SELECT" in result
    assert "LIMIT 500" in result
