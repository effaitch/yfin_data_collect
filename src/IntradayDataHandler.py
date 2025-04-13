import os
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

class IntradayDataHandler:
    def __init__(self, tickers, raw_folder, processed_folder, tranf_folder):
        self.tickers = [ticker.upper() for ticker in tickers]
        self.raw_folder = raw_folder
        self.processed_folder = processed_folder
        self.tranf_folder = tranf_folder
        
        os.makedirs(raw_folder, exist_ok=True)
        os.makedirs(processed_folder, exist_ok=True)
        os.makedirs(tranf_folder, exist_ok=True)

        self.intraday_timeframes = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

    def fetch_intraday_data(self):
        """
        Fetch historical data from Yahoo Finance and save it to raw folder.
        """
        for ticker in self.tickers:
            for timeframe in self.intraday_timeframes:
                raw_csv_file = os.path.join(self.raw_folder, f"{ticker}_{timeframe}.csv")
                
                print(f"🔄 Fetching {ticker} data for timeframe: {timeframe}...")
                try:
                    period = "max"
                    data = yf.download(ticker, interval=timeframe, period=period)

                    if data.empty:
                        print(f"⚠️ No data available for {ticker} ({timeframe})")
                        continue
                    
                    # ✅ Ensure datetime is properly set
                    data.reset_index(inplace=True)
                    data.rename(columns={data.columns[0]: 'Datetime'}, inplace=True)

                    # ✅ Save to CSV
                    data.to_csv(raw_csv_file, index=False)
                    print(f"✅ Raw data for {ticker} ({timeframe}) saved to: {raw_csv_file}")

                except Exception as e:
                    print(f"❌ Error fetching {ticker} ({timeframe}): {e}")

                time.sleep(0.1)  # To avoid rate-limiting

    def fetch_2min_data(self):
        """
        Fetch 2-minute historical data from Yahoo Finance.
        """
        timeframe = "2m"
        for ticker in self.tickers:
            raw_csv_file = os.path.join(self.raw_folder, f"{ticker}_{timeframe}.csv")
            
            print(f"🔄 Fetching {ticker} data for timeframe: {timeframe}...")
            try:
                period = "60d"
                data = yf.download(ticker, interval=timeframe, period=period)

                if data.empty:
                    print(f"⚠️ No data available for {ticker} ({timeframe})")
                    continue
                
                # ✅ Ensure datetime is properly set
                data.reset_index(inplace=True)
                data.rename(columns={data.columns[0]: 'Datetime'}, inplace=True)

                # ✅ Save to CSV
                data.to_csv(raw_csv_file, index=False)
                print(f"✅ Raw data for {ticker} ({timeframe}) saved to: {raw_csv_file}")

            except Exception as e:
                print(f"❌ Error fetching {ticker} ({timeframe}): {e}")

            time.sleep(0.1)  # To avoid rate-limiting

    def load_process_intraday_data(self):
        """
        Loads and processes intraday raw data, checks for NaNs, and saves to processed folder.
        """
        nan_files = {}

        for file in os.listdir(self.raw_folder):
            if file.endswith('.csv'):
                ticker_timeframe = file.replace('.csv', '')
                timeframe = ticker_timeframe.split('_')[-1]
                
                if timeframe not in self.intraday_timeframes:
                    continue

                raw_path = os.path.join(self.raw_folder, file)
                processed_path = os.path.join(self.processed_folder, file)

                try:
                    df = pd.read_csv(raw_path)

                    if df.empty:
                        print(f"⚠️ Skipping empty file: {file}")
                        continue

                    # ✅ Handle missing headers
                    if 'Datetime' not in df.columns:
                        df.columns = df.iloc[0]
                        df = df.iloc[1:].reset_index(drop=True)

                    # ✅ Remove any row containing the ticker value in any column
                    ticker = ticker_timeframe.split('_')[0]
                    df = df[~df.apply(lambda row: row.astype(str).str.contains(ticker).any(), axis=1)].reset_index(drop=True)

                    # ✅ Convert 'Datetime' column
                    df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')
                    df.dropna(subset=['Datetime'], inplace=True)
                    df.set_index('Datetime', inplace=True)

                    # ✅ Clean numeric columns
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                    # ✅ Check for NaNs before saving
                    if df.isna().any().any():
                        nan_rows = df[df.isna().any(axis=1)]
                        nan_files[ticker_timeframe] = nan_rows
                    
                    # ✅ Save to processed folder
                    df.to_csv(processed_path)
                    print(f"✅ Processed intraday data saved to: {processed_path}")

                except Exception as e:
                    print(f"❌ Error processing intraday file {file}: {e}")

        if nan_files:
            print("\n⚠️ Intraday files with NaN values found:")
            for file, rows in nan_files.items():
                print(f"\n🔍 File: {file}")
                print(rows)
        else:
            print("\n✅ No missing intraday data found.")

    def append_intraday_data(self):
        """
        Append new data from raw files to existing processed files.
        """
        for file in os.listdir(self.raw_folder):
            if file.endswith('.csv'):
                ticker_timeframe = file.replace('.csv', '')
                timeframe = ticker_timeframe.split('_')[-1]

                if timeframe not in self.intraday_timeframes:
                    continue
                
                raw_path = os.path.join(self.raw_folder, file)
                processed_path = os.path.join(self.processed_folder, file)
                tranf_path = os.path.join(self.tranf_folder, file)

                try:
                    raw_data = pd.read_csv(raw_path, parse_dates=['Datetime'])
                    raw_data.set_index('Datetime', inplace=True)

                    if not os.path.exists(processed_path):
                        raw_data.to_csv(processed_path)
                        print(f"✅ Created new file: {processed_path}")
                        continue

                    processed_data = pd.read_csv(processed_path, parse_dates=['Datetime'])
                    processed_data.set_index('Datetime', inplace=True)

                    new_data = raw_data.loc[~raw_data.index.isin(processed_data.index)]

                    if not new_data.empty:
                        combined_data = pd.concat([processed_data, new_data])
                        combined_data.sort_index(inplace=True)
                        combined_data.to_csv(tranf_path)
                        print(f"✅ Appended new data to: {tranf_path}")

                except Exception as e:
                    print(f"❌ Error appending data for file {file}: {e}")



    

# Example Usage
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
    raw_folder = "./raw_intraday"
    processed_folder = "./data_preproc"
    tranf_folder = "./data_proc"
    #ticker = mag7_tickers+pharma_tickers+fin_tickers + index_tickers + commod_tickers + curren_tickers + crypt_tickers
    ticker=fin_tickers
    #print(ticker)

    # still need to clean the df frame of the ticker column before saving to csv
    """
    
    """
    intradayCollector = IntradayDataHandler(ticker, raw_folder, processed_folder, tranf_folder)
    intradayCollector.fetch_intraday_data()
    intradayCollector.fetch_2min_data()
    intradayCollector.load_process_intraday_data()
    intradayCollector.append_intraday_data()