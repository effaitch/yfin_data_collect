import os
import pandas as pd
import yfinance as yf

# create a script that reads all csv files in data_proc foldeer and then renames the columns as
# Datetime in the index, Close, High, Low, Open, Volume
data_proc_folder = '/home/hasfar/projects/trading_sys/data_proc'
raw_folder = '/home/hasfar/projects/trading_sys/data'
"""
for filename in os.listdir(raw_folder):
    if filename.endswith('.csv'):
        file_path = os.path.join(raw_folder, filename)
        df = pd.read_csv(file_path)
        print(df.dtypes)


"""

file_intraday="/home/hasfar/projects/trading_sys/data/CL=F_1m.csv"
file_interday="/home/hasfar/projects/trading_sys/data/CL=F_1d.csv"
intraday_timeframes = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h",]
daily_timeframes = ["1d", "5d", "1wk", "1mo", "3mo"]
tickers = ["CL=F"]
                    

