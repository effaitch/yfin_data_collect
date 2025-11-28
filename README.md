# Yahoo Finance Data Collection Service

A lightweight Python service for automated collection, processing, and storage of financial market data using the Yahoo Finance API. Designed to run efficiently on small micro VMs without Docker overhead.

## Features

- **Automated Data Collection**: Fetch OHLCV data for stocks, indices, forex, commodities, and cryptocurrencies
- **Multiple Timeframes**: Support for daily and intraday data (1m, 5m, 15m, 30m, 1h, 90m)
- **Data Processing Pipeline**: Clean, transform, and organize collected data
- **Multiple Storage Options**:
  - Local PostgreSQL database
  - Google Cloud BigQuery tables
  - Google Cloud Storage Parquet files
- **Data Quality Monitoring**: Automated quality checks with visual candlestick charts
- **Comprehensive Logging**: Structured logging with timestamped log files
- **Flexible Configuration**: Environment-based configuration
- **Lightweight**: Optimized for small micro VMs (no Docker required)

## Project Structure

```
yfin_data_collect/
├── dataHandler/                      # Data collection and processing handlers
│   ├── DailyDataHandler.py          # Daily data collection
│   ├── IntradayDataHandler.py       # Intraday data collection
│   ├── backfill_combined_csv_local.py  # Local DB upload (legacy)
│   ├── combine_transf_csv_for_upload.py # BigQuery upload (legacy)
│   ├── data_quality_monitor.py      # Data quality monitoring
│   └── gcs_uploader.py              # GCS Parquet uploader
├── all_ohclv_data/                  # Collected data storage
│   ├── fetched_data/                # Raw fetched data
│   ├── process_data/                 # Processed data
│   ├── transf_data/                 # Final transformed data
│   └── ...
├── logs/                             # Log files
│   └── quality_reports/             # Quality check reports
├── service.py                        # Main service script
├── main.py                           # Legacy main script
├── validate_config.py                # Configuration validation
├── ticker.json                       # Ticker configuration
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
└── README.md                         # This file
```

## Quick Start

### 1. Installation on Micro VM

```bash
# Clone the repository
git clone https://github.com/effaitch/yfin_data_collect.git
cd yfin_data_collect

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Minimum Configuration** (for local data collection only):
```bash
TZ=UTC
LOG_LEVEL=INFO
ENABLE_QUALITY_CHECKS=true
```

**With Local PostgreSQL**:
```bash
ENABLE_LOCAL_DB=true
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

**With Google Cloud BigQuery**:
```bash
ENABLE_BIGQUERY=true
daily_datset_bq=project.dataset.daily_table
intraday_dataset_bq=project.dataset.intraday_table
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**With Google Cloud Storage (Parquet)**:
```bash
STORAGE_MODE=parquet  # or "both" for BigQuery + Parquet
ENABLE_GCS=true
GCS_BUCKET_NAME=your-bucket-name
GCS_BUCKET_PATH=data
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### 3. Configure Tickers

Edit `ticker.json` to specify which assets to collect:

```json
{
  "mag7_tickers": ["AAPL", "TSLA", "MSFT", "AMZN", "GOOG", "META", "NVDA"],
  "portfolio_tickers": ["MRNA", "PFE", "BNTX", "LLY", "PYPL", "AMD"],
  "index_tickers": ["^GSPC", "^VIX", "^DJI", "^IXIC"],
  "commod_tickers": ["CL=F", "GC=F", "NG=F"],
  "curren_tickers": ["GBPUSD=X", "EURUSD=X"],
  "crypt_tickers": ["BTC-USD", "ETH-USD"]
}
```

### 4. Validate Configuration

```bash
python validate_config.py
```

### 5. Run the Service

```bash
# Run once
python service.py

# Or make it executable and run directly
chmod +x service.py
./service.py
```

## Automated Scheduling with Cron

To run the service automatically on a schedule:

