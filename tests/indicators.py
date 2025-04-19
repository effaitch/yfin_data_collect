import pandas as pd
import numpy as np
import ta
import os
"""
2. Signal indicators for OHLCV data
read OHLCV data 
- IN: {ticker, timeframe, indicator name, indicator parameters}
- OUT: {entry signal, exit signal,strategy name, strategy description}"""
class TechnicalIndicators:

    def __init__(self, df):
        self.df = df.copy()

    def add_rsi(self, window=14):
        self.df['RSI'] = ta.momentum.RSIIndicator(self.df['Close'], window=window).rsi()

    def add_bollinger_bands(self, window=20):
        bb = ta.volatility.BollingerBands(self.df['Close'], window=window)
        self.df['BB_Upper'] = bb.bollinger_hband()
        self.df['BB_Lower'] = bb.bollinger_lband()
        self.df['BB_Mid'] = bb.bollinger_mavg()

    def add_adx(self, window=14):
        self.df['ADX'] = ta.trend.ADXIndicator(self.df['High'], self.df['Low'], self.df['Close'], window=window).adx()

    def add_macd(self):
        macd = ta.trend.MACD(self.df['Close'])
        self.df['MACD'] = macd.macd()
        self.df['MACD_Signal'] = macd.macd_signal()
        self.df['MACD_Hist'] = macd.macd_diff()

    def add_ema(self, windows):
        for window in windows:
            self.df[f'EMA_{window}'] = ta.trend.EMAIndicator(self.df['Close'], window=window).ema_indicator()

    def add_sma(self, windows):
        for window in windows:
            self.df[f'SMA_{window}'] = self.df['Close'].rolling(window=window).mean()

    def add_fibonacci(self, window=100):
        high_max = self.df['High'].rolling(window=window).max()
        low_min = self.df['Low'].rolling(window=window).min()
        for level, ratio in zip(['0.236', '0.382', '0.5', '0.618', '0.786'], [0.236, 0.382, 0.5, 0.618, 0.786]):
            self.df[f'Fib_{level}'] = low_min + (high_max - low_min) * ratio

    def add_vwap(self):
        self.df['VWAP'] = ta.volume.VolumeWeightedAveragePriceIndicator(
            self.df['High'], self.df['Low'], self.df['Close'], self.df['Volume']
        ).volume_weighted_average_price()

    def get_data(self):
        return self.df


def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file in os.listdir(input_folder):
        if file.endswith(".csv"):
            file_path = os.path.join(input_folder, file)
            df = pd.read_csv(file_path)
            indicators = TechnicalIndicators(df)

            indicators.add_rsi(window=14)
            indicators.add_bollinger_bands(window=20)
            indicators.add_adx(window=14)
            indicators.add_macd()
            indicators.add_ema(windows=[50, 200])
            indicators.add_sma(windows=[50, 200])
            indicators.add_fibonacci(window=100)
            indicators.add_vwap()

            result_df = indicators.get_data()
            result_df.to_csv(os.path.join(output_folder, file), index=False)

# Example Usage
input_folder =  "./data_proc"
output_folder = "./indicator_data"
tickers=["CL=F"] # where file name begins with ticker
# choose inficator and its parameters
# Entry signal = rsi(14) < 30
# Exit signal = rsi(14) > 70
# Stop loss = 2 * ATR(14)
# Take profit = 2 * ATR(14)


# load data and save to output_folder
#process_folder("data", "output")
