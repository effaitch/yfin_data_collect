
"""
run through each csv in the root folder all_ohclv_data
find all the csv files with the same name 
- this will in the form "{ticker}_{timeframe}.csv"
- when duplicate found read each row and check what is the earliest and latest datetime values in index
- find any gaps in datetime values and combine the data if neccssary so we have a complete set of data for datetime row values
- put the combined data into a new csv file with the same name as the original and intoa  new folder called "transf"

where timeframe = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

"""
import os
import pandas as pd
from collections import defaultdict

# Setup root, subfolders, and timeframe list
root_folder = "all_ohclv_data"
sub_folders = ["data_loadz", "data_preproc", "data_proc_intraday", "fetched_data", "yfin_hist_data"]
valid_timeframes = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

# Folder to store transf results
transf_folder = os.path.join(root_folder, "transf")
os.makedirs(transf_folder, exist_ok=True)

# Grouping files by their base filename (e.g. AAPL_1m.csv)
file_groups = defaultdict(list)

# Search through each subfolder for matching CSV files
for sub in sub_folders:
    sub_path = os.path.join(root_folder, sub)
    if not os.path.exists(sub_path):
        continue

    for file_name in os.listdir(sub_path):
        if file_name.endswith(".csv"):
            base_name = os.path.splitext(file_name)[0]
            parts = base_name.split("_")

            if len(parts) >= 2:
                ticker, timeframe = parts[0], parts[1]
                if timeframe in valid_timeframes:
                    full_path = os.path.join(sub_path, file_name)
                    file_groups[file_name].append(full_path)

# Process and merge each group of matched files
for filename, file_list in file_groups.items():
    all_data = []
    print(f"\n🔄 Processing: {filename} with {len(file_list)} files...")

    for path in file_list:
        df = pd.read_csv(path)
        df.rename(columns={df.columns[0]: "Datetime"}, inplace=True)
        df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
        df.set_index("Datetime", inplace=True)
        all_data.append(df)

    # Combine and clean
    combined_df = pd.concat(all_data)
    combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
    combined_df.sort_index(inplace=True)
    combined_df.dropna(subset=["Close", "Open", "High", "Low"], how="any", inplace=True)

    # Infer and check missing timestamps
    freq = pd.infer_freq(combined_df.index)
    if freq:
        full_range = pd.date_range(start=combined_df.index.min(), end=combined_df.index.max(), freq=freq)
        missing = full_range.difference(combined_df.index)
        if not missing.empty:
            print(f"⚠️ {len(missing)} missing timestamps in {filename}")

    # Save transf file
    transf_path = os.path.join(transf_folder, filename)
    combined_df.to_csv(transf_path)
    print(f"✅ Saved transf file: {transf_path}")

