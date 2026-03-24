"""
Process CSV files in all_ohclv_data/transf_data one by one and upload to Postgres.
Memory-optimized for micro-VMs: avoids concatenating all files into a single DataFrame.
Upload only new data (after latest timestamp in Postgres) to the 'yfin' table.
Schema: ticker (text), timeframe (text), timestamp (timestamptz), open (double), high (double), low (double), close (double), volume (double)
"""

import os
import glob
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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

def format_df(df, filepath):
    """Format dataframe columns and types for DB upload."""
    # Determine if daily or intraday by column name
    if "Date" in df.columns:
        df.rename(columns={"Date": "timestamp"}, inplace=True)
    elif "Datetime" in df.columns:
        df.rename(columns={"Datetime": "timestamp"}, inplace=True)
    else:
        logger.warning(f"File {filepath} missing Date or Datetime column. Skipping.")
        return None
        
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    base = os.path.basename(filepath).replace(".csv", "")
    parts = base.split("_")
    ticker = parts[0]
    timeframe = parts[-1]
    df["ticker"] = ticker
    df["timeframe"] = timeframe
    
    # Ensure correct column names
    df = df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    # Filter and reorder columns
    cols = ["ticker", "timeframe", "timestamp", "open", "high", "low", "close", "volume"]
    # Ensure all required columns exist (yfinance sometimes omits volume for some instruments)
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    return df[cols]

def get_latest_timestamp_pg(conn, table_name, ticker, timeframe):
    """Get the latest timestamp for a specific ticker/timeframe combination."""
    with conn.cursor() as cur:
        query = f"SELECT MAX(timestamp) FROM {table_name} WHERE ticker = %s AND timeframe = %s"
        cur.execute(query, (ticker, timeframe))
        result = cur.fetchone()
        return result[0] if result else None

def upload_to_pg(conn, df, table_name):
    """Upload data using execute_values for efficiency."""
    if df.empty:
        return 0
    # Prepare data as list of tuples
    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(df.columns)
    query = f"INSERT INTO {table_name} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
    with conn.cursor() as cur:
        execute_values(cur, query, tuples)
    conn.commit()
    return len(df)

def main():
    if not all_csvs:
        logger.info("No CSV files found for upload.")
        return

    # Connect to Postgres
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return

    yfin_table = "yfin"
    total_uploaded = 0
    
    logger.info(f"Processing {len(all_csvs)} files individually...")

    for filepath in all_csvs:
        try:
            # Read file
            df = pd.read_csv(filepath)
            if df.empty:
                continue
                
            # Format
            formatted_df = format_df(df, filepath)
            if formatted_df is None:
                continue
                
            ticker = formatted_df["ticker"].iloc[0]
            timeframe = formatted_df["timeframe"].iloc[0]
            
            # Filter new data
            latest_ts = get_latest_timestamp_pg(conn, yfin_table, ticker, timeframe)
            if latest_ts:
                latest_ts = pd.to_datetime(latest_ts)
                formatted_df = formatted_df[formatted_df["timestamp"] > latest_ts]
            
            # Upload
            if not formatted_df.empty:
                rows = upload_to_pg(conn, formatted_df, yfin_table)
                total_uploaded += rows
                logger.info(f"Uploaded {rows} new rows for {ticker} ({timeframe})")
            else:
                logger.debug(f"No new data for {ticker} ({timeframe})")
                
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")

    conn.close()
    logger.info(f"Upload complete. Total rows added to PostgreSQL: {total_uploaded}")

if __name__ == "__main__":
    main()
