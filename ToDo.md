W: To have a reliable data source
O: use this to build a reliable databse of intraday data
OP1: if cannto automate the processing - can manulally run the task
OP2: if unable to manually run - create exception that comparing lost times that data may have gaps
OP3: if gaps form and data is incomplete - then be able to backfill data with linear reg 
OP4: 

1. DataCollection 
if time in last transf file is about 12 hours away then run data collection
Extract: into fetched folder 
Transform: clean up the fetched folder data to keep column format and highlight NaN
    - compare the rows by index Datetime to find any missing rows of data
    - move file from raw into process folder if there is new data to append or delete if not
    - append the data in process folder to transf folder file then delete the file in process folder
Load: all data from transf will be used for analysis

2. Data Analysis:
Normailise the data - simple and log returns

Seasonality of closing price over month, week and day
    consider data and timeline is in timezone
ohlcv features added:Inidcators
Start with Fundamental Technical Indicators: Implement classic indicators like:
Moving Averages (SMA, EMA) - to identify trends.   
Relative Strength Index (RSI) - to gauge overbought/oversold conditions.   
MACD - for trend and momentum.   
Bollinger Bands - for volatility and potential breakouts.
Simple Volume Indicators.
Create Lagged Price Features: Include past closing prices or returns as features.
Consider Volatility Measures: Calculate historical volatility.
