# interactive visualisation
#import plotly.express as px
# import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import os

data_transf = "all_ohclv_data/transf_data"
data_playground = "all_ohclv_data/playground"

# create a vcahrt of the ohlcv data 
# one chart using close across time
#and underneath a simple return chart agaisnt time
# make it interactive 

#SEASONALITY
import nasdaqdatalink
import seaborn as sns
nasdaqdatalink.ApiConfig.api_key = "Key"

df = (nasdaqdatalink.get("FRED/UN-RATENSA", start_date="2020-01-01", end_date="2023-10-01").rename(columns={"value": "Unemployment rate"}))
df.plot(title="Unemployment rate 2020-2023")
# create new col with year and month and plt ulitlple lines

# other seasonality analysis
from statsmodels.graphics.tsaplots import month_plot, quarter_plot
import plotly.experss as px

month_plot(df["unemp_rate"], ylabel="unempeloyment rare (%)")
plt.title("Unemployment rate by month")

quarter_plot(df["unemp_rate"].resample("Q").mean(),, ylabel="unempeloyment rare (%)")

#cufflinks allow for more interactive vusualisations

# crearte a candle stick chart