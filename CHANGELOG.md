# Changelog

## Version 3.0 - Weekend Cron Job Automation (2025-12-25)

### Major Changes

- **Automated Weekend Scheduling**: New cron job setup for automated weekend data collection
- **Simplified Cloud Storage**: Removed GCS Parquet upload, keeping only BigQuery for cloud storage
- **Refactored Service Script**: Complete rewrite of `service.py` to run scripts sequentially via subprocess

### New Features

#### Weekend Cron Job Automation ✅
- Created `run_weekend_job.sh` script that activates venv and runs service
- Automatic virtual environment activation handled by shell script
- Created `WEEKEND_CRON_SETUP.md` with complete setup instructions
- Created `CRON_SETUP.txt` with crontab examples
- Service runs all 4 scripts in sequence:
  1. `main.py` - Data collection
  2. `src/data_quality_monitor.py` - Quality checks
  3. `src/combine_transf_csv_for_upload.py` - BigQuery upload
  4. `src/backfill_combined_csv_local.py` - Local DB upload

#### Service Script Refactor ✅
- Complete rewrite of `service.py` to use subprocess for running scripts
- Better error handling and logging
- Each script runs independently with full output capture
- Non-critical failures don't stop the pipeline
- Comprehensive logging to timestamped files

#### Simplified Storage Options ✅
- Removed GCS Parquet upload functionality
- Removed `STORAGE_MODE` configuration
- Removed `ENABLE_GCS`, `GCS_BUCKET_NAME`, `GCS_BUCKET_PATH` environment variables
- Streamlined to just BigQuery and local PostgreSQL options

### Removed Features

- **GCS Parquet Upload**: Removed GCS/Parquet support (never implemented)
- **Storage Mode**: Removed `STORAGE_MODE` configuration option
- **GCS Configuration**: Removed all GCS-related environment variables

### Updated Files

- `service.py` - Complete rewrite for subprocess-based execution
- `validate_config.py` - Removed GCS/Parquet configuration checks
- `GEMINI.md` - Updated to reflect current project state and weekend automation
- `CHANGELOG.md` - This file

### New Files

- `run_weekend_job.sh` - Cron job wrapper script with venv activation
- `CRON_SETUP.md` - Complete cron job setup guide

### Configuration Changes

Removed environment variables:
- `STORAGE_MODE` - No longer needed (use ENABLE_BIGQUERY directly)
- `ENABLE_GCS` - GCS Parquet upload removed
- `GCS_BUCKET_NAME` - GCS Parquet upload removed
- `GCS_BUCKET_PATH` - GCS Parquet upload removed

Existing environment variables (unchanged):
- `ENABLE_LOCAL_DB` - Enable/disable local PostgreSQL upload
- `ENABLE_BIGQUERY` - Enable/disable BigQuery upload
- `ENABLE_QUALITY_CHECKS` - Enable/disable quality monitoring
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `BASE_FOLDER` - Base folder for data storage
- Database and BigQuery credentials

### Migration Guide from Version 2.0

If you were using GCS Parquet references:

1. Remove GCS configuration from `.env`:
   ```bash
   # Remove these lines if present:
   # ENABLE_GCS=true
   # STORAGE_MODE=parquet
   # GCS_BUCKET_NAME=your-bucket
   # GCS_BUCKET_PATH=data
   ```

2. Use BigQuery for cloud storage:
   ```bash
   ENABLE_BIGQUERY=true
   daily_datset_bq=your-project.dataset.daily_table
   intraday_dataset_bq=your-project.dataset.intraday_table
   ```

3. Set up weekend cron job:
   ```bash
   chmod +x /home/farq/projects/yfin_data_collect/run_weekend_job.sh
   crontab -e
   # Add: 0 2 * * 6 /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1
   ```

---

## Version 2.0 - Service-Based Architecture (2025-01-XX)

### Major Changes

- **Removed Docker Setup**: Removed all Docker-related files
- **New Service Architecture**: Created `service.py` as the main orchestration script
- **Lightweight Design**: Optimized for small micro VMs without Docker overhead

### New Features

#### Complete Automated Workflow ✅
- Integrated local PostgreSQL database upload into the main workflow
- Service runs: Data Collection → Quality Checks → BigQuery Upload → Local DB Upload
- All steps are optional and controlled by environment variables

#### Data Quality Monitoring ✅
- New `data_quality_monitor.py` module for automated quality checks
- Detects missing values, duplicates, price inconsistencies, volume anomalies, outliers
- Generates visual candlestick charts with Plotly
- Creates HTML reports with statistics
- Reports saved to `logs/quality_reports/`

#### Enhanced Error Handling and Logging ✅
- Structured logging with different log levels
- Comprehensive error handling throughout the pipeline
- Errors in one step don't stop the entire pipeline
- Timestamped log files

#### Configuration and Environment Management ✅
- Environment-based configuration (no hardcoded values)
- `validate_config.py` script for configuration validation
- Support for optional features

### New Files

- `service.py` - Main service orchestration script
- `src/data_quality_monitor.py` - Data quality monitoring module
- `validate_config.py` - Configuration validation script

### Removed Files

- Docker-related files (Dockerfile, docker-compose.yml, etc.)

---

## Version 1.0 - Initial Release

Initial project setup with Docker-based architecture.

