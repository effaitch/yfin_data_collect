# Automated Data Collection Cron Job Setup

This project can run automatically on a schedule via a cron job.

## Quick Reference - Crontab Entries

Choose one of these cron schedules based on your needs:

```cron
# Run every Saturday at 2:00 AM
0 2 * * 6 /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1

# Run every Sunday at 2:00 AM
0 2 * * 0 /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1

# Run both Saturday AND Sunday at 2:00 AM
0 2 * * 0,6 /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1

# Run every Friday at 11:00 PM (end of week)
0 23 * * 5 /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1

# Run daily at 6:00 AM
0 6 * * * /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1
```

**Cron schedule format:**
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday=0 or 7)
│ │ │ │ │
* * * * *
```

## Architecture

The service runs 4 scripts in sequence:
1. **main.py** - Collects daily and intraday data from Yahoo Finance
2. **src/data_quality_monitor.py** - Runs quality checks and generates reports
3. **src/combine_transf_csv_for_upload.py** - Uploads to BigQuery
4. **src/backfill_combined_csv_local.py** - Uploads to local PostgreSQL database

## Setup Instructions

### 1. Make the script executable
```bash
chmod +x /home/farq/projects/yfin_data_collect/run_weekend_job.sh
```

### 2. Configure environment variables
Ensure your `.env` file has the following:
```bash
# Enable/disable features
ENABLE_BIGQUERY=true        # Set to 'false' to skip BigQuery upload
ENABLE_LOCAL_DB=true        # Set to 'false' to skip local DB upload
ENABLE_QUALITY_CHECKS=true  # Set to 'false' to skip quality checks

# BigQuery configuration (if ENABLE_BIGQUERY=true)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
daily_datset_bq=your-project.dataset.daily_table
intraday_dataset_bq=your-project.dataset.intraday_table

# PostgreSQL configuration (if ENABLE_LOCAL_DB=true)
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Optional
LOG_LEVEL=INFO
BASE_FOLDER=all_ohclv_data
QUALITY_REPORT_PATH=logs/quality_reports
```

### 3. Install the cron job

Edit your crontab:
```bash
crontab -e
```

Add one of the following lines:

**Run every Saturday at 2:00 AM:**
```cron
0 2 * * 6 /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1
```

**Run every Sunday at 2:00 AM:**
```cron
0 2 * * 0 /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1
```

**Run both Saturday AND Sunday at 2:00 AM:**
```cron
0 2 * * 0,6 /home/farq/projects/yfin_data_collect/run_weekend_job.sh >> /home/farq/projects/yfin_data_collect/logs/cron_output.log 2>&1
```

### 4. Verify the cron job is installed
```bash
crontab -l
```

## Manual Testing

Test the service manually before setting up the cron job:
```bash
# Activate venv and run service
cd /home/farq/projects/yfin_data_collect
source venv/bin/activate
python service.py
```

Or use the shell script:
```bash
./run_weekend_job.sh
```

## Logs

Logs are stored in two places:
1. **Service logs**: `logs/service_YYYYMMDD_HHMMSS.log` - Detailed timestamped logs for each run
2. **Cron output**: `logs/cron_output.log` - Standard output/errors from the cron job

## Monitoring

Check if the cron job ran successfully:
```bash
# View latest service log
ls -lt logs/service_*.log | head -1 | xargs cat

# View cron output
tail -f logs/cron_output.log

# Check cron job history
grep CRON /var/log/syslog
```

## Troubleshooting

### Cron job not running
- Verify cron service is running: `sudo systemctl status cron`
- Check crontab is installed: `crontab -l`
- Check system logs: `grep CRON /var/log/syslog`

### Script fails in cron but works manually
- Ensure paths are absolute in the cron command
- Check that `.env` file exists and is readable
- Verify virtual environment path in `run_weekend_job.sh`

### Data not uploading
- Check environment variables in `.env`
- Verify credentials for BigQuery/PostgreSQL
- Review logs in `logs/service_*.log`

## Workflow Summary

When the cron job runs, it will:
1. ✓ Activate the virtual environment
2. ✓ Run `service.py` which orchestrates all 4 scripts
3. ✓ Log everything to timestamped files
4. ✓ Exit with appropriate status codes

The service is fault-tolerant: if quality checks or uploads fail, the pipeline continues and logs warnings rather than aborting.
