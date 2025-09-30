# Yahoo Finance Data Collection Project

A comprehensive Python project for automated collection, processing, and storage of financial market data using the Yahoo Finance API. This project supports both daily and intraday data collection with SQL database integration.

## Features

- **Automated Data Collection**: Fetch OHLCV data for stocks, indices, forex, commodities, and cryptocurrencies
- **Multiple Timeframes**: Support for daily and intraday data (1m, 5m, 15m, 30m, 1h, 90m)
- **Data Processing Pipeline**: Clean, transform, and organize collected data
- **SQL Database Integration**: Import processed data into PostgreSQL database
- **Comprehensive Logging**: Detailed logging with timestamped log files
- **Flexible Configuration**: JSON-based ticker configuration

## Project Structure

```
yfin_data_collect/
├── dataHandler/                 # Data collection handlers
│   ├── DailyDataHandler.py     # Daily data collection
│   └── IntradayDataHandler.py  # Intraday data collection
├── sql_import/                 # SQL database import utilities
│   ├── insert_data_yfin_sql.py # Main SQL import script
│   ├── db_utils.py            # Database utilities
│   └── ...                     # Additional SQL tools
├── all_ohclv_data/            # Collected data storage
│   ├── fetched_data/          # Raw fetched data
│   ├── process_data/          # Processed data
│   ├── transf_data/           # Final transformed data
│   └── ...                    # Additional data folders
├── logs/                      # Log files with timestamps
├── main.py                    # Main execution script
├── ticker.json               # Ticker configuration
└── requirements.txt          # Python dependencies
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/effaitch/yfin_data_collect.git
   cd yfin_data_collect
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure tickers**:
   Edit `ticker.json` to specify which assets you want to collect data for:
   ```json
   {
     "stocks": ["AAPL", "MSFT", "GOOGL"],
     "indices": ["^GSPC", "^DJI", "^IXIC"],
     "forex": ["EURUSD=X", "GBPUSD=X"],
     "commodities": ["GC=F", "CL=F"],
     "crypto": ["BTC-USD", "ETH-USD"]
   }
   ```

## Usage

### Basic Data Collection

Run the main script to collect both daily and intraday data:

```bash
python main.py
```

This will:
- Read tickers from `ticker.json`
- Collect daily data for all specified tickers
- Collect intraday data for all specified tickers
- Process and store data in organized folders
- Generate timestamped log files in `/logs` folder

### Individual Data Collection

**Daily Data Only**:
```python
from dataHandler.DailyDataHandler import DailyDataHandler
import json

with open("ticker.json", "r") as f:
    ticker_dict = json.load(f)

tickers = []
for key in ticker_dict:
    tickers.extend(ticker_dict[key])

handler = DailyDataHandler(tickers, "all_ohclv_data")
handler.update_all()
```

**Intraday Data Only**:
```python
from dataHandler.IntradayDataHandler import IntradayDataHandler
import json

with open("ticker.json", "r") as f:
    ticker_dict = json.load(f)

tickers = []
for key in ticker_dict:
    tickers.extend(ticker_dict[key])

handler = IntradayDataHandler(tickers, "all_ohclv_data")
handler.update_all()
```

### SQL Database Import

To import collected data into a PostgreSQL database:

1. **Set up database credentials** in `.env.tradingdb`:
   ```
   DATABASE_HOST=your_host
   DATABASE_NAME=your_database
   DATABASE_USER=your_username
   DATABASE_PASSWORD=your_password
   ```

2. **Run the SQL import script**:
   ```bash
   python sql_import/insert_data_yfin_sql.py
   ```

   This will:
   - Read CSV files from `all_ohclv_data/transf_data/`
   - Clean and format the data
   - Import into the `yfin` table with the following schema:
     - `ticker` (TEXT) - Asset symbol
     - `timeframe` (TEXT) - Time interval (1d, 1h, 5m, etc.)
     - `timestamp` (TIMESTAMPTZ) - Candle start time
     - `open`, `high`, `low`, `close`, `volume` (DOUBLE PRECISION)

## Data Organization

The project uses a structured folder system:

- **`fetched_data/`**: Raw data directly from Yahoo Finance API
- **`raw_intraday/`**: Processed raw data for intraday timeframes
- **`process_data/`**: Newly processed data
- **`transf_data/`**: Final transformed data ready for database import
- **`logs/`**: Timestamped log files (format: `handler_name_YYYYMMDD_HHMMSS.log`)

## Configuration

### Supported Assets
- **Stocks**: AAPL, MSFT, GOOGL, TSLA, etc.
- **Indices**: ^GSPC (S&P 500), ^DJI (Dow Jones), ^IXIC (NASDAQ)
- **Forex**: EURUSD=X, GBPUSD=X, JPY=X
- **Commodities**: GC=F (Gold), CL=F (Crude Oil), NG=F (Natural Gas)
- **Cryptocurrencies**: BTC-USD, ETH-USD, ADA-USD

### Supported Timeframes
- **Daily**: 1d
- **Intraday**: 1m, 5m, 15m, 30m, 1h, 90m

## Logging

The project generates detailed logs with timestamps:
- Log files are stored in `/logs` folder
- Each run creates a new log file with current datetime
- Logs include data collection progress, errors, and statistics

## Database Schema

The SQL database uses the following schema for the `yfin` table:

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

## Future Enhancements

- [ ] Automated weekly data collection scheduling
- [ ] Data retention policies for older data
- [ ] Optimized data processing pipeline
- [ ] BigQuery integration for cloud storage
- [ ] Real-time data streaming capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.