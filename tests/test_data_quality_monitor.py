"""data_quality_monitor.with_date_column: daily files (dates in an unnamed index) used to raise KeyError 'Datetime'."""
import datetime as dt
import importlib.util
import os
from pathlib import Path

import pandas as pd

os.environ.setdefault("DB_PASSWORD", "test-only")
_spec = importlib.util.spec_from_file_location(
    "dqm", Path(__file__).resolve().parents[1] / "src" / "data_quality_monitor.py")
dqm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dqm)
OHLCV = {"Close": [2.0, 2.1], "High": [2.2, 2.3], "Low": [1.9, 2.0], "Open": [2.0, 2.05], "Volume": [10, 11]}


def test_daily_unnamed_date_index_becomes_date_column():
    df = pd.DataFrame(OHLCV, index=pd.Index([dt.date(2026, 11, 5), dt.date(2026, 11, 6)], dtype=object))
    out, col = dqm.with_date_column(df)
    assert col == "Date" and pd.api.types.is_datetime64_any_dtype(out["Date"])
    assert out["Date"].duplicated().sum() == 0


def test_intraday_datetime_index_keeps_its_name():
    idx = pd.DatetimeIndex(["2026-11-05 14:30", "2026-11-05 14:35"], name="Datetime", tz="UTC")
    out, col = dqm.with_date_column(pd.DataFrame(OHLCV, index=idx))
    assert col == "Datetime" and len(out) == 2


def test_existing_date_column_used_as_is():
    out, col = dqm.with_date_column(pd.DataFrame({**OHLCV, "Date": ["2026-11-05", "2026-11-06"]}))
    assert col == "Date" and pd.api.types.is_datetime64_any_dtype(out["Date"])
