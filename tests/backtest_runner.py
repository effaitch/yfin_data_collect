import os
from data_loader import load_data
from strategy_tester import StrategyTester, simple_moving_average_strategy

# Define data path
data_folder = "/home/hasfar/projects/trading_sys/data"

# Load all datasets
data_frames = load_data(data_folder)

# Run backtest on each dataset
performance_results = {}

for df_name, df in data_frames.items():
    print(f"\n🚀 Running Strategy on {df_name}...")

    tester = StrategyTester(df, simple_moving_average_strategy)
    tester.run_backtest()
    performance = tester.evaluate_performance()
    
    performance_results[df_name] = performance
    print(f"📊 Performance: {performance}")

# Print summary results
print("\n📈 Strategy Performance Summary:")
for asset, metrics in performance_results.items():
    print(f"\n🔹 {asset}")
    for metric, value in metrics.items():
        print(f"   {metric}: {value:.2f}")
