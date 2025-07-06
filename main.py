import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from DailyDataHandler import DailyDataHandler
from IntradayCollector import IntradayCollector
import pandas as pd
import yfinance as yf
import json

# Example Usage
if __name__ == "__main__":
    # read json file that contains the tickers
    with open('ticker.json', 'r') as f:
        data = json.load(f)
        test_tickers = data['test_tickers']
        mag7_tickers = data['mag7_tickers']
        pharma_tickers = data['pharma_tickers']
        fin_tickers = data['fin_tickers']
        index_tickers = data['index_tickers']
        commod_tickers = data['commod_tickers']
        curren_tickers = data['curren_tickers']
        crypt_tickers = data['crypt_tickers']
    
    tickers = mag7_tickers+pharma_tickers+fin_tickers + index_tickers + commod_tickers + curren_tickers + crypt_tickers
    #print(ticker)
    

    base_folder = "/all_ohclv_data"
    handler = DailyDataHandler(test_tickers, base_folder)

    """
     # Before starting fetching/cleaning/processing
    if intradayCollector.needs_update():
        intradayCollector.fetch_intraday_data()
        intradayCollector.clean_fetched_data()
        intradayCollector.check_new_datetime()
    else:
        print("ℹ️ No update needed.")
    """  

    handler.update_all()
    
    intradayHandler = IntradayDataHandler(test_tickers, base_folder)

    """
     # Before starting fetching/cleaning/processing
    if intradayCollector.needs_update():
        intradayCollector.fetch_intraday_data()
        intradayCollector.clean_fetched_data()
        intradayCollector.check_new_datetime()
    else:
        print("ℹ️ No update needed.")
    """  

    intradayHandler.update_all()
