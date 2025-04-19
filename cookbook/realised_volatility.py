import pandas as pd
import numpy as np
import os


timeframe = "1d"
data_transf = "all_ohclv_data/transf_data"
data_playground = "all_ohclv_data/playground"
         

raw_data = pd.read_csv(f"{data_playground}/*_{timeframe}.csv")


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



