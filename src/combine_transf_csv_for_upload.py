"""
Combine all CSV files in all_ohclv_data/transf_data into one DataFrame.
Separate daily timeframe (_1d.csv) from intraday.
Upload only new data (after latest date in BigQuery) to respective tables.
"""

import os
import glob
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
daily_table_id = os.getenv("daily_datset_bq")
intraday_table_id = os.getenv("intraday_dataset_bq")

# Set paths
transf_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../all_ohclv_data/transf_data/"))
all_csvs = glob.glob(os.path.join(transf_folder, "*.csv"))

# Separate daily and intraday files
daily_files = [f for f in all_csvs if f.endswith("_1d.csv")]
intraday_files = [f for f in all_csvs if not f.endswith("_1d.csv")]

def load_and_format(filepath, is_daily=False):
    df = pd.read_csv(filepath)
    if is_daily:
        df["Date"] = pd.to_datetime(df["Date"])
    else:
        df.rename(columns={"Datetime": "Date"}, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
    base = os.path.basename(filepath).replace(".csv", "")
    parts = base.split("_")
    ticker = parts[0]
    timeframe = parts[-1]
    df["Ticker"] = ticker
    df["Timeframe"] = timeframe
    return df[["Date", "Ticker", "Timeframe", "Open", "High", "Low", "Close", "Volume"]]

# Combine all daily and intraday data
daily_df = pd.concat([load_and_format(f, is_daily=True) for f in daily_files], ignore_index=True) if daily_files else pd.DataFrame()
intraday_df = pd.concat([load_and_format(f, is_daily=False) for f in intraday_files], ignore_index=True) if intraday_files else pd.DataFrame()
print(f"Combined {len(daily_df)} daily rows and {len(intraday_df)} intraday rows.")

client = bigquery.Client()

def get_latest_date(table_id, date_col="Date"):
    query = f"SELECT MAX({date_col}) as max_date FROM `{table_id}`"
    result = client.query(query).result()
    for row in result:
        return row.max_date
    return None

def make_tz_naive(dt):
    # Converts a pandas.Timestamp or datetime to tz-naive
    if pd.isnull(dt):
        return dt
    if hasattr(dt, 'tz_convert'):
        return dt.tz_convert(None)
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def upload_to_bq(df, table_id):
    if df.empty:
        print(f"No new data to upload for {table_id}")
        return
    job = client.load_table_from_dataframe(df, table_id)
    job.result()
    print(f"Uploaded {len(df)} rows to {table_id}")

# Upload only new daily data
if not daily_df.empty and daily_table_id:
    latest_daily = get_latest_date(daily_table_id, "Date")
    if latest_daily:
        latest_daily_naive = pd.to_datetime(latest_daily).replace(tzinfo=None)
        daily_df = daily_df[daily_df["Date"] > latest_daily_naive]
    upload_to_bq(daily_df, daily_table_id)

# Upload only new intraday data
if not intraday_df.empty and intraday_table_id:
    latest_intraday = get_latest_date(intraday_table_id, "Date")
    if latest_intraday:
        latest_intraday_naive = pd.to_datetime(latest_intraday).replace(tzinfo=None)
        intraday_df = intraday_df[intraday_df["Date"] > latest_intraday_naive]
    upload_to_bq(intraday_df, intraday_table_id)