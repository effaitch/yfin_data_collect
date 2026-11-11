# 2026-11-11 — Untrack `.venv/`, fix the data-quality monitor (collection moves to the VPS)

**Host**: laptop. **Ticket**: LAPTOP-COLLECTION-TO-VPS-01 hygiene item (demo_trader
`docs/handoff/laptop_prompt_2026-11-11_collection_move_close.md` task 6). Commit `63ffeeb4`.

## Why
The weekend job and the 5-minute realtime volume sync moved to the VPS today (operator: scheduled collection on the
VPS only). The VPS clone could not pull cleanly with a tracked 1 GB `.venv`, and the weekend monitor failed on every
daily file.

## Changes
- `git rm -r --cached .venv src/__pycache__` (28,975 paths) and `.gitignore` entries. The laptop's working copy keeps
  its files; pulling on the VPS deletes the clone's tracked `.venv`, which the VPS does not use.
- `data_quality_monitor.py`: `with_date_column()` — daily files store dates in an unnamed index of `datetime.date`
  objects, not a `Date` or `Datetime` column. 3 tests (named column, named index, unnamed date index).
- `run_weekend_job.sh`: prefers `/home/farq/projects/.venv` (VPS shared venv), falls back to `demo_trader/.venv`.

## Next
- VPS pulls `63ffeeb4` before its first weekend run (Sat 2026-11-14 02:00 UTC).
- Laptop cron lines for this repo go off after 2026-11-15 10:00 UTC, once the VPS runs are in the synced `yfin` table.
