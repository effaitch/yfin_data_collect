"""
Combine all CSV files in all_ohclv_data/transf_data into one DataFrame.
Combine all timeframes (daily and intraday) into a single DataFrame.
Upload only new data (after latest timestamp in Postgres) to the 'yfin' table.
Schema: ticker (text), timeframe (text), timestamp (timestamptz), open (double), high (double), low (double), close (double), volume (double)
"""

import os
import glob
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Set paths
transf_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../all_ohclv_data/transf_data/"))
all_csvs = glob.glob(os.path.join(transf_folder, "*.csv"))

def load_and_format(filepath):
    df = pd.read_csv(filepath)
    # Determine if daily or intraday by column name
    if "Date" in df.columns:
        df.rename(columns={"Date": "timestamp"}, inplace=True)
    elif "Datetime" in df.columns:
        df.rename(columns={"Datetime": "timestamp"}, inplace=True)
    else:
        raise ValueError(f"File {filepath} missing Date or Datetime column")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    base = os.path.basename(filepath).replace(".csv", "")
    parts = base.split("_")
    ticker = parts[0]
    timeframe = parts[-1]
    df["ticker"] = ticker
    df["timeframe"] = timeframe
    # Ensure correct column order and types
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    return df[["ticker", "timeframe", "timestamp", "open", "high", "low", "close", "volume"]]

# Combine all timeframes into one DataFrame
all_df = pd.concat([load_and_format(f) for f in all_csvs], ignore_index=True) if all_csvs else pd.DataFrame()
print(f"Combined {len(all_df)} rows from all timeframes.")

def get_latest_timestamp_pg(conn, table_name):
    with conn.cursor() as cur:
        cur.execute(f"SELECT MAX(timestamp) FROM {table_name}")
        result = cur.fetchone()
        return result[0] if result else None

def upload_to_pg(df, table_name):
    if df.empty:
        print(f"No new data to upload for {table_name}")
        return
    # Prepare data as list of tuples
    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(df.columns)
    query = f"INSERT INTO {table_name} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
    with conn.cursor() as cur:
        execute_values(cur, query, tuples)
    conn.commit()
    print(f"Uploaded {len(df)} rows to {table_name}")

# Connect to Postgres
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

# Table name
yfin_table = "yfin"

# Upload only new data
if not all_df.empty:
    latest_ts = get_latest_timestamp_pg(conn, yfin_table)
    if latest_ts:
        latest_ts = pd.to_datetime(latest_ts)
        all_df = all_df[all_df["timestamp"] > latest_ts]
    upload_to_pg(all_df, yfin_table)

conn.close()