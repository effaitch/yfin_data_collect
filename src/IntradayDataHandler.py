import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
import logging
import json
"""
LOGGING being appended to daily datahandelr 
when running main.py file

#""Get the current date and time to create a unique filename
log_filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Ensure the logs directory exists
log_dir = "./logs"
os.makedirs(log_dir, exist_ok=True)

#Construct the full path for the log file
log_filepath = os.path.join(log_dir, f"{log_filename}_intraday_data_handler.log")

# Configure logging using the generated filename
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filepath), # Use the variable here
        logging.StreamHandler()
    ]
)"""

class IntradayDataHandler:
    def __init__(self, tickers, base_folder):
        self.tickers = [ticker.upper() for ticker in tickers]
        self.base_folder = base_folder

        self.fetched_folder = os.path.join(base_folder, "fetched_data")
        self.raw_folder = os.path.join(base_folder, "raw_intraday")
        self.processed_folder = os.path.join(base_folder, "process_data")
        self.transf_folder = os.path.join(base_folder, "transf_data")

        os.makedirs(self.fetched_folder, exist_ok=True)
        os.makedirs(self.raw_folder, exist_ok=True)
        os.makedirs(self.processed_folder, exist_ok=True)
        os.makedirs(self.transf_folder, exist_ok=True)

        self.intraday_timeframes = ["1m", "5m", "15m", "30m", "90m", "1h"]

    def update_all(self):
        if self.needs_update():
            self.fetch_intraday_data()
            self.clean_fetched_data()
            self.check_new_datetime()
        else:
            logging.info("ℹ️ No update needed.")

    def needs_update(self):
        now = datetime.now(timezone.utc)

        for file in os.listdir(self.transf_folder):
            if not file.endswith('.parquet'):
                continue

            timeframe = file.replace('.parquet', '').split('_')[-1]
            if timeframe not in self.intraday_timeframes:
                continue

            path = os.path.join(self.transf_folder, file)

            try:
                df = pd.read_parquet(path)
                if df.empty:
                    logging.warning(f"⚠️ Empty file detected: {file}, update needed.")
                    return True

                # Parquet stores datetime objects directly, but let's ensure UTC and no tz for comparison if needed
                if 'Datetime' in df.columns:
                    df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True).dt.tz_convert(None)
                    latest = df['Datetime'].max()
                else:
                    # If it's indexed by Datetime
                    latest = df.index.max()
                    if isinstance(latest, pd.Timestamp):
                        latest = latest.tz_localize(timezone.utc).tz_convert(None) if latest.tzinfo else latest

                if pd.isna(latest):
                    logging.warning(f"⚠️ No valid datetime in {file}, update needed.")
                    return True

                if (now.replace(tzinfo=None) - latest).total_seconds() > 12 * 3600:
                    logging.warning(f"⚠️ Data in {file} is older than 12 hours, update needed.")
                    return True

            except Exception as e:
                logging.error(f"❌ Error checking {file}: {e}")
                return True

        logging.info("✅ All files are up-to-date (within 12 hours).")
        return False
    def fetch_intraday_data(self):
        # Define valid period per interval (based on yfinance limitations)
        interval_to_period = {
            "1m": "7d",     # Max for 1m
            "5m": "60d",
            "15m": "60d",
            "30m": "60d",
            "90m": "60d",
            "1h": "730d"    # Approx 2 years
        }
    
        for ticker in self.tickers:
            for tf in self.intraday_timeframes:
                period = interval_to_period.get(tf, "60d")  # Default to 60d if not found
                path = os.path.join(self.fetched_folder, f"{ticker}_{tf}.parquet")
                logging.info(f"🔄 Fetching {ticker} data for timeframe: {tf} (period: {period})...")
    
                try:
                    data = yf.download(ticker, interval=tf, period=period, auto_adjust=True)
                    if data.empty:
                        logging.warning(f"⚠️ No data for {ticker} ({tf})")
                        continue
    
                    # Flatten MultiIndex columns if present
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = [col[0] for col in data.columns]

                    data.reset_index(inplace=True)
                    data.rename(columns={data.columns[0]: "Datetime"}, inplace=True)
                    data.to_parquet(path, index=False)
                    logging.info(f"✅ Raw data for {ticker} ({tf}) saved to: {path}")
    
                except Exception as e:
                    logging.error(f"❌ Error fetching {ticker} ({tf}): {e}")

    def clean_fetched_data(self):
        nan_files = {}

        for file in os.listdir(self.fetched_folder):
            if not file.endswith('.parquet'):
                continue

            tf = file.replace('.parquet', '').split('_')[-1]
            if tf not in self.intraday_timeframes:
                continue

            fetch_path = os.path.join(self.fetched_folder, file)
            raw_path = os.path.join(self.raw_folder, file)

            try:
                df = pd.read_parquet(fetch_path)

                if df.empty:
                    logging.warning(f"⚠️ Skipping empty file: {file}")
                    continue

                # Flatten MultiIndex columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]

                # If first row is just tickers (legacy cleaning logic)
                ticker = file.split('_')[0]
                if df.iloc[0].astype(str).str.contains(ticker).any():
                    df = df.iloc[1:].reset_index(drop=True)

                if 'Datetime' not in df.columns:
                    if isinstance(df.index, pd.DatetimeIndex):
                         df.reset_index(inplace=True)
                         df.rename(columns={df.columns[0]: "Datetime"}, inplace=True)
                    else:
                        # Attempt to find it
                        possible_dt_cols = [c for c in df.columns if 'Datetime' in str(c) or 'Date' in str(c) or 'index' in str(c).lower()]
                        if possible_dt_cols:
                            df.rename(columns={possible_dt_cols[0]: "Datetime"}, inplace=True)
                        else:
                            logging.error(f"❌ Datetime column missing in {file}: {df.columns.tolist()}")
                            continue

                df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True).dt.tz_convert(None)
                df.dropna(subset=['Datetime'], inplace=True)
                df.set_index('Datetime', inplace=True)

                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                if df.isna().any().any():
                    nan_files[file] = df[df.isna().any(axis=1)]

                df.to_parquet(raw_path)
                logging.info(f"✅ Processed intraday data saved to: {raw_path}")

            except Exception as e:
                logging.error(f"❌ Error processing {file}: {e}")

        if nan_files:
            logging.warning("⚠️ Files with NaNs found:")
            for f, rows in nan_files.items():
                print(f"\n🔍 {f}\n{rows}")
        else:
            logging.info("✅ No missing intraday data found.")

    def check_new_datetime(self):
        for file in os.listdir(self.raw_folder):
            if not file.endswith('.parquet'):
                continue

            tf = file.replace('.parquet', '').split('_')[-1]
            if tf not in self.intraday_timeframes:
                continue

            raw_path = os.path.join(self.raw_folder, file)
            transf_path = os.path.join(self.transf_folder, file)
            processed_path = os.path.join(self.processed_folder, file)

            try:
                raw_df = pd.read_parquet(raw_path)
                # Ensure Datetime is index and has no TZ
                if 'Datetime' in raw_df.columns:
                    raw_df['Datetime'] = pd.to_datetime(raw_df['Datetime'], utc=True).dt.tz_convert(None)
                    raw_df.set_index('Datetime', inplace=True)
                else:
                    raw_df.index = pd.to_datetime(raw_df.index, utc=True).tz_convert(None)

                if not os.path.exists(transf_path):
                    raw_df.to_parquet(transf_path)
                    logging.info(f"✅ New master file created: {transf_path}")
                    continue

                transf_df = pd.read_parquet(transf_path)
                if 'Datetime' in transf_df.columns:
                    transf_df['Datetime'] = pd.to_datetime(transf_df['Datetime'], utc=True).dt.tz_convert(None)
                    transf_df.set_index('Datetime', inplace=True)
                else:
                    transf_df.index = pd.to_datetime(transf_df.index, utc=True).tz_convert(None)

                new_rows = raw_df.loc[~raw_df.index.isin(transf_df.index)]

                if not new_rows.empty:
                    new_rows.to_parquet(processed_path)
                    logging.info(f"✅ New data detected and saved to: {processed_path}")

                    combined = pd.concat([transf_df, new_rows])
                    combined = combined[~combined.index.duplicated(keep='first')]
                    combined.sort_index(inplace=True)
                    combined.to_parquet(transf_path)
                    logging.info(f"✅ Appended new data and updated: {transf_path}")
                else:
                    logging.info(f"ℹ️ No new data found for {file}.")

            except Exception as e:
                logging.error(f"❌ Error comparing/appending for {file}: {e}")



# Example Usage
if __name__ == "__main__":
    # Get the absolute path to ticker.json
    ticker_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ticker.json"))
    with open(ticker_json_path, "r") as f:
        ticker_dict = json.load(f)
    tickers = []
    for key in ticker_dict:
        tickers.extend(ticker_dict[key])

    base_folder = "./all_ohclv_data"
    intradayCollector = IntradayDataHandler(tickers, base_folder)
    intradayCollector.update_all()
