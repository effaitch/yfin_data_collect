# AGENTS.md - Agent Reference Guide

This document provides essential context for AI agents working on the Yahoo Finance Data Collection project. It focuses on architecture, conventions, and where to find key information.

---

## 🧭 Navigation for Agents

- **Feature Implementation & Roadmap**: Refer to [PROGRESS.md](PROGRESS.md) in the root. This is the source of truth for "What is done" and "What is next".
- **Documentation & Guides**: Detailed technical guides are located in the `docs/` folder.
- **Session History**: Summarized logs of past development sessions are in `docs/sessions/`.
- **Changelogs**: Historical updates are tracked in `docs/CHANGELOGS.md`.

---

## 🏗️ Architecture Blueprint

The project is a service-based data pipeline designed for minimal resource consumption.

```
service.py (Main Orchestrator)
├── Step 1: Data Collection (main.py)
│   ├── src/DailyDataHandler.py - Daily OHLCV
│   └── src/IntradayDataHandler.py - Intraday OHLCV
├── Step 2: Data Quality Monitoring (src/data_quality_monitor.py)
│   └── Automated quality checks and visual reports
├── Step 3: BigQuery Upload (src/combine_transf_parquet_for_upload.py)
│   └── Google Cloud BigQuery sync
└── Step 4: Local Database Upload (src/backfill_combined_parquet_local.py)
    └── PostgreSQL (TimescaleDB) upload

**Auxiliary Services**:
- **Real-Time Proxy Volume Sync** (`src/realtime_volume_sync.py`): Runs every 5 mins via cron to provide high-frequency volume data for `demo_trader`.
```

## 📜 Agent Mandates

1. **Documentation First**: After implementing ANY feature or fix, you MUST update `PROGRESS.md` (mark tasks complete), `docs/CHANGELOGS.md` (add date-stamped entry), and create/update a session log in `docs/sessions/`.
2. **Micro-VM Friendly**: Avoid high-concurrency or high-memory operations. Favor sequential processing.
2. **Incremental by Default**: Always check the destination (DB/BQ) for the latest timestamp before fetching data to avoid duplicates.
3. **Environment Isolation**: All configuration must be handled via `.env`. No hardcoded credentials.
4. **Parquet Storage**: Use Parquet for intermediate storage to improve performance and reduce disk footprint.

---

## 🛠️ Operational Commands

```bash
# Validate configuration
python validate_config.py

# Run full pipeline manually
python service.py

# Run weekend job (crontab equivalent)
./run_weekend_job.sh

# Run real-time volume sync (runs every 5 mins via cron)
python src/realtime_volume_sync.py
```

---

## ⚠️ Known Quirks
- **Yahoo Finance Gaps**: Intraday data for ticker symbols with low liquidity may have gaps. The Quality Monitor flags these.
- **Local DB Connectivity**: Ensure the bot runs on the host (or uses host networking) to reach `127.0.0.1:55432`.

**Last Updated**: March 24, 2026
