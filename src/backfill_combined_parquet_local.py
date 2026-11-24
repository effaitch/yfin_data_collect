"""
Process CSV files in all_ohclv_data/transf_data one by one and upload to Postgres.
Memory-optimized for micro-VMs: avoids concatenating all files into a single DataFrame.
Upload only new data (after latest timestamp in Postgres) to the 'yfin' table, and fill stored rows that have no close.
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
all_parquets = glob.glob(os.path.join(transf_folder, "*.parquet"))

def format_df(df, filepath):
    """Format dataframe columns and types for DB upload."""
    # Determine if daily or intraday by column name
    if "Date" in df.columns:
        df.rename(columns={"Date": "timestamp"}, inplace=True)
    elif "Datetime" in df.columns:
        df.rename(columns={"Datetime": "timestamp"}, inplace=True)
    elif isinstance(df.index, (pd.DatetimeIndex, pd.Index)):
        # Check if the index is the timestamp
        if "timestamp" not in df.columns:
            df.index.name = "timestamp"
            df.reset_index(inplace=True)
    else:
        logger.warning(f"File {filepath} missing Date or Datetime column. Skipping.")
        return None
        
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    base = os.path.basename(filepath).replace(".parquet", "")
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

def get_priceless_timestamps_pg(conn, table_name, ticker, timeframe):
    """Timestamps of stored rows that have no close (DATA-YFIN-FRIDAY-CLOSE-01)."""
    with conn.cursor() as cur:
        query = (f"SELECT timestamp FROM {table_name} WHERE ticker = %s AND timeframe = %s "
                 "AND (close IS NULL OR close = 'NaN')")
        cur.execute(query, (ticker, timeframe))
        return [r[0] for r in cur.fetchall()]


def select_rows_to_upload(df, latest_ts, priceless_ts=()):
    """Rows to send: those after the latest stored bar, plus those whose stored version has no close.

    DATA-YFIN-FRIDAY-CLOSE-01: Yahoo sometimes returns the newest day with a volume and no prices. Such a row is
    not a bar and is never sent. A stored row without a close is sent again once Yahoo has its prices; before this
    fix only rows newer than the latest stored one were sent, so an empty Friday row stayed empty for good.
    """
    df = df[df["close"].notna()]
    if latest_ts is None:
        return df
    latest = pd.to_datetime(latest_ts, utc=True)
    holes = pd.to_datetime(list(priceless_ts), utc=True) if len(priceless_ts) else pd.DatetimeIndex([], tz="UTC")
    return df[(df["timestamp"] > latest) | (df["timestamp"].isin(holes))]


def upload_query(table_name, cols):
    """Insert new bars; fill the prices of a stored row only where that row has no close."""
    return (
        f"INSERT INTO {table_name} ({cols}) VALUES %s "
        "ON CONFLICT (ticker, timeframe, timestamp) DO UPDATE SET "
        "open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low, close = EXCLUDED.close, "
        f"volume = COALESCE(EXCLUDED.volume, {table_name}.volume) "
        f"WHERE {table_name}.close IS NULL OR {table_name}.close = 'NaN'"
    )


def upload_to_pg(conn, df, table_name):
    """Upload data using execute_values for efficiency."""
    if df.empty:
        return 0
    # Prepare data as list of tuples
    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(df.columns)
    query = upload_query(table_name, cols)
    with conn.cursor() as cur:
        execute_values(cur, query, tuples)
    conn.commit()
    return len(df)

def main():
    if not all_parquets:
        logger.info("No Parquet files found for upload.")
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
    
    logger.info(f"Processing {len(all_parquets)} files individually...")

    for filepath in all_parquets:
        try:
            # Read file
            df = pd.read_parquet(filepath)
            if df.empty:
                continue
                
            # Format
            formatted_df = format_df(df, filepath)
            if formatted_df is None:
                continue
                
            ticker = formatted_df["ticker"].iloc[0]
            timeframe = formatted_df["timeframe"].iloc[0]
            
            # Filter new data: bars after the latest stored one, and bars whose stored row has no close
            latest_ts = get_latest_timestamp_pg(conn, yfin_table, ticker, timeframe)
            priceless_ts = get_priceless_timestamps_pg(conn, yfin_table, ticker, timeframe) if latest_ts else []
            formatted_df = select_rows_to_upload(formatted_df, latest_ts, priceless_ts)
            
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
