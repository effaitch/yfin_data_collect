# interactive visualisation
#import plotly.express as px
# import plotly.graph_objects as go
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import os

ticker = []
timeframe = "1d"
data_transf = "all_ohclv_data/transf_data"
data_playground = "all_ohclv_data/playground"



# find all files in data_transf that end with "_{tmeframe}.csv"
for file in os.listdir(data_transf):
    if file.endswith(f"_{timeframe}.csv"):
        # get the ticker from the file name
        ticker.append(file.split("_")[0])
        # copy the file to data_playground folder
        os.system(f"cp {data_transf}/{file} {data_playground}/{file}")
        