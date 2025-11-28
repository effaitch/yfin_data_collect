# Project Improvement Roadmap & Current State

This document outlines the current state, architecture, and implementation details for the Yahoo Finance Data Collection project. Use this as a guide when implementing enhancements or understanding the system.

## Project Overview

This project is designed to run as an **automated data collection and storage service** that:
1. Fetches financial market data (OHLCV) from Yahoo Finance API
2. Processes and transforms the data
3. Stores data in multiple destinations (local database, cloud storage)
4. Monitors data quality and integrity

**Architecture**: Service-based (no Docker) - optimized for small micro VMs

## Current Architecture

### Service-Based Workflow

The project uses a **service-based architecture** (no Docker) with the main orchestration script `service.py`:

```
service.py (Main Orchestrator)
├── Step 1: Data Collection
│   ├── DailyDataHandler.py - Collects daily (1d) data
│   └── IntradayDataHandler.py - Collects intraday data (1m, 5m, 15m, 30m, 1h, 90m)
├── Step 2: Data Quality Monitoring (Optional)
│   └── data_quality_monitor.py - Quality checks and visual reports
├── Step 3: Local Database Upload (Optional)
│   └── Integrated PostgreSQL upload in service.py
└── Step 4: Cloud Storage Upload (Optional)
    ├── BigQuery upload (integrated in service.py)
    └── GCS Parquet upload (gcs_uploader.py)
```

### Workflow Sequence

1. **Data Collection** (`main.py` via service.py)
   - **Purpose**: Fetch ticker and timeframe data from Yahoo Finance
   - **Input**: `ticker.json` configuration file
   - **Output**: Processed CSV files in `all_ohclv_data/transf_data/`
   - **Handlers**:
     - `DailyDataHandler.py` - Collects daily (1d) data
     - `IntradayDataHandler.py` - Collects intraday data (1m, 5m, 15m, 30m, 1h, 90m)

2. **Data Quality Monitoring** (`dataHandler/data_quality_monitor.py`)
   - **Purpose**: Automated quality checks with visual reports
   - **Status**: ✅ **COMPLETE** - Fully implemented
   - **Features**:
     - Detects missing values, duplicate timestamps
     - Checks price consistency (high >= low, close within range)
     - Detects volume anomalies (zero/negative volume)
     - Identifies outliers using Z-score analysis
     - Detects gaps in time series
     - Generates Plotly candlestick charts with volume bars
     - Creates HTML reports with statistics
   - **Output**: Reports in `logs/quality_reports/`
   - **Configuration**: `ENABLE_QUALITY_CHECKS=true` in `.env`

3. **Local Database Upload** (Integrated in `service.py`)
   - **Purpose**: Upload processed data to local PostgreSQL database
   - **Target**: PostgreSQL table `yfin`
   - **Schema**: `ticker`, `timeframe`, `timestamp`, `open`, `high`, `low`, `close`, `volume`
   - **Behavior**: Only uploads new data (after latest timestamp in database)
   - **Status**: ✅ **COMPLETE** - Fully integrated into service workflow
   - **Configuration**: `ENABLE_LOCAL_DB=true` in `.env`

4. **Cloud Storage Upload** (Integrated in `service.py` + `gcs_uploader.py`)
   - **BigQuery Upload**: Integrated in `service.py`
     - **Purpose**: Upload processed data to Google Cloud BigQuery
     - **Tables**: Separate for daily and intraday data
     - **Behavior**: Only uploads new data (after latest date in BigQuery)
     - **Status**: ✅ **COMPLETE** - Fully integrated
     - **Configuration**: `ENABLE_BIGQUERY=true` in `.env`
   
   - **GCS Parquet Upload**: `dataHandler/gcs_uploader.py`
     - **Purpose**: Upload processed data as Parquet files to Google Cloud Storage
     - **Structure**: `gs://bucket-name/data/YYYY/MM/DD/ticker_timeframe.parquet`
     - **Behavior**: Only uploads new data (tracked via metadata)
     - **Status**: ✅ **COMPLETE** - Fully implemented
     - **Configuration**: `ENABLE_GCS=true` and `STORAGE_MODE=parquet` or `both` in `.env`

## Implementation Status

### ✅ Priority 1: Complete Automated Workflow - **COMPLETE**

**Status**: ✅ **FULLY IMPLEMENTED**

