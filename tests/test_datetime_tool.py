from agent.tools.datetime_tool import run as datetime_run


def test_today_returns_iso_date():
    result = datetime_run({"op": "today"})
    assert result["ok"] is True
    assert len(result["result"]) == 10


def test_days_between_two_dates():
    result = datetime_run({"op": "days_between", "start": "2020-01-01", "end": "2020-12-31"})
    assert result["ok"] is True
    assert result["result"] == 365


def test_years_since_birth():
    result = datetime_run({"op": "years_since", "date": "2000-01-01", "reference": "2026-06-02"})
    assert result["ok"] is True
    assert result["result"] == 26


def test_bad_date_returns_error_envelope():
    result = datetime_run({"op": "days_between", "start": "not-a-date", "end": "2020-01-01"})
    assert result["ok"] is False
    assert result["error_type"] == "bad_input"


def test_unknown_op_returns_error():
    result = datetime_run({"op": "teleport", "date": "2020-01-01"})
    assert result["ok"] is False
    assert result["error_type"] == "bad_input"
