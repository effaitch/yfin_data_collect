# Yahoo Finance Data Collection Service

An automated, service-based data pipeline for fetching, processing, and storing OHLCV market data from Yahoo Finance.

## 🚀 Overview

This project provides a robust, low-resource solution for collecting historical and intraday financial data. It is optimized for micro-VM environments and operates via automated weekend cron jobs.

### Key Features
- **Multi-Source Storage**: Syncs data to local PostgreSQL (TimescaleDB) and Google Cloud BigQuery.
- **Quality Assurance**: Automated candlestick chart generation and gap detection.
- **Incremental Updates**: Efficiently fetches only new data points.
- **Micro-VM Optimized**: Sequential processing designed for stable execution on single-core systems.

## 🛠️ Quick Start

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Update .env with your database and GCP credentials
   ```

2. **Run Pipeline**:
   ```bash
   python service.py
   ```

3. **Schedule Automation**:
   Refer to `docs/CRON_SETUP.md` for weekend automation steps.

## 📂 Documentation Structure

- **Roadmap & Progress**: [PROGRESS.md](PROGRESS.md)
- **Agent Guide**: [AGENTS.md](AGENTS.md)
- **Technical Guides**: Located in the `docs/` directory.
- **Session Logs**: Historical development context in `docs/sessions/`.

## 📜 License
Internal Project - All Rights Reserved.
