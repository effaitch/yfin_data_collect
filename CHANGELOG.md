# Changelog

## Version 2.0 - Service-Based Architecture (2025-01-XX)

### Major Changes

- **Removed Docker Setup**: Removed all Docker-related files (Dockerfile, docker-compose.yml, docker-entrypoint.sh, run-docker.sh)
- **New Service Architecture**: Created `service.py` as the main orchestration script
- **Lightweight Design**: Optimized for small micro VMs without Docker overhead

### New Features

#### Priority 1: Complete Automated Workflow ✅
- Integrated local PostgreSQL database upload into the main workflow
- Service now runs: Data Collection → Quality Checks → Local DB Upload → Cloud Storage Upload
- Local DB upload is optional and controlled by `ENABLE_LOCAL_DB` environment variable

#### Priority 2: Cloud Storage Options ✅
- Added Google Cloud Storage (GCS) Parquet file upload support
- New `gcs_uploader.py` module for Parquet file creation and GCS upload
- Date-partitioned storage structure: `gs://bucket/data/YYYY/MM/DD/ticker_timeframe.parquet`
- Configurable storage mode: `bigquery`, `parquet`, or `both`
- Incremental uploads (only new data)

#### Priority 3: Data Quality Monitoring ✅
- New `data_quality_monitor.py` module for automated quality checks
- Detects:
  - Missing values
  - Duplicate timestamps
  - Price inconsistencies (high < low, close outside range)
  - Volume anomalies (zero/negative volume)
  - Outliers using Z-score analysis
  - Time series gaps
- Generates visual candlestick charts with Plotly
- Creates HTML reports with statistics and issue details
- Reports saved to `logs/quality_reports/`

#### Priority 4: Enhanced Error Handling and Logging ✅
- Structured logging with different log levels (DEBUG, INFO, WARNING, ERROR)
- Comprehensive error handling throughout the pipeline
- Errors in one step don't stop the entire pipeline
- Timestamped log files in `logs/` directory
- Execution summary report at the end of each run

#### Priority 5: Configuration and Environment Management ✅
- Created `.env.example` with all configuration options
- New `validate_config.py` script for configuration validation
- Environment-based configuration (no hardcoded values)
- Support for optional features (local DB, BigQuery, GCS, quality checks)

### New Files

- `service.py` - Main service orchestration script
- `dataHandler/data_quality_monitor.py` - Data quality monitoring module
- `dataHandler/gcs_uploader.py` - GCS Parquet uploader module
- `validate_config.py` - Configuration validation script
- `.env.example` - Environment variables template
- `run_service.sh` - Convenience script to run the service
- `CHANGELOG.md` - This file

### Updated Files

- `README.md` - Complete rewrite for service-based setup (no Docker)
- `requirements.txt` - Added `google-cloud-storage` dependency

### Removed Files

- `Dockerfile` - No longer needed
- `docker-compose.yml` - No longer needed
- `docker-entrypoint.sh` - No longer needed
- `run-docker.sh` - No longer needed

### Configuration Changes

New environment variables:
- `ENABLE_LOCAL_DB` - Enable/disable local PostgreSQL upload
- `ENABLE_BIGQUERY` - Enable/disable BigQuery upload
- `ENABLE_GCS` - Enable/disable GCS Parquet upload
- `STORAGE_MODE` - Storage mode: `bigquery`, `parquet`, or `both`
- `GCS_BUCKET_NAME` - GCS bucket name
- `GCS_BUCKET_PATH` - GCS bucket path prefix
- `ENABLE_QUALITY_CHECKS` - Enable/disable quality monitoring
- `QUALITY_REPORT_PATH` - Path for quality reports
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `BASE_FOLDER` - Base folder for data storage

### Migration Guide

If you were using Docker:

1. Remove Docker setup:
   ```bash
   # Docker files are already removed
   ```

2. Set up Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your settings
   ```

4. Validate configuration:
   ```bash
   python validate_config.py
   ```

5. Run service:
   ```bash
   python service.py
   # or
   ./run_service.sh
   ```

6. Update cron jobs:
   ```cron
   # Old (Docker)
   0 6 * * * cd /path/to/project && docker-compose up
   
   # New (Service)
   0 6 * * * cd /path/to/project && /path/to/venv/bin/python service.py
   ```

### Breaking Changes

- Docker support removed - must use Python directly
- Service workflow changed - now uses `service.py` instead of `main.py` + separate upload scripts
- Configuration moved to environment variables (`.env` file)

### Performance Improvements

- Optimized for small micro VMs (no Docker overhead)
- Incremental uploads (only new data)
- Efficient Parquet compression
- Optional components (disable unused features)

### Known Issues

- None at this time

### Future Enhancements

See `GEMINI.md` for the complete roadmap.

