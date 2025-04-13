import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from DayDataCollectorv2 import DayDataCollector
from IntradayDataHandler import IntradayDataHandler
import pandas as pd
import yfinance as yf


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

    raw_folder = "/data"
    processed_folder = "/data_preproc"
    tranf_folder = "/data_tranf"
    loaded_data_folder = "/data_load"
    ticker = mag7_tickers+pharma_tickers+fin_tickers + index_tickers + commod_tickers + curren_tickers + crypt_tickers
    #print(ticker)
    """ 
    dailyDataCollector = DayDataCollector(ticker, raw_folder, processed_folder)
    dailyDataCollector.fetch_data()
    dailyDataCollector.load_process_daily_data
    dailyDataCollector.append_daily_data()
    """
    intradayCollector = IntradayDataHandler(ticker, raw_folder, processed_folder, tranf_folder)
    intradayCollector.fetch_intraday_data()
    intradayCollector.fetch_2min_data()
    intradayCollector.load_process_intraday_data()
    intradayCollector.append_intraday_data()