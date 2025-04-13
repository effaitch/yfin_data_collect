1. DataCollection 
raw: contains the final processed fetched data
fetch: temporary data that is fetched from the api
preproc: cleaned fetched data before appending to raw

OPTIMISE CODE:
- normalise the data in data_tranf

2. Signal indicators for OHLCV data
- IN: {filename(ticker, timeframe), indicator name, indicator parameters}
- OUT: {entry signal, exit signal,filename:{strategy name, date}, strategy tracker csv:{filename, descriptioin, entry, exit rules}}

