

# outlier detection
# rolling statistics
import pandas as pd
import yfinance as yf
import numpy as np
#download data
"""
#calc 21 days rolling mean and std
#join the rolling data bak to initioa ,df
calc upper and lower thresholds

"""

# Hampel filter

# detecting changepoints
import yfinance as yf
from kats.detectors.cumsum_detection import CUSUMDetector
from kats.consts import TimeSeriesData

"""
download data

convert df to timeseries data
tsd = TimeSeriesData(df)

instantion and run the changepoint detector
cumsum_detector = CUSUMDetector(tsd)
change_points = cumsum_detector.detector(change_directions=["increase"])
cumsum_detector.plot(change_points)

investigate detected changepoints
point, meta = change_points[0]

restricitng the detection window:
change_points = cumsum_detector.detector(change_directions=["increase"], interst_window=[200,250])
cumsum_detector.plot(change_points)

RobustStatsDetector
from kats.detectors.robust_stats_detection import RobustStatsDetector
robust_detector = RobustStatsDetector(tsd)
change_points = robust_detector.detector()
robust_detector.plot(change_points)
"""

#detecting trends 
"""
from kats.consts import TimeSeriesData
from kats.detectors.trend_mk import MKDetector

# download data

# keep only the close price and reset index and rename the columns
df = df[['Close']].reset_index(drop=False)
df.columns = ['time', 'price']

#convert df into timeseries
tsd = TimeSeriesData(df)
# instantiate and run the detector
trend_detector = MKDetector(tsd,threshold=0.9)
time_points = trend_detector.detector(direction="up",window_size=30)
trend_detector.plot(time_points)
"""

#detecting patterns in a time series using hurst exponenet
"""
H < 0.5 is mean reverting 
H=0.5 is random walk
H>0.5 is trending

# download data and plot clos prices across time

#define hurst exponent function - returns the hurst exponent of a timeseries
"""
def get_hurst_exponent(ts, max_lag=20):
    lags= range(2,max_lag)
    tau =[np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]
    hurst_exp = np.polyfit(np.log(lags), np.log(tau),i)[0]
    return hurst_exp
# calc values of the hurst exp using various value for max_lag
for lag in [20,100,250,500,1000]:
    hurst_exp = get_hurst_exponent(df["Close"].values, lag)
    print(f"Hurst exp with {lag} lags: {hurst_exp:4f}")

"""
hurst exponenet based on rescaled range analysis 
"""


