import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

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
            if not file.endswith('.csv'):
                continue

            timeframe = file.replace('.csv', '').split('_')[-1]
            if timeframe not in self.intraday_timeframes:
                continue

            path = os.path.join(self.transf_folder, file)

            try:
                df = pd.read_csv(path, parse_dates=['Datetime'])
                if df.empty:
                    logging.warning(f"⚠️ Empty file detected: {file}, update needed.")
                    return True

                df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True).dt.tz_convert(None)
                latest = df['Datetime'].max()

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
                path = os.path.join(self.fetched_folder, f"{ticker}_{tf}.csv")
                logging.info(f"🔄 Fetching {ticker} data for timeframe: {tf} (period: {period})...")
    
                try:
                    data = yf.download(ticker, interval=tf, period=period, auto_adjust=True)
                    if data.empty:
                        logging.warning(f"⚠️ No data for {ticker} ({tf})")
                        continue
    
                    data.reset_index(inplace=True)
                    data.rename(columns={data.columns[0]: "Datetime"}, inplace=True)
                    data.to_csv(path, index=False)
                    logging.info(f"✅ Raw data for {ticker} ({tf}) saved to: {path}")
    
                except Exception as e:
                    logging.error(f"❌ Error fetching {ticker} ({tf}): {e}")

    """def fetch_intraday_data(self):
        for ticker in self.tickers:
            for tf in self.intraday_timeframes:
                path = os.path.join(self.fetched_folder, f"{ticker}_{tf}.csv")
                logging.info(f"🔄 Fetching {ticker} data for timeframe: {tf}...")

                try:
                    data = yf.download(ticker, interval=tf, period="max", auto_adjust=True)
                    if data.empty:
                        logging.warning(f"⚠️ No data for {ticker} ({tf})")
                        continue

                    data.reset_index(inplace=True)
                    data.rename(columns={data.columns[0]: "Datetime"}, inplace=True)
                    data.to_csv(path, index=False)
                    logging.info(f"✅ Raw data for {ticker} ({tf}) saved to: {path}")

                except Exception as e:
                    logging.error(f"❌ Error fetching {ticker} ({tf}): {e}")
    """
    def clean_fetched_data(self):
        nan_files = {}

        for file in os.listdir(self.fetched_folder):
            if not file.endswith('.csv'):
                continue

            tf = file.replace('.csv', '').split('_')[-1]
            if tf not in self.intraday_timeframes:
                continue

            fetch_path = os.path.join(self.fetched_folder, file)
            raw_path = os.path.join(self.raw_folder, file)

            try:
                df = pd.read_csv(fetch_path)

                if df.empty:
                    logging.warning(f"⚠️ Skipping empty file: {file}")
                    continue

                if 'Datetime' not in df.columns:
                    df.columns = df.iloc[0]
                    df = df.iloc[1:].reset_index(drop=True)

                ticker = file.split('_')[0]
                df = df[~df.apply(lambda row: row.astype(str).str.contains(ticker).any(), axis=1)]

                df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True).dt.tz_convert(None)
                df.dropna(subset=['Datetime'], inplace=True)
                df.set_index('Datetime', inplace=True)

                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                if df.isna().any().any():
                    nan_files[file] = df[df.isna().any(axis=1)]

                df.to_csv(raw_path)
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
            if not file.endswith('.csv'):
                continue

            tf = file.replace('.csv', '').split('_')[-1]
            if tf not in self.intraday_timeframes:
                continue

            raw_path = os.path.join(self.raw_folder, file)
            transf_path = os.path.join(self.transf_folder, file)
            processed_path = os.path.join(self.processed_folder, file)

            try:
                raw_df = pd.read_csv(raw_path, parse_dates=['Datetime'])
                raw_df['Datetime'] = pd.to_datetime(raw_df['Datetime'], utc=True).dt.tz_convert(None)
                raw_df.set_index('Datetime', inplace=True)

                if not os.path.exists(transf_path):
                    raw_df.to_csv(transf_path)
                    logging.info(f"✅ New master file created: {transf_path}")
                    continue

                transf_df = pd.read_csv(transf_path, parse_dates=['Datetime'])
                transf_df['Datetime'] = pd.to_datetime(transf_df['Datetime'], utc=True).dt.tz_convert(None)
                transf_df.set_index('Datetime', inplace=True)

                new_rows = raw_df.loc[~raw_df.index.isin(transf_df.index)]

                if not new_rows.empty:
                    new_rows.to_csv(processed_path)
                    logging.info(f"✅ New data detected and saved to: {processed_path}")

                    combined = pd.concat([transf_df, new_rows])
                    combined = combined[~combined.index.duplicated(keep='first')]
                    combined.sort_index(inplace=True)
                    combined.to_csv(transf_path)
                    logging.info(f"✅ Appended new data and updated: {transf_path}")
                else:
                    logging.info(f"ℹ️ No new data found for {file}.")

            except Exception as e:
                logging.error(f"❌ Error comparing/appending for {file}: {e}")



# Example Usage
if __name__ == "__main__":
    test_tickers = ["^GSPC","^VIX","CL=F","GC=F","GBPUSD=X","GBPEUR=X","EURUSD=X"]
    # https://uk.finance.yahoo.com/markets/
    mag7_tickers=["AAPL", "TSLA", "MSFT", "AMZN", "GOOG", "META","NVDA"] # OK
    pharma_tickers=["MRNA","PFE","BNTX","LLY"]
    fin_tickers=["PYPL"]
    #https://uk.finance.yahoo.com/markets/world-indices/
    index_tickers = ["^GSPC","^VIX","^DJI", "^IXIC", "^RUT","^STOXX50E","^FTSE","^N225","^GDAXI"] # OK
    # https://uk.finance.yahoo.com/markets/commodities/
    commod_tickers =["CL=F","GC=F","NG=F","BZ=F","SI=F","HG=F"] #OK
    # https://uk.finance.yahoo.com/markets/currencies/
    curren_tickers = ["GBPUSD=X","GBPEUR=X","EURUSD=X","GBPJPY=X","JPY=X","GBP=X"] #OK
    # https://uk.finance.yahoo.com/markets/crypto/all/
    crypt_tickers=["BTC-USD","ETH-USD","USDT-USD","USDC-USD","MATIC-USD","ADA-USD"] # OK
    # https://uk.finance.yahoo.com/markets/etfs/most-active/
    
    tickers = mag7_tickers+pharma_tickers+fin_tickers + index_tickers + commod_tickers + curren_tickers + crypt_tickers
    #print(ticker)
    

    base_folder = "./all_ohclv_data"
    intradayCollector = IntradayDataHandler(tickers, base_folder)

    """
     # Before starting fetching/cleaning/processing
    if intradayCollector.needs_update():
        intradayCollector.fetch_intraday_data()
        intradayCollector.clean_fetched_data()
        intradayCollector.check_new_datetime()
    else:
        print("ℹ️ No update needed.")
    """  

    intradayCollector.update_all()
