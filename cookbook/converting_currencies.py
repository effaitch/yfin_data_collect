import pandas as pd
import yfinance as yf
from forex_python.converter import CurrencyRates

# to convert currencies for 

# downlaod stock data with following 
# start, end, progess=ase
#drop col adj close and vol
# instatiate current rates obj
c = CurrencyyRates()
#download teh usd/eur for each req date
df["usd_eur"]=[c.get_rate("USD","EUR",date) for date in df.index]

#convert price#
for column in df.columns[:-1]:
    df[f"{column}_EUR"]=df[column]*df["usd_eur"]

df.head()

