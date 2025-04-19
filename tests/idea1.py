import pandas as pd
import numpy as np

class IndicatorCalculator:
    """Class to calculate RSI and Bollinger Bands manually."""
    
    @staticmethod
    def calculate_rsi(data, period=14):
        """
        Calculate the Relative Strength Index (RSI).
        
        :param data: DataFrame containing 'Close' prices.
        :param period: Lookback period for RSI calculation.
        :return: Series with RSI values.
        """
        delta = data["Close"].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=period, min_periods=1).mean()
        avg_loss = pd.Series(loss).rolling(window=period, min_periods=1).mean()

        rs = avg_gain / (avg_loss + 1e-9)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    @staticmethod
    def calculate_bollinger_bands(data, window=20, std_factor=2):
        """
        Calculate Bollinger Bands:
        :param data: DataFrame containing 'Close' prices.
        :param window: Lookback period for moving average.
        :param std_factor: Standard deviation factor for bands.
        :return: Tuple (middle_band, upper_band, lower_band).
        """
        middle_band = data["Close"].rolling(window=window).mean()
        std_dev = data["Close"].rolling(window=window).std()
        
        upper_band = middle_band + (std_factor * std_dev)
        lower_band = middle_band - (std_factor * std_dev)
        
        return middle_band, upper_band, lower_band

def define_trade_conditions(data):
    """
    Define Open/Close conditions for Long & Short trades based on RSI & BB.

    :param data: DataFrame containing OHLCV, RSI, and Bollinger Bands.
    :return: DataFrame with trading signals.
    """
    data["Open_Long"] = (data["RSI"] < 25) & (data["Close"] < data["Lower_BB"])
    data["Close_Long"] = (data["RSI"] > 75) | (data["Close"] > data["Upper_BB"])

    data["Open_Short"] = (data["RSI"] > 75) & (data["Close"] > data["Upper_BB"])
    data["Close_Short"] = (data["RSI"] < 25) | (data["Close"] < data["Lower_BB"])

    return data