```bash
# Edit crontab
crontab -e

# Add schedule (example: every day at 6:00 AM)
0 6 * * * cd /home/user/yfin_data_collect && /home/user/yfin_data_collect/venv/bin/python service.py >> /home/user/yfin-cron.log 2>&1

# Or if using system Python
0 6 * * * cd /home/user/yfin_data_collect && python3 service.py >> /home/user/yfin-cron.log 2>&1
```

**Common Cron Schedules**:
```cron
# Every day at 6:00 AM
0 6 * * * cd /path/to/yfin_data_collect && python3 service.py

# Every Saturday at 9:00 AM
0 9 * * 6 cd /path/to/yfin_data_collect && python3 service.py

# Every Monday and Friday at 8:00 AM
0 8 * * 1,5 cd /path/to/yfin_data_collect && python3 service.py

# Every hour during market hours (9 AM - 4 PM EST, weekdays)
0 9-16 * * 1-5 cd /path/to/yfin_data_collect && python3 service.py
```

## Service Workflow

The service (`service.py`) orchestrates the complete workflow:

1. **Data Collection**: Fetches daily and intraday data from Yahoo Finance
2. **Quality Checks**: Runs data quality monitoring (if enabled)
3. **Local DB Upload**: Uploads to PostgreSQL (if enabled)
4. **Cloud Storage Upload**: Uploads to BigQuery and/or GCS (if enabled)

Each step is logged with timestamps and error handling ensures one failure doesn't stop the entire pipeline.

## Configuration Options

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TZ` | Timezone | No | UTC |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |
| `BASE_FOLDER` | Base folder for data storage | No | all_ohclv_data |
| `ENABLE_LOCAL_DB` | Enable local PostgreSQL upload | No | false |
| `DB_NAME` | PostgreSQL database name | If ENABLE_LOCAL_DB=true | - |
| `DB_USER` | PostgreSQL user | If ENABLE_LOCAL_DB=true | - |
| `DB_PASSWORD` | PostgreSQL password | If ENABLE_LOCAL_DB=true | - |
| `DB_HOST` | PostgreSQL host | No | localhost |
| `DB_PORT` | PostgreSQL port | No | 5432 |
| `ENABLE_BIGQUERY` | Enable BigQuery upload | No | false |
| `daily_datset_bq` | BigQuery daily table ID | If ENABLE_BIGQUERY=true | - |
| `intraday_dataset_bq` | BigQuery intraday table ID | If ENABLE_BIGQUERY=true | - |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP service account JSON path | For GCP services | - |
| `STORAGE_MODE` | Storage mode: bigquery, parquet, both | No | bigquery |
| `ENABLE_GCS` | Enable GCS Parquet upload | No | false |
| `GCS_BUCKET_NAME` | GCS bucket name | If ENABLE_GCS=true | - |
| `GCS_BUCKET_PATH` | GCS bucket path prefix | No | data |
| `ENABLE_QUALITY_CHECKS` | Enable data quality monitoring | No | true |
| `QUALITY_REPORT_PATH` | Path for quality reports | No | logs/quality_reports |

## Data Quality Monitoring

The service includes automated data quality monitoring that:

- Detects missing values
- Identifies duplicate timestamps
- Checks price consistency (high >= low, close within range)
- Detects volume anomalies (zero/negative volume)
- Identifies outliers using Z-score analysis
- Detects gaps in time series
- Generates visual candlestick charts with volume bars
- Creates HTML reports with statistics

Quality reports are saved to `logs/quality_reports/` and include:
- Summary statistics
- File-by-file results
- Issue details
- Interactive charts (if Plotly is available)

## Storage Options

### Local PostgreSQL

The service uploads data to a local PostgreSQL database with the following schema:

```sql
CREATE TABLE yfin (
    ticker TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    PRIMARY KEY (ticker, timeframe, timestamp)
);
```

Only new data (after the latest timestamp) is uploaded to avoid duplicates.

### Google Cloud BigQuery

Data is uploaded to separate BigQuery tables for daily and intraday data:
- Daily data: `daily_datset_bq` table
- Intraday data: `intraday_dataset_bq` table

Only new data (after the latest date) is uploaded.

### Google Cloud Storage (Parquet)

Data is exported as Parquet files and uploaded to GCS with date partitioning:
```
gs://bucket-name/data/YYYY/MM/DD/ticker_timeframe.parquet
```

Parquet files are compressed with Snappy compression for efficient storage.

## Monitoring and Logs

### View Service Logs

```bash
# View latest service log
ls -t logs/service_*.log | head -1 | xargs tail -f

