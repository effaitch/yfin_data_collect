#!/usr/bin/env python3
import os
import pandas as pd
import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Load env from parent dir
env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(env_path)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "55432")

# Tickers to sync in real-time (Focus on active demo_trader epics)
TICKERS = ["CL=F", "GC=F", "BTC-USD", "ETH-USD"]
TIMEFRAMES = ["1m", "5m", "15m", "1h"]

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def sync_volume():
    conn = get_db_connection()
    
    for ticker in TICKERS:
        for tf in TIMEFRAMES:
            logger.info(f"🔄 Syncing {ticker} ({tf})...")
            try:
                # Fetch only last 2 days to be safe and fast
                data = yf.download(ticker, interval=tf, period="2d", auto_adjust=True)
                if data.empty:
                    continue
                
                # Flatten MultiIndex
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [col[0] for col in data.columns]
                
                data.reset_index(inplace=True)
                # Ensure 'timestamp' column name
                ts_col = data.columns[0]
                data.rename(columns={ts_col: "timestamp"}, inplace=True)
                
                # Format for yfin table
                df = pd.DataFrame()
                df['ticker'] = [ticker] * len(data)
                df['timeframe'] = [tf] * len(data)
                df['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
                df['open'] = data['Open']
                df['high'] = data['High']
                df['low'] = data['Low']
                df['close'] = data['Close']
                df['volume'] = data['Volume']
                
                # Using execute_values for efficiency
                tuples = [tuple(x) for x in df.to_numpy()]
                cols = ','.join(df.columns)
                # We now have idx_yfin_unique_sync on (ticker, timeframe, timestamp)
                query = f"INSERT INTO yfin ({cols}) VALUES %s ON CONFLICT (ticker, timeframe, timestamp) DO UPDATE SET volume = EXCLUDED.volume, close = EXCLUDED.close"
                
                with conn.cursor() as cur:
                    execute_values(cur, query, tuples)
                conn.commit()
                logger.info(f"✅ Synced {len(df)} rows for {ticker} ({tf})")
                
            except Exception as e:
                logger.error(f"❌ Failed to sync {ticker} ({tf}): {e}")
                conn.rollback() # Rollback the specific failed ticker transaction
    
    conn.close()

if __name__ == "__main__":
    sync_volume()
