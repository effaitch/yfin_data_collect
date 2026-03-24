# Progress & Roadmap: yfin_data_collect

This file tracks the implementation of features and planned optimizations for the Yahoo Finance Data Collection service.

---

## 📈 Current Status

- **Architecture**: Service-based (no Docker) - optimized for small micro VMs.
- **Automation**: Fully automated weekend cron job via `run_weekend_job.sh`.
- **Data Integrity**: Integrated quality checks with visual reports.
- **Connectivity**: Verified connectivity to local PostgreSQL (localhost:55432) and BigQuery.

---

## ✅ Completed Features

### Phase 1: Core Infrastructure
- [x] Data collection script for daily and intraday data using `yfinance`.
- [x] Sequential orchestration via `service.py`.
- [x] Incremental logic: only fetch data after the latest timestamp in the destination.

### Phase 2: Automation & Persistence
- [x] Weekend cron job setup.
- [x] Local PostgreSQL upload (TimescaleDB hypertable support).
- [x] Google Cloud BigQuery upload integration.

### Phase 3: Quality & Reliability
- [x] Data Quality Monitor with HTML reports and Plotly charts.
- [x] Enhanced error handling: one failure does not stop the entire pipeline.
- [x] Configuration validation script (`validate_config.py`).

---

## 🚀 Planned Optimizations

### 1. Documentation Reorganization (In Progress)
- [x] Create `docs/` folder and move legacy guides.
- [x] Implement `PROGRESS.md` for feature tracking.
- [x] Summarize chat logs into `docs/sessions/`.
- [x] Standardize `CHANGELOGS.md`.

### 2. Pipeline Simplification
- [ ] **Parquet Integration**: Replace CSV files with Parquet for faster read/write and reduced disk footprint.
- [ ] **Single-Core Optimization**: Explicitly limit Python processes to a single core to ensure stability on micro-VMs.
- [x] **Memory Optimization**: Refactored `backfill_combined_csv_local.py` to process files individually, avoiding large memory allocations.
- [ ] **Direct-to-DB Path**: Review if raw data can be streamed more directly to PostgreSQL to reduce intermediate file hops.

### 3. Resilience & Monitoring
- [ ] **Health Alerts**: Add simple webhook/email notifications if a weekend job fails.
- [ ] **Parallel Ticker Fetching**: (Low priority) Evaluate if single-core fetching is fast enough for the growing ticker list.

---

## 🛠️ Implementation Log

| Feature | Date | Status | Notes |
|---------|------|--------|-------|
| Documentation Structure | 2026-03-23 | ✅ | Created docs/, PROGRESS.md, and sessions/ |
| CFD vs Spread Bet Epic Alignment | 2026-03-23 | ✅ | Verified data flow for both account types |
| BigQuery Integration | 2025-12-25 | ✅ | Verified end-to-end cloud backup |
