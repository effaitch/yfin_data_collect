import os
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

class DayDataCollector:
    def __init__(self, tickers, raw_folder, processed_folder):
        self.tickers = [ticker.upper() for ticker in tickers]
        self.raw_folder = raw_folder
        self.processed_folder = processed_folder
        
        os.makedirs(raw_folder, exist_ok=True)
        os.makedirs(processed_folder, exist_ok=True)

        self.daily_timeframes = ["1d", "5d", "1wk", "1mo", "3mo"]
    def fetch_data(self):
        """
        Fetch historical data from Yahoo Finance and save it to raw folder.
        """
        for ticker in self.tickers:
            for timeframe in self.daily_timeframes:
                raw_csv_file = os.path.join(self.raw_folder, f"{ticker}_{timeframe}.csv")
                
                print(f"🔄 Fetching {ticker} data for timeframe: {timeframe}...")
                try:
                    period = "max"
                    data = yf.download(ticker, interval=timeframe, period=period)

                    if data.empty:
                        print(f"⚠️ No data available for {ticker} ({timeframe})")
                        continue
                    
                    # ✅ Ensure datetime is properly set
                    data.reset_index(inplace=True)  # Ensure 'Datetime' is a column
                    data.rename(columns={data.columns[0]: 'Datetime'}, inplace=True)

                    # ✅ Save to CSV
                    data.to_csv(raw_csv_file, index=False)
                    print(f"✅ Raw data for {ticker} ({timeframe}) saved to: {raw_csv_file}")

                except Exception as e:
                    print(f"❌ Error fetching {ticker} ({timeframe}): {e}")

                time.sleep(0.01)  # To avoid rate-limiting

    def load_process_daily_data(self):
        """
        Loads and processes daily and higher timeframe raw data, checks for NaNs, and saves to processed folder.
        """
        nan_files = {}

        for file in os.listdir(self.raw_folder):
            if file.endswith('.csv'):
                ticker_timeframe = file.replace('.csv', '')
                timeframe = ticker_timeframe.split('_')[-1]
                
                if timeframe not in self.daily_timeframes:
                    continue

                raw_path = os.path.join(self.raw_folder, file)
                processed_path = os.path.join(self.processed_folder, file)

                try:
                    df = pd.read_csv(raw_path)

                    if df.empty:
                        print(f"⚠️ Skipping empty file: {file}")
                        continue

                    # ✅ Handle missing headers
                    if 'Date' not in df.columns:
                        df.columns = df.iloc[0]  # First row as header
                        df = df[1:]

                    # ✅ Convert 'Date' column
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df.dropna(subset=['Date'], inplace=True)
                    df.set_index('Date', inplace=True)

                    # FIND row with {Ticker} vlaue - normally the first or second row and then drop it
                    

                    # ✅ Clean numeric columns
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                    # ✅ Check for NaNs before saving
                    if df.isna().any().any():
                        nan_rows = df[df.isna().any(axis=1)]
                        nan_files[ticker_timeframe] = nan_rows

                    # ✅ Save to processed folder
                    df.to_csv(processed_path))
                    print(f"✅ Processed daily data saved to: {processed_path}")

                except Exception as e:
                    print(f"❌ Error processing daily file {file}: {e}")

        # ✅ Report NaNs for daily files
        if nan_files:
            print("\n⚠️ Daily files with NaN values found:")
            for file, rows in nan_files.items():
                print(f"\n🔍 File: {file}")
                print(rows)
        else:
            print("\n✅ No missing daily data found.")


    def append_daily_data(self):
        """
        Append new data from raw files to existing processed files, avoiding duplicates.
        """
        for file in os.listdir(self.raw_folder):
            if file.endswith('.csv'):
                # add condition to inly work for daily timefreame
                ticker_timeframe = file.replace('.csv', '')
                timeframe = ticker_timeframe.split('_')[-1]
                
                if timeframe not in self.daily_timeframes:
                   continue
                raw_path = os.path.join(self.raw_folder, file)
                processed_path = os.path.join(self.processed_folder, file)

                try:
                    raw_data = pd.read_csv(raw_path, parse_dates=['Date'])
                    raw_data.set_index('Date', inplace=True)

                    if not os.path.exists(processed_path):
                        raw_data.to_csv(processed_path)
                        print(f"✅ Created new file: {processed_path}")
                        continue

                    processed_data = pd.read_csv(processed_path, parse_dates=['Date'])
                    processed_data.set_index('Date', inplace=True)

                    new_data = raw_data.loc[~raw_data.index.isin(processed_data.index)]

                    if not new_data.empty:
                        combined_data = pd.concat([processed_data, new_data])
                        combined_data.sort_index(inplace=True)
                        combined_data.to_csv(processed_path)
                        print(f"✅ Appended new data to: {processed_path}")

                except Exception as e:
                    print(f"❌ Error appending data for file {file}: {e}")

""" Example Usage
if __name__ == "__main__":
    # https://uk.finance.yahoo.com/markets/
    mag7_tickers=["AAPL", "TSLA", "MSFT", "AMZN", "GOOG", "META","NVDA"] # OK
    pharma_tickers=["MRNA","PFE","BNTX","LLY"]
    fin_tickers=["PYPL"]
    #https://uk.finance.yahoo.com/markets/world-indices/
    index_tickers = ["^GSPC","^DJI", "^IXIC", "^RUT","^STOXX50E","^FTSE","^N225","^GDAXI"] # OK
    # https://uk.finance.yahoo.com/markets/commodities/
    commod_tickers =["CL=F","GC=F","NG=F","BZ=F","SI=F","HG=F"] #OK
    # https://uk.finance.yahoo.com/markets/currencies/
    curren_tickers = ["GBPUSD=X","GBPEUR=X","EURUSD=X","GBPJPY=X","JPY=X","GBP=X"] #OK
    # https://uk.finance.yahoo.com/markets/crypto/all/
    crypt_tickers=["BTC-USD","ETH-USD","USDT-USD","USDC-USD","MATIC-USD","ADA-USD"] # OK

    # https://uk.finance.yahoo.com/markets/etfs/most-active/
    raw_folder = "./data"
    processed_folder = "./data_proc"
    ticker = mag7_tickers+pharma_tickers+fin_tickers + index_tickers + commod_tickers + curren_tickers + crypt_tickers
    #print(ticker)

    # still need to clean the df frame of the ticker column before saving to csv
    collector = DayDataCollector(ticker, raw_folder, processed_folder)
    collector.fetch_data()
    collector.fetch_2min_data()
    
    # load, process and append data post all tickers have been fetched
    collector.load_process_intraday_data()
    collector.load_process_daily_data()
    collector.append_intraday_data()
    collector.append_daily_data()"
    """