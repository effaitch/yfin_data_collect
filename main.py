import os
import sys
#sys.path.append(os.path.join(os.path.dirname(__file__), 'dataHandler'))
from dataHandler.DailyDataHandler import DailyDataHandler
from dataHandler.IntradayDataHandler import IntradayDataHandler
import pandas as pd
import yfinance as yf
import json


# Example Usage
if __name__ == "__main__":
    # read json file that contains the tickers
    with open("ticker.json", "r") as f:
        ticker_dict = json.load(f)
    # Combine all tickers into one list
    tickers = []
    for key in ticker_dict:
        tickers.extend(ticker_dict[key])
    
    base_folder = "all_ohclv_data"
    handler = DailyDataHandler(tickers, base_folder)
    handler.update_all()
    
    intradayHandler = IntradayDataHandler(tickers, base_folder)  
    intradayHandler.update_all()



"""
use the sql_import files to import the data into the database
from the all_ohclv_data/transf_data folder
"""