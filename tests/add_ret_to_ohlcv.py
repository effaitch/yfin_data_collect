import pandas as pd
import numpy as np
import os

timeframe = "1d"
data_playground = "all_ohclv_data/playground"

# Go through all files in the playground folder
# if the values alreayd exisit skip this
for file in os.listdir(data_playground):
    if file.endswith(f"_{timeframe}.csv"):
        file_path = os.path.join(data_playground, file)
        
        # Read the file
        ohlcv_df = pd.read_csv(file_path, parse_dates=True)
        
        # Ensure 'Close' is float
        ohlcv_df['Close'] = ohlcv_df['Close'].astype(float)
        
        # Calculate returns and log returns
        ohlcv_df['Returns'] = ohlcv_df['Close'].pct_change()
        ohlcv_df['LogRet'] = np.log(ohlcv_df['Close'] / ohlcv_df['Close'].shift(1))
        
        # Save back to the same path
        ohlcv_df.to_csv(file_path, index=False)
        
        print(f"✅ Updated file: {file}")
        print(ohlcv_df.tail())

# anomaly detection over last 3 years, 3 months, 3 weeks, 3 days

# how to check the seasonalirt of the data across 3 years, 3 months, 3 weeks, 3 days


#