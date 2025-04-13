import pandas as pd
import numpy as np


ticker = "CL=F"
timeframe = "1d"
raw_data = pd.read_csv(f"data/{ticker}_{timeframe}.csv")
# drop first row 
# set date as index
raw_data = raw_data.drop(raw_data.index[0])
# convert date to datetime
raw_data['Date'] = pd.to_datetime(raw_data['Date'])
# set date as index
raw_data = raw_data.set_index('Date')
# convert all columns to numeric
raw_data = raw_data.apply(pd.to_numeric, errors='coerce')
#print(raw_data.head())

df_returns = raw_data.copy()
# calculate daily returns
df_returns['Close'] = df_returns['Close'].astype(float)
df_returns['Returns'] = df_returns['Close'].pct_change()
df_returns['LogRet'] = np.log(df_returns['Close'] / df_returns['Close'].shift(1))
#print(df_returns.head())

# How to calc REALIZED volatility
def realized_volatility(x):
    """
    Calculate the realized volatility of a time series of returns.
    """
    return np.sqrt(np.sum(x**2))

# calculate realized volatility
df_realized_volatility = raw_data.copy()
df_realized_volatility['Close'] = df_realized_volatility['Close'].astype(float)
df_realized_volatility = (df.groupby(pd.Grouper(freq='M')).apply(realized_volatility).rename(column='log_ret':'realV'))
print(df_realized_volatility.head())
# annulaise the values
df_realized_volatility.rv = df_realized_volatility['realV'] * np.sqrt(12)
# csm [;lot t compsre voltility with log returns]

# inputting missing data
# 2 options include backfill or forwardfill
    # backfill is where we use previous data to fill in the missing data
    # forwardfill is where we use future data to fill in the missing data
for method in ['backfill', 'ffill']:
    df_na = raw_data.copy()
    # assign missing na values
    # fill missing values
    df_na[f"method_{method}"]=(df_na[['missing']].fillna(method=method))