- ✅ Local DB upload integrated into `service.py` workflow
- ✅ Proper error handling between steps (one failure doesn't stop pipeline)
- ✅ Local DB credentials configurable via `.env`
- ✅ Complete workflow: collection → quality checks → local DB → cloud storage
- ✅ Optional components (controlled by environment variables)
- ✅ Docker removed - service-based architecture for micro VMs

**Implementation Details**:
- Service orchestrates all steps in `service.py`
- Local DB upload runs after data collection
- Error handling ensures one failure doesn't stop the entire pipeline
- All components are optional and controlled by environment variables

### ✅ Priority 2: Cloud Storage Options - **COMPLETE**

**Status**: ✅ **FULLY IMPLEMENTED**

- ✅ Configuration option to choose between BigQuery, Parquet, or both
- ✅ Parquet file export functionality implemented (`gcs_uploader.py`)
- ✅ Date-partitioned GCS bucket structure: `gs://bucket-name/data/YYYY/MM/DD/ticker_timeframe.parquet`
- ✅ Incremental upload logic (only new data)
- ✅ Configuration in `.env` file with `STORAGE_MODE`, `GCS_BUCKET_NAME`, `GCS_BUCKET_PATH`

**Implementation Details**:
- Uses `pyarrow` for Parquet file creation
- Date partitioning for better query performance
- Metadata tracking to avoid duplicate uploads
- Compatible with both BigQuery and Parquet storage methods

### ✅ Priority 3: Data Quality Monitoring - **COMPLETE**

**Status**: ✅ **FULLY IMPLEMENTED**

- ✅ Data quality monitoring module (`dataHandler/data_quality_monitor.py`)
- ✅ Visual candlestick chart generation using Plotly
- ✅ Detects all required data issues:
  - ✅ Missing data points (gaps in time series)
  - ✅ Outlier detection (unusual price movements using Z-score)
  - ✅ Volume anomalies (zero or negative volume)
  - ✅ Price inconsistencies (high < low, close outside high/low range)
  - ✅ Duplicate timestamps
- ✅ HTML report generation with charts and statistics
- ✅ Reports saved to `logs/quality_reports/` directory

**Implementation Details**:
- Uses Plotly for interactive candlestick charts
- Includes volume bars in charts
- Generates charts for each ticker/timeframe combination
- Saves charts as HTML files for easy viewing
- Creates summary report with statistics and issue details

### ✅ Priority 4: Enhanced Error Handling and Logging - **COMPLETE**

**Status**: ✅ **FULLY IMPLEMENTED**

- ✅ Comprehensive error handling throughout the pipeline
- ✅ Structured logging with different log levels (DEBUG, INFO, WARNING, ERROR)
- ✅ Execution summary report at end of each run
- ✅ Error handling ensures one failure doesn't stop the entire pipeline
- ✅ Timestamped log files in `logs/` directory

**Implementation Details**:
- Logging configured via `LOG_LEVEL` environment variable
- Each step logs its progress and errors
- Final summary shows success/failure for each step
- Errors are logged with full stack traces for debugging

### ✅ Priority 5: Configuration and Environment Management - **COMPLETE**

**Status**: ✅ **FULLY IMPLEMENTED**

- ✅ Comprehensive `.env.example` with all required variables
- ✅ Configuration validation script (`validate_config.py`)
- ✅ All configuration options documented in README
- ✅ Environment-based configuration (no hardcoded values)
- ✅ Support for optional features via environment variables

**Implementation Details**:
- `.env.example` includes all configuration options with examples
- `validate_config.py` validates configuration before service runs
- All features are optional and controlled by environment variables
- No hardcoded credentials or paths

## Current File Structure

```
yfin_data_collect/
├── service.py                        # Main service orchestration script
├── main.py                           # Legacy data collection script (used by service.py)
├── validate_config.py                # Configuration validation script
├── run_service.sh                    # Convenience script to run service
├── .env.example                      # Environment variables template
├── ticker.json                       # Ticker configuration
├── requirements.txt                  # Python dependencies
├── README.md                         # Complete documentation
├── CHANGELOG.md                      # Version history
├── GEMINI.md                         # This file
│
├── dataHandler/                      # Data collection and processing handlers
│   ├── DailyDataHandler.py          # Daily data collection
│   ├── IntradayDataHandler.py       # Intraday data collection
│   ├── backfill_combined_csv_local.py  # Legacy local DB upload (integrated in service.py)
│   ├── combine_transf_csv_for_upload.py  # Legacy BigQuery upload (integrated in service.py)
│   ├── data_quality_monitor.py      # ✅ NEW: Data quality monitoring
│   └── gcs_uploader.py              # ✅ NEW: GCS Parquet uploader
│
├── all_ohclv_data/                   # Collected data storage
│   ├── fetched_data/                # Raw fetched data
│   ├── process_data/                # Processed data
│   ├── transf_data/                 # Final transformed data (used for uploads)
│   └── ...
│
└── logs/                             # Log files
    ├── service_*.log                 # Service execution logs
    └── quality_reports/              # ✅ NEW: Quality check reports
        ├── quality_report_*.html     # Summary reports
        └── *_chart.html              # Individual ticker charts
```

## Environment Variables

### Required Configuration

All configuration is done via environment variables in `.env` file. See `.env.example` for complete template.

**General**:
- `TZ=UTC` - Timezone (default: UTC)
- `LOG_LEVEL=INFO` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `BASE_FOLDER=all_ohclv_data` - Base folder for data storage

**Local PostgreSQL** (Optional):
- `ENABLE_LOCAL_DB=false` - Enable/disable local DB upload
- `DB_NAME` - Database name (required if ENABLE_LOCAL_DB=true)
- `DB_USER` - Database user (required if ENABLE_LOCAL_DB=true)
- `DB_PASSWORD` - Database password (required if ENABLE_LOCAL_DB=true)
- `DB_HOST=localhost` - Database host (default: localhost)
- `DB_PORT=5432` - Database port (default: 5432)

**Google Cloud BigQuery** (Optional):
- `ENABLE_BIGQUERY=false` - Enable/disable BigQuery upload
- `daily_datset_bq` - Daily BigQuery table ID (format: project.dataset.table)
- `intraday_dataset_bq` - Intraday BigQuery table ID
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to GCP service account JSON

**Google Cloud Storage** (Optional):
- `STORAGE_MODE=bigquery` - Storage mode: bigquery, parquet, or both
- `ENABLE_GCS=false` - Enable/disable GCS Parquet upload
- `GCS_BUCKET_NAME` - GCS bucket name (required if ENABLE_GCS=true)
- `GCS_BUCKET_PATH=data` - GCS bucket path prefix (default: data)

**Data Quality Monitoring** (Optional):
- `ENABLE_QUALITY_CHECKS=true` - Enable/disable quality monitoring
- `QUALITY_REPORT_PATH=logs/quality_reports` - Path for quality reports

## Running the Service

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# 3. Validate configuration
python validate_config.py

# 4. Run service
python service.py
# or
./run_service.sh
```

### Automated Scheduling

Use cron to schedule the service:

```bash
# Edit crontab
crontab -e

# Add schedule (example: every day at 6:00 AM)
0 6 * * * cd /path/to/yfin_data_collect && /path/to/venv/bin/python service.py >> /path/to/yfin-cron.log 2>&1
```

## Development Guidelines

### Before Making Changes

1. **Create a new Git branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Test locally**:
   - Test data collection with a small subset of tickers
   - Verify local database upload works
   - Verify BigQuery upload works
   - Test GCS Parquet upload
   - Test data quality monitoring

3. **Update service workflow**:
   - Ensure `service.py` includes all new steps
   - Test service runs end-to-end
   - Verify error handling works correctly

4. **Documentation**:
   - Update README.md with new features
   - Add examples of new configuration options
   - Document any new dependencies
   - Update this file (GEMINI.md) if architecture changes

### Testing Checklist

Before submitting changes, verify:
- [ ] Data collection works for all ticker types (stocks, indices, forex, commodities, crypto)
- [ ] Local database upload completes successfully (if enabled)
- [ ] BigQuery upload completes successfully (if enabled)
- [ ] GCS Parquet upload completes successfully (if enabled)
- [ ] Data quality monitoring generates reports (if enabled)
- [ ] Service runs end-to-end workflow successfully
- [ ] All environment variables are properly documented
- [ ] No hardcoded credentials or paths
- [ ] Error handling works for common failure scenarios
- [ ] Configuration validation works correctly

## Notes for AI Agents

When implementing improvements or understanding the system:

1. **Architecture**: Service-based (no Docker) - runs directly with Python
2. **Main Entry Point**: `service.py` orchestrates the complete workflow
3. **Configuration**: All settings via `.env` file (see `.env.example`)
4. **Error Handling**: One failure doesn't stop the entire pipeline
5. **Optional Components**: All features are optional and controlled by environment variables
6. **Logging**: Structured logging with configurable levels
7. **Incremental Uploads**: Only new data is uploaded to avoid duplicates
8. **Quality Monitoring**: Automated checks with visual reports
9. **Storage Options**: Local DB, BigQuery, and/or GCS Parquet (all optional)
10. **Read existing code** to understand patterns and conventions
11. **Maintain consistency** with existing code style
12. **Use environment variables** for all configuration - no hardcoded values
13. **Add logging** at appropriate levels (INFO, WARNING, ERROR)
14. **Test incrementally** - don't make all changes at once
15. **Update documentation** as you add features

## Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Data Collection (`main.py`) | ✅ Complete | Works for all ticker types |
| Service Orchestration (`service.py`) | ✅ Complete | Orchestrates complete workflow |
| Local DB Upload | ✅ Complete | Integrated in service workflow |
| BigQuery Upload | ✅ Complete | Integrated in service workflow |
| GCS Parquet Upload | ✅ Complete | Fully implemented with date partitioning |
| Data Quality Monitoring | ✅ Complete | Full implementation with visual charts |
| Error Handling & Logging | ✅ Complete | Comprehensive error handling |
| Configuration Management | ✅ Complete | `.env.example` and validation script |
| Docker Setup | ❌ Removed | Replaced with service-based architecture |

## Future Enhancements (Lower Priority)

- [ ] Real-time data streaming capabilities
- [ ] Support for additional data sources beyond Yahoo Finance
- [ ] Data retention policies and archival
- [ ] Performance optimization (parallel processing)
- [ ] Web dashboard for monitoring and configuration
- [ ] API endpoints for querying collected data
- [ ] Machine learning integration for anomaly detection
- [ ] Email/Slack notifications for data quality issues
- [ ] Retry logic for API calls and uploads
- [ ] Success/failure rate tracking per ticker

---

**Last Updated**: 2025-01-XX  
**Version**: 2.0 (Service-based, no Docker)  
**Maintainer**: Project Owner  
**Questions?**: Refer to README.md or code comments