# View all logs
ls -lh logs/

# Search logs for errors
grep -i error logs/service_*.log
```

### View Quality Reports

```bash
# List quality reports
ls -lh logs/quality_reports/

# Open latest report in browser
ls -t logs/quality_reports/quality_report_*.html | head -1 | xargs xdg-open
```

### Check Cron Execution

```bash
# View cron log
tail -f ~/yfin-cron.log

# Check cron job status
crontab -l
```

## Troubleshooting

### Service Won't Start

```bash
# Validate configuration
python validate_config.py

# Check Python version (requires 3.8+)
python3 --version

# Check dependencies
pip list | grep -E "pandas|yfinance|psycopg2|google-cloud"
```

### Data Collection Fails

- Check internet connectivity
- Verify ticker symbols are valid
- Check Yahoo Finance API rate limits
- Review logs for specific error messages

### Database Upload Fails

```bash
# Test database connection
psql -h localhost -U your_user -d your_database -c "SELECT 1;"

# Check if table exists
psql -h localhost -U your_user -d your_database -c "\d yfin"
```

### BigQuery/GCS Upload Fails

```bash
# Verify service account credentials
cat $GOOGLE_APPLICATION_CREDENTIALS | jq .project_id

# Test GCP authentication
gcloud auth application-default print-access-token

# Check BigQuery table exists
bq ls your-project:your_dataset
```

### Quality Checks Fail

- Ensure Plotly is installed: `pip install plotly`
- Check disk space for report generation
- Review logs for specific errors

## Performance Optimization for Micro VMs

The service is optimized for small micro VMs:

1. **Incremental Uploads**: Only new data is uploaded to avoid redundant transfers
2. **Efficient Storage**: Parquet files use compression
3. **Optional Components**: Disable unused features to save resources
4. **Lightweight Dependencies**: Minimal required packages
5. **Error Handling**: Failures don't crash the service

**Resource Recommendations**:
- **Minimum**: 1 CPU, 512MB RAM, 5GB disk
- **Recommended**: 1 CPU, 1GB RAM, 10GB disk
- **Optimal**: 2 CPU, 2GB RAM, 20GB disk

## Database Schema

### PostgreSQL (yfin table)

```sql
CREATE TABLE IF NOT EXISTS yfin (
    ticker TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    PRIMARY KEY (ticker, timeframe, timestamp)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_yfin_ticker_timeframe ON yfin(ticker, timeframe);
CREATE INDEX IF NOT EXISTS idx_yfin_timestamp ON yfin(timestamp);
```

## Supported Assets

- **Stocks**: AAPL, MSFT, GOOGL, TSLA, etc.
- **Indices**: ^GSPC (S&P 500), ^DJI (Dow Jones), ^VIX (Volatility Index)
- **Forex**: EURUSD=X, GBPUSD=X, JPY=X
- **Commodities**: GC=F (Gold), CL=F (Crude Oil), NG=F (Natural Gas)
- **Cryptocurrencies**: BTC-USD, ETH-USD, ADA-USD

## Supported Timeframes

- **Daily**: 1d
- **Intraday**: 1m, 5m, 15m, 30m, 1h, 90m

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Refer to `GEMINI.md` for project roadmap and improvement plans
- Check logs in `logs/` directory for detailed error messages

---

**Last Updated**: 2025-01-XX  
**Version**: 2.0 (Service-based, no Docker)
