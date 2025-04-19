from binance.spot import Spot as Client
import pandas as pd
import numpy as np

# instantiate teh bin client and download last 500 tradees
spot_client=Client(base_url="https://api3.binance.com")
r = spot_cleint.trades("BTCEUR)")

# PROCESS TRADES INTO DF
df={pd.DataFrame(r).drop(columns=['isBuyermaker', 'isBestMatch'])}
df["time"] = pd.to_datetime(df["time"], unit="ms")
for column in ["price", "qty", "quoteQty"]:
    df[column] = pd.to_numeric(df[column])

# define fucntion to get raw aggreagtes into bares
def get_bars(df,add_time=False):
    ohlc=df["price"].ohlc()
    vwap=(df.apply(lambda_x: np.average(x["price"], weights=x["qty"])).toframe("vwap"))
    vol=df["qty"].sum().to_frame("vol")
    cnt=df["qty"].size().to_frame("cnt")
    if add_time:
        time=df["time"].last().to_frame("time")
        res=pd.concat([ohlc, vwap, vol, cnt, time], axis=1)
    else:
        res=pd.concat([ohlc, vwap, vol, cnt], axis=1)
        return res

# get the time bars
df_grouped_time=df.groupby(pd.Grouper(keys="time",freq="1Min"))
time_bars=get_bars(df_grouped_time)
time_bars

#get the tick bars
bar_size=50
df["tick_group"]