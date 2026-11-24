"""DATA-YFIN-FRIDAY-CLOSE-01: the daily master file does not keep a row that has no close."""
import datetime as dt
import importlib.util
from pathlib import Path

import pandas as pd

_spec = importlib.util.spec_from_file_location(
    "daily_handler", Path(__file__).resolve().parents[1] / "src" / "DailyDataHandler.py")
dh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dh)

NAN = float("nan")


def _frame(rows):
    df = pd.DataFrame(rows, columns=["Date", "Close", "High", "Low", "Open", "Volume"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def _master(handler):
    df = pd.read_parquet(Path(handler.transf_folder) / "NVDA_1d.parquet")
    return {str(i)[:10]: (None if c != c else c) for i, c in df["Close"].items()}


def test_a_priceless_row_is_replaced_and_never_added(tmp_path):
    h = dh.DailyDataHandler(["NVDA"], str(tmp_path))
    raw = Path(h.raw_folder) / "NVDA_1d.parquet"

    # Saturday's download: Friday has a volume and no prices
    _frame([("2026-11-19", 145.98, 158.13, 145.71, 152.92, 322940100),
            ("2026-11-20", NAN, NAN, NAN, NAN, 626274281)]).to_parquet(raw, index=False)
    h.check_new_date()                       # creates the master file from the download as it is
    # the next download has Friday complete and adds Monday
    _frame([("2026-11-19", 145.98, 158.13, 145.71, 152.92, 322940100),
            ("2026-11-20", 125.53, 142.5, 124.9, 141.0, 626274300),
            ("2026-11-23", 165.05, 166.0, 150.0, 151.0, 500000000)]).to_parquet(raw, index=False)
    h.check_new_date()
    assert _master(h) == {"2026-11-19": 145.98, "2026-11-20": 125.53, "2026-11-23": 165.05}

    # a later download whose newest day is empty again adds nothing and removes nothing
    _frame([("2026-11-20", 125.53, 142.5, 124.9, 141.0, 626274300),
            ("2026-11-23", 165.05, 166.0, 150.0, 151.0, 500000000),
            ("2026-11-24", NAN, NAN, NAN, NAN, 123456789)]).to_parquet(raw, index=False)
    h.check_new_date()
    assert _master(h) == {"2026-11-19": 145.98, "2026-11-20": 125.53, "2026-11-23": 165.05}


def test_a_complete_stored_row_keeps_its_first_version(tmp_path):
    h = dh.DailyDataHandler(["NVDA"], str(tmp_path))
    raw = Path(h.raw_folder) / "NVDA_1d.parquet"
    _frame([("2026-11-19", 145.98, 158.13, 145.71, 152.92, 322940100)]).to_parquet(raw, index=False)
    h.check_new_date()
    _frame([("2026-11-19", 140.00, 150.0, 139.0, 149.0, 322940100),          # a re-based value from the vendor
            ("2026-11-20", 125.53, 142.5, 124.9, 141.0, 626274300)]).to_parquet(raw, index=False)
    h.check_new_date()
    assert _master(h) == {"2026-11-19": 145.98, "2026-11-20": 125.53}        # unchanged behaviour for complete rows
