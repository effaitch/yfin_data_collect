import os
import pandas as pd
from idea1 import IndicatorCalculator, define_trade_conditions

# Load data
def load_data(data_folder):
    """
    Load CSV files from the data folder.

    :param data_folder: Path to folder containing CSV files.
    :return: Dictionary of DataFrames.
    """
    data_frames = {}

    for file_name in os.listdir(data_folder):
        if file_name.endswith(".csv"):
            file_path = os.path.join(data_folder, file_name)
            df_name = os.path.splitext(file_name)[0]

            df = pd.read_csv(file_path)
            df.rename(columns={df.columns[0]: "Datetime"}, inplace=True)
            df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
            df.set_index("Datetime", inplace=True)
            
            # Convert columns to numeric (handling errors)
            for col in ["Close", "High", "Low", "Open", "Volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            data_frames[df_name] = df
    
    return data_frames

def run_backtest(data_frames):
    """
    Run backtest on all datasets.

    :param data_frames: Dictionary of OHLCV DataFrames.
    """
    for df_name, df in data_frames.items():
        print(f"\n🚀 Running Strategy on {df_name}...")

        # Calculate indicators
        df["RSI"] = IndicatorCalculator.calculate_rsi(df, period=13)
        df["Middle_BB"], df["Upper_BB"], df["Lower_BB"] = IndicatorCalculator.calculate_bollinger_bands(df, window=30)

        # Define trade conditions
        df = define_trade_conditions(df)

        # Show first few rows
        print(df[["Close", "RSI", "Upper_BB", "Lower_BB", "Open_Long", "Close_Long", "Open_Short", "Close_Short"]].head())

# Define data folder path
data_folder = "/home/hasfar/projects/trading_sys/data"

# Load data & run backtest
data_frames = load_data(data_folder)
run_backtest(data_frames)
