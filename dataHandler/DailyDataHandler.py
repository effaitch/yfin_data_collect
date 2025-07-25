import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
import logging
import json

# 1. Get the current date and time to create a unique filename
log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Ensure the logs directory exists
log_dir = "./logs"
os.makedirs(log_dir, exist_ok=True)

# 2. Construct the full path for the log file
log_filepath = os.path.join(log_dir, f"{log_filename}_daily_data_handler.log")

# 3. Configure logging using the generated filename
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filepath), # Use the variable here
        logging.StreamHandler()
    ]
)

class DailyDataHandler:
    def __init__(self, tickers, base_folder):
        # Ensure tickers are upper case
        self.tickers = [ticker.upper() for ticker in tickers]
        self.base_folder = base_folder

        # Define folder paths
        self.fetched_folder = os.path.join(base_folder, "fetched_data")
        self.raw_folder = os.path.join(base_folder, "raw_daily")
        self.processed_folder = os.path.join(base_folder, "process_data")
        self.transf_folder = os.path.join(base_folder, "transf_data")

        # Create directories if they don't exist
        os.makedirs(self.fetched_folder, exist_ok=True)
        os.makedirs(self.raw_folder, exist_ok=True)
        os.makedirs(self.processed_folder, exist_ok=True)
        os.makedirs(self.transf_folder, exist_ok=True)

    def update_all(self):
        # Check if update is needed, then fetch and clean data
        if self.needs_update():
            self.fetch_daily_data()
            self.clean_fetched_data()
            self.check_new_date()
        else:
            logging.info("ℹ️ No update needed.")

    def needs_update(self):
        # Current time in UTC
        now = datetime.now(timezone.utc)
        needs_update_flag = False

        # Loop through each ticker to check the files
        for ticker in self.tickers:
            expected_filename = f"{ticker}_1d.csv"
            path = os.path.join(self.transf_folder, expected_filename)

            # Check if file exists
            if not os.path.exists(path):
                logging.warning(f"⚠️ Missing file: {expected_filename}, update needed.")
                needs_update_flag = True
                continue

            try:
                # Read the CSV and parse dates
                df = pd.read_csv(path, parse_dates=['Date'])
                if df.empty:
                    logging.warning(f"⚠️ Empty file detected: {expected_filename}, update needed.")
                    needs_update_flag = True
                    continue

                df['Date'] = pd.to_datetime(df['Date']).dt.date
                latest = df['Date'].max()

                if pd.isna(latest):
                    logging.warning(f"⚠️ No valid date in {expected_filename}, update needed.")
                    needs_update_flag = True
                    continue

                days_difference = (now.date() - latest).days
                if days_difference > 7:
                    logging.warning(f"⚠️ Data in {expected_filename} is older than 7 days, update needed.")
                    needs_update_flag = True

            except Exception as e:
                logging.error(f"❌ Error checking {expected_filename}: {e}")
                needs_update_flag = True

        if needs_update_flag:
            return True

        logging.info("✅ All daily files are fresh (within last 7 days).")
        return False

    def fetch_daily_data(self):
        # Fetch data for each ticker
        for ticker in self.tickers:
            path = os.path.join(self.fetched_folder, f"{ticker}_1d.csv")
            logging.info(f"🔄 Fetching {ticker} daily data...")

            try:
                # Fetch the data with yfinance
                data = yf.download(ticker, interval="1d", period="max", auto_adjust=True)
                if data.empty:
                    logging.warning(f"⚠️ No data for {ticker} (1d)")
                    continue

                data.reset_index(inplace=True)
                data.rename(columns={data.columns[0]: "Date"}, inplace=True)
                data.to_csv(path, index=False)
                logging.info(f"✅ Raw daily data for {ticker} saved to: {path}")

            except Exception as e:
                logging.error(f"❌ Error fetching {ticker} (1d): {e}")

    def clean_fetched_data(self):
        # Dictionary to hold files with NaN values
        nan_files = {}

        # Loop through fetched data files
        for file in os.listdir(self.fetched_folder):
            if not file.endswith('.csv') or "_1d" not in file:
                continue

            fetch_path = os.path.join(self.fetched_folder, file)
            raw_path = os.path.join(self.raw_folder, file)

            try:
                df = pd.read_csv(fetch_path)

                if df.empty:
                    logging.warning(f"⚠️ Skipping empty file: {file}")
                    continue

                # Handle case if 'Date' column is missing
                if 'Date' not in df.columns:
                    df.columns = df.iloc[0]
                    df = df.iloc[1:].reset_index(drop=True)

                # Remove rows containing ticker in any column
                ticker = file.split('_')[0]
                df = df[~df.apply(lambda row: row.astype(str).str.contains(ticker).any(), axis=1)]

                # Convert Date to datetime and drop NaN rows
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                df.dropna(subset=['Date'], inplace=True)
                df.set_index('Date', inplace=True)

                # Convert all columns to numeric
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # Record files with NaN rows
                if df.isna().any().any():
                    nan_files[file] = df[df.isna().any(axis=1)]

                df.to_csv(raw_path)
                logging.info(f"✅ Processed daily data saved to: {raw_path}")

            except Exception as e:
                logging.error(f"❌ Error processing {file}: {e}")

        if nan_files:
            logging.warning("⚠️ Files with NaNs found:")
            for f, rows in nan_files.items():
                print(f"\n🔍 {f}\n{rows}")
        else:
            logging.info("✅ No missing daily data found.")

    def check_new_date(self):
        # Check for new date in raw data and update transformed files
        for file in os.listdir(self.raw_folder):
            if not file.endswith('.csv') or "_1d" not in file:
                continue

            raw_path = os.path.join(self.raw_folder, file)
            transf_path = os.path.join(self.transf_folder, file)
            processed_path = os.path.join(self.processed_folder, file)

            try:
                raw_df = pd.read_csv(raw_path, parse_dates=['Date'])
                raw_df['Date'] = pd.to_datetime(raw_df['Date']).dt.date
                raw_df.set_index('Date', inplace=True)

                # If transformation file doesn't exist, create it
                if not os.path.exists(transf_path):
                    raw_df.to_csv(transf_path)
                    logging.info(f"✅ New master daily file created: {transf_path}")
                    continue

                transf_df = pd.read_csv(transf_path, parse_dates=['Date'])
                transf_df['Date'] = pd.to_datetime(transf_df['Date']).dt.date
                transf_df.set_index('Date', inplace=True)

                new_rows = raw_df.loc[~raw_df.index.isin(transf_df.index)]

                # If there are new rows, append to the transformed file
                if not new_rows.empty:
                    new_rows.to_csv(processed_path)
                    logging.info(f"✅ New daily data detected and saved to: {processed_path}")

                    combined = pd.concat([transf_df, new_rows])
                    combined = combined[~combined.index.duplicated(keep='first')]
                    combined.sort_index(inplace=True)
                    combined.to_csv(transf_path)
                    logging.info(f"✅ Appended new daily data and updated: {transf_path}")
                else:
                    logging.info(f"ℹ️ No new daily data found for {file}.")

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
    handler = DailyDataHandler(tickers, base_folder)
    handler.update_all()