# DATA-YFIN-FRIDAY-CLOSE-01 — daily rows without prices: cause, fix, repair (2026-11-24, VPS)

## What was wrong

36 daily rows in `yfin` held a volume and no open, high, low or close: 31 shares on Friday 2026-11-20 and five
(BNTX, GOOG, META, MRNA, PYPL) on Friday 2026-11-13. Indices, futures and currencies were complete. Found during the
context library's weekly update, when Nvidia's close of 2026-11-20 could not be compared with a reported figure.

## Cause

Yahoo sometimes returns the newest day with a volume and no prices (the Saturday 02:00 UTC download of 2026-11-21
had `NaN` prices and volume 626,274,281 for NVDA on 11-20). Two steps then kept that first version for good:

1. `DailyDataHandler.check_new_date` adds to the master file only dates the master file does not have yet.
2. `backfill_combined_parquet_local.py` sends to Postgres only rows newer than the latest stored one, with
   `ON CONFLICT DO NOTHING`.

A later download had the complete row (fetched 2026-11-24: NVDA 11-20 close 125.53) and both steps ignored it. The
first note on this ticket named the five-minute volume job; that was wrong, it handles four futures and crypto
tickers at intraday timeframes only.

## Fix

- `src/DailyDataHandler.py`: a row without a close is not taken from the download, and one already in the master
  file is dropped before the comparison, so the complete row replaces it. A complete stored row keeps its first
  version, as before.
- `src/backfill_combined_parquet_local.py`: `select_rows_to_upload` never sends a row without a close and also sends
  rows whose stored version has no close (`get_priceless_timestamps_pg`); `upload_query` uses
  `ON CONFLICT (ticker, timeframe, timestamp) DO UPDATE … WHERE yfin.close IS NULL OR yfin.close = 'NaN'` (unique
  index `idx_yfin_unique_sync`). A stored row that has a close is never rewritten.
- Tests: `tests/test_backfill_upload.py` (4), `tests/test_daily_master_file.py` (2); 9 pass with the 3 existing.

Impact on readers: the table's columns are unchanged. Rows without prices are no longer stored; the 36 existing ones
were filled. The laptop's copy re-reads daily series 30 days back (its change of 2026-11-23/24) and so takes them.

## Repair (job run by hand twice, as cron runs it)

| Run (UTC) | Result |
|---|---|
| 00:12:53 → 00:13:24, upload fix only | 10,435 rows: `^NDX` full history (10,367 rows, 1985-10-01 → 2026-11-23) and Monday's bars; the 36 holes stayed, which showed the master file was the second place that kept them |
| 00:14:46 → 00:15:16, both fixes | 36 rows: every hole filled; 0 daily rows without a close |

Checked after: NVDA 2026-11-20 close 125.53 (the figure CNBC reported); `^NDX` 2026-11-20 close 25,028.98.

## Not fixed here

- The master file and the table still keep the first version of a complete row while the download uses
  `auto_adjust=True`. After a dividend or split Yahoo re-bases the whole history, so stored rows of different weeks
  can sit on different adjustment bases. Ticket YFIN-ADJUSTMENT-BASE-01 (root `GEMINI_QUEUE.md`).
- Daily bars arrive once a week (Saturday 02:00 UTC). A Friday row Yahoo returns empty on Saturday now arrives with
  the next run, a week later, unless the job runs more often (a crontab change by the operator).
- `BRK.A`, `BK` and `MATIC-USD` fail on every run (known).
