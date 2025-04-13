import pandas as pd
import numpy as np

class StrategyTester:
    def __init__(self, data, strategy_function):
        self.data = data.copy()
        self.strategy_function = strategy_function
        self.results = None

    def run_backtest(self):
        """Apply the strategy function to the data."""
        self.results = self.strategy_function(self.data)

    def evaluate_performance(self):
        """Calculate key performance metrics."""
        self.results["Returns"] = self.results["Equity"].pct_change()
        net_profit = self.results["Equity"].iloc[-1] - self.results["Equity"].iloc[0]
        max_drawdown = self.calculate_max_drawdown()
        sharpe_ratio = self.results["Returns"].mean() / self.results["Returns"].std()

        return {
            "Net Profit": net_profit,
            "Max Drawdown": max_drawdown,
            "Sharpe Ratio": sharpe_ratio
        }

    def calculate_max_drawdown(self):
        """Calculate max drawdown from equity curve."""
        cum_max = self.results["Equity"].cummax()
        drawdown = self.results["Equity"] - cum_max
        return drawdown.min()

# Example strategy function
def simple_moving_average_strategy(data):
    """Simple moving average strategy using SMA50."""
    data = data.copy()
    data["SMA50"] = data["Close"].rolling(window=50).mean()
    data["Position"] = np.where(data["Close"] > data["SMA50"], 1, -1)
    data["Equity"] = (data["Position"].shift(1) * data["Close"]).cumsum()
    return data
