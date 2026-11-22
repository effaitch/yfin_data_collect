# 2026-11-22 — Nasdaq-100 added to the daily ticker list (VPS)

Host: VPS. One configuration line; no code, schema or cron change.

## Why

The context library (trading_system branch `context-library-01`, CONTEXT-EVENTS-01) fills the price move of every
dated entry by script. For US100 it needs a maintained Nasdaq-100 daily series. The database held `^IXIC` (Nasdaq
Composite) and no Nasdaq-100; the laptop's research files end on 2026-11-20, so new US100 entries would stay
`pending`.

## Change

`ticker.json`: `^NDX` added to `index_tickers` (61 tickers in all).

## Checks

- The file parses; `pytest -q tests` 3 passed.
- A one-off Yahoo look-up of `^NDX` the same day returned daily bars to 2026-11-20.
- The weekend job downloads a new ticker's full history (`DailyDataHandler`, `period="max"`).

## To verify

After Saturday 2026-11-28 02:00 UTC: `yfin` holds `^NDX` at timeframe `1d` up to 2026-11-27, and the laptop's synced
copy has it.
