"""DATA-YFIN-FRIDAY-CLOSE-01: a daily row Yahoo returned without prices is not stored, and a stored one is filled."""
import importlib.util
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

_spec = importlib.util.spec_from_file_location(
    "backfill_upload", Path(__file__).resolve().parents[1] / "src" / "backfill_combined_parquet_local.py")
bu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bu)


def _df(rows):
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df.insert(0, "timeframe", "1d")
    df.insert(0, "ticker", "NVDA")
    return df


NAN = float("nan")
WEEK = [("2026-11-18", 159.19, 159.70, 150.40, 150.96, 349791400.0),
        ("2026-11-19", 152.92, 158.13, 145.71, 145.98, 322940100.0),
        ("2026-11-20", NAN, NAN, NAN, NAN, 626274281.0)]          # as Yahoo returned it on 2026-11-21 02:00 UTC


def test_a_row_without_a_close_is_never_sent():
    out = bu.select_rows_to_upload(_df(WEEK), pd.Timestamp("2026-11-18", tz="UTC"))
    assert [d.strftime("%m-%d") for d in out["timestamp"]] == ["11-19"]
    first_load = bu.select_rows_to_upload(_df(WEEK), None)
    assert len(first_load) == 2 and first_load["close"].notna().all()


def test_a_stored_row_without_a_close_is_sent_again_when_yahoo_has_it():
    later = WEEK[:2] + [("2026-11-20", 141.0, 142.5, 124.9, 125.53, 626274281.0), ("2026-11-23", 126.0, 131.0, 125.0, 130.2, 4.1e8)]
    latest_stored = pd.Timestamp("2026-11-20", tz="UTC")           # the empty Friday row is the latest stored bar
    out = bu.select_rows_to_upload(_df(later), latest_stored, [latest_stored.to_pydatetime()])
    assert [d.strftime("%m-%d") for d in out["timestamp"]] == ["11-20", "11-23"]
    assert out["close"].tolist() == [125.53, 130.2]
    # without the list of empty rows only the newer bar goes, which is how the hole stayed
    assert len(bu.select_rows_to_upload(_df(later), latest_stored)) == 1
    # an older hole (2026-11-13 style) is found as well, complete older rows are not re-sent
    old_hole = pd.Timestamp("2026-11-18", tz="UTC")
    out = bu.select_rows_to_upload(_df(later), pd.Timestamp("2026-11-23", tz="UTC"), [old_hole])
    assert [d.strftime("%m-%d") for d in out["timestamp"]] == ["11-18"]


def test_upload_fills_only_rows_that_have_no_close():
    q = bu.upload_query("yfin", "ticker,timeframe,timestamp,open,high,low,close,volume")
    assert "ON CONFLICT (ticker, timeframe, timestamp) DO UPDATE SET" in q
    assert q.rstrip().endswith("WHERE yfin.close IS NULL OR yfin.close = 'NaN'")
    assert "DO NOTHING" not in q
    conn = MagicMock()
    with patch.object(bu, "execute_values") as ev:
        n = bu.upload_to_pg(conn, _df(WEEK[:2]), "yfin")
    assert n == 2 and ev.call_args.args[1] == q
    conn.commit.assert_called_once()


def test_priceless_timestamps_query_reads_null_and_nan():
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [(pd.Timestamp("2026-11-20", tz="UTC").to_pydatetime(),)]
    out = bu.get_priceless_timestamps_pg(conn, "yfin", "NVDA", "1d")
    sql, params = cur.execute.call_args.args
    assert "close IS NULL OR close = 'NaN'" in sql and params == ("NVDA", "1d")
    assert len(out) == 1
