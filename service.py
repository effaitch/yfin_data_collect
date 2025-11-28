#!/usr/bin/env python3
"""
Main service script for Yahoo Finance Data Collection
Orchestrates the complete workflow: data collection, quality checks, and storage uploads
Designed to run on a small micro VM without Docker overhead
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataHandler.DailyDataHandler import DailyDataHandler
from dataHandler.IntradayDataHandler import IntradayDataHandler
# Import handlers - these will be imported conditionally
try:
    from dataHandler.data_quality_monitor import DataQualityMonitor
except ImportError:
    DataQualityMonitor = None

try:
    from dataHandler.gcs_uploader import GCSParquetUploader
except ImportError:
    GCSParquetUploader = None

# Load environment variables
load_dotenv()

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"service_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class DataCollectionService:
    """Main service class that orchestrates the complete data collection workflow"""
    
    def __init__(self):
        self.base_folder = "all_ohclv_data"
        self.ticker_file = "ticker.json"
        self.tickers = []
        self.load_tickers()
        
        # Configuration flags
        self.enable_local_db = os.getenv("ENABLE_LOCAL_DB", "false").lower() == "true"
        self.enable_bigquery = os.getenv("ENABLE_BIGQUERY", "false").lower() == "true"
        self.enable_gcs = os.getenv("ENABLE_GCS", "false").lower() == "true"
        self.storage_mode = os.getenv("STORAGE_MODE", "bigquery").lower()
        self.enable_quality_checks = os.getenv("ENABLE_QUALITY_CHECKS", "true").lower() == "true"
        
        # Initialize components
        self.quality_monitor = None
        if self.enable_quality_checks and DataQualityMonitor:
            try:
                self.quality_monitor = DataQualityMonitor()
            except Exception as e:
                logger.warning(f"Failed to initialize quality monitor: {e}")
        
        self.gcs_uploader = None
        if (self.enable_gcs or self.storage_mode in ["parquet", "both"]) and GCSParquetUploader:
            try:
                self.gcs_uploader = GCSParquetUploader()
            except Exception as e:
                logger.warning(f"Failed to initialize GCS uploader: {e}")
    
    def load_tickers(self):
        """Load tickers from configuration file"""
        try:
            with open(self.ticker_file, "r") as f:
                ticker_dict = json.load(f)
            for key in ticker_dict:
                self.tickers.extend(ticker_dict[key])
            logger.info(f"Loaded {len(self.tickers)} tickers from {self.ticker_file}")
        except FileNotFoundError:
            logger.error(f"Ticker file {self.ticker_file} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing {self.ticker_file}: {e}")
            sys.exit(1)
    
    def collect_data(self):
        """Step 1: Collect data from Yahoo Finance"""
        logger.info("=" * 60)
        logger.info("Step 1: Data Collection")
        logger.info("=" * 60)
        
        try:
            # Collect daily data
            logger.info("Collecting daily data...")
            daily_handler = DailyDataHandler(self.tickers, self.base_folder)
            daily_handler.update_all()
            
            # Collect intraday data
            logger.info("Collecting intraday data...")
            intraday_handler = IntradayDataHandler(self.tickers, self.base_folder)
            intraday_handler.update_all()
            
            logger.info("✓ Data collection completed successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Data collection failed: {e}", exc_info=True)
            return False
    
    def run_quality_checks(self):
        """Step 2: Run data quality monitoring"""
        if not self.enable_quality_checks or not self.quality_monitor:
            logger.info("Skipping quality checks (disabled)")
            return True
        
        logger.info("=" * 60)
        logger.info("Step 2: Data Quality Monitoring")
        logger.info("=" * 60)
        
        try:
            self.quality_monitor.run_checks()
            logger.info("✓ Quality checks completed successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Quality checks failed: {e}", exc_info=True)
            # Don't fail the pipeline on quality check errors
            return True
    
    def upload_to_local_db(self):
        """Step 3: Upload to local PostgreSQL database"""
        if not self.enable_local_db:
            logger.info("Skipping local DB upload (disabled)")
            return True
        
        logger.info("=" * 60)
        logger.info("Step 3: Local Database Upload")
        logger.info("=" * 60)
        
        try:
            import glob
            import pandas as pd
            import psycopg2
            from psycopg2.extras import execute_values
            
            # Load environment variables
            db_name = os.getenv("DB_NAME")
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            
            if not all([db_name, db_user, db_password]):
                logger.warning("Local DB credentials not configured, skipping upload")
                return True
            
            # Helper function to load and format CSV
            def load_and_format(filepath):
                df = pd.read_csv(filepath)
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
                df = df.rename(columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume"
                })
                return df[["ticker", "timeframe", "timestamp", "open", "high", "low", "close", "volume"]]
            
            # Connect to database
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            
            # Load and combine all CSV files
            transf_folder = os.path.join(self.base_folder, "transf_data")
            all_csvs = glob.glob(os.path.join(transf_folder, "*.csv"))
            
            if not all_csvs:
                logger.warning("No CSV files found in transf_data folder")
                conn.close()
                return True
            
            all_df = pd.concat([load_and_format(f) for f in all_csvs], ignore_index=True)
            logger.info(f"Combined {len(all_df)} rows from all timeframes")
            
            # Get latest timestamp and filter new data
            table_name = "yfin"
            with conn.cursor() as cur:
                cur.execute(f"SELECT MAX(timestamp) FROM {table_name}")
                result = cur.fetchone()
                latest_ts = result[0] if result else None
            
            if latest_ts:
                latest_ts = pd.to_datetime(latest_ts)
                all_df = all_df[all_df["timestamp"] > latest_ts]
                logger.info(f"Filtered to {len(all_df)} new rows after {latest_ts}")
            
            # Upload new data
            if not all_df.empty:
                tuples = [tuple(x) for x in all_df.to_numpy()]
                cols = ','.join(all_df.columns)
                query = f"INSERT INTO {table_name} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
                with conn.cursor() as cur:
                    execute_values(cur, query, tuples)
                conn.commit()
                logger.info(f"Uploaded {len(all_df)} rows to {table_name}")
            else:
                logger.info("No new data to upload to local DB")
            
            conn.close()
            logger.info("✓ Local DB upload completed successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Local DB upload failed: {e}", exc_info=True)
            # Don't fail the pipeline on local DB errors
            return True
    
    def upload_to_cloud_storage(self):
        """Step 4: Upload to cloud storage (BigQuery and/or GCS Parquet)"""
        logger.info("=" * 60)
        logger.info("Step 4: Cloud Storage Upload")
        logger.info("=" * 60)
        
        success = True
        
        # BigQuery upload
        if self.enable_bigquery or self.storage_mode in ["bigquery", "both"]:
            try:
                logger.info("Uploading to BigQuery...")
                import glob
                import pandas as pd
                from google.cloud import bigquery
                
                daily_table_id = os.getenv("daily_datset_bq")
                intraday_table_id = os.getenv("intraday_dataset_bq")
                
                if not daily_table_id and not intraday_table_id:
                    logger.warning("BigQuery table IDs not configured, skipping BigQuery upload")
                else:
                    client = bigquery.Client()
                    transf_folder = os.path.join(self.base_folder, "transf_data")
                    all_csvs = glob.glob(os.path.join(transf_folder, "*.csv"))
                    
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
                    
                    def get_latest_date(table_id, date_col="Date", client=None):
                        if client is None:
                            client = bigquery.Client()
                        query = f"SELECT MAX({date_col}) as max_date FROM `{table_id}`"
                        result = client.query(query).result()
                        for row in result:
                            return row.max_date
                        return None
                    
                    # Process daily data
                    if daily_files and daily_table_id:
                        daily_df = pd.concat([load_and_format(f, is_daily=True) for f in daily_files], ignore_index=True)
                        if not daily_df.empty:
                            latest_daily = get_latest_date(daily_table_id, "Date", client)
                            if latest_daily:
                                latest_daily_naive = pd.to_datetime(latest_daily).replace(tzinfo=None)
                                daily_df = daily_df[daily_df["Date"] > latest_daily_naive]
                            if not daily_df.empty:
                                job = client.load_table_from_dataframe(daily_df, daily_table_id)
                                job.result()
                                logger.info(f"Uploaded {len(daily_df)} rows to {daily_table_id}")
                    
                    # Process intraday data
                    if intraday_files and intraday_table_id:
                        intraday_df = pd.concat([load_and_format(f, is_daily=False) for f in intraday_files], ignore_index=True)
                        if not intraday_df.empty:
                            latest_intraday = get_latest_date(intraday_table_id, "Date", client)
                            if latest_intraday:
                                latest_intraday_naive = pd.to_datetime(latest_intraday).replace(tzinfo=None)
                                intraday_df = intraday_df[intraday_df["Date"] > latest_intraday_naive]
                            if not intraday_df.empty:
                                job = client.load_table_from_dataframe(intraday_df, intraday_table_id)
                                job.result()
                                logger.info(f"Uploaded {len(intraday_df)} rows to {intraday_table_id}")
                    
                    logger.info("✓ BigQuery upload completed successfully")
            except Exception as e:
                logger.error(f"✗ BigQuery upload failed: {e}", exc_info=True)
                success = False
        
        # GCS Parquet upload
        if self.enable_gcs or self.storage_mode in ["parquet", "both"]:
            try:
                logger.info("Uploading Parquet files to GCS...")
                if self.gcs_uploader:
                    self.gcs_uploader.upload_new_data()
                    logger.info("✓ GCS Parquet upload completed successfully")
                else:
                    logger.warning("GCS uploader not initialized")
            except Exception as e:
                logger.error(f"✗ GCS Parquet upload failed: {e}", exc_info=True)
                success = False
        
        return success
    
    def run(self):
        """Run the complete workflow"""
        logger.info("=" * 60)
        logger.info("Yahoo Finance Data Collection Service")
        logger.info(f"Started at: {datetime.now()}")
        logger.info("=" * 60)
        
        results = {
            "collection": False,
            "quality_checks": False,
            "local_db": False,
            "cloud_storage": False
        }
        
        # Step 1: Collect data
        results["collection"] = self.collect_data()
        if not results["collection"]:
            logger.error("Data collection failed, aborting workflow")
            return False
        
        # Step 2: Quality checks
        results["quality_checks"] = self.run_quality_checks()
        
        # Step 3: Upload to local DB (can run in parallel with cloud, but sequential for simplicity)
        results["local_db"] = self.upload_to_local_db()
        
        # Step 4: Upload to cloud storage
        results["cloud_storage"] = self.upload_to_cloud_storage()
        
        # Summary
        logger.info("=" * 60)
        logger.info("Workflow Summary")
        logger.info("=" * 60)
        for step, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"{status} {step.replace('_', ' ').title()}")
        
        all_success = all(results.values())
        if all_success:
            logger.info("=" * 60)
            logger.info("All tasks completed successfully!")
            logger.info(f"Completed at: {datetime.now()}")
            logger.info("=" * 60)
        else:
            logger.warning("Some tasks completed with errors (see logs above)")
        
        return all_success


def main():
    """Main entry point"""
    try:
        service = DataCollectionService()
        success = service.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

