"""
Google Cloud Storage Parquet Uploader
Uploads processed data as Parquet files to GCS bucket
"""

import os
import glob
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from dotenv import load_dotenv

try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logging.warning("Google Cloud Storage libraries not available")

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False
    logging.warning("PyArrow not available, Parquet export will fail")

load_dotenv()

logger = logging.getLogger(__name__)


class GCSParquetUploader:
    """Handles uploading data as Parquet files to Google Cloud Storage"""
    
    def __init__(self):
        if not GCS_AVAILABLE:
            raise ImportError("Google Cloud Storage libraries not installed")
        if not PARQUET_AVAILABLE:
            raise ImportError("PyArrow not installed")
        
        self.base_folder = os.getenv("BASE_FOLDER", "all_ohclv_data")
        self.transf_folder = os.path.join(self.base_folder, "transf_data")
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        self.bucket_path = os.getenv("GCS_BUCKET_PATH", "data")
        
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable not set")
        
        # Initialize GCS client
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = storage.Client(credentials=credentials)
        else:
            # Try default credentials
            self.client = storage.Client()
        
        self.bucket = self.client.bucket(self.bucket_name)
        
        # Track uploaded files (simple metadata file approach)
        self.metadata_file = Path("logs") / "gcs_upload_metadata.json"
        self.uploaded_files = self.load_uploaded_metadata()
    
    def load_uploaded_metadata(self):
        """Load metadata about previously uploaded files"""
        if self.metadata_file.exists():
            try:
                import json
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load upload metadata: {e}")
        return {}
    
    def save_uploaded_metadata(self):
        """Save metadata about uploaded files"""
        try:
            import json
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, "w") as f:
                json.dump(self.uploaded_files, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save upload metadata: {e}")
    
    def check_file_uploaded(self, local_file, gcs_path):
        """Check if a file has already been uploaded"""
        file_key = f"{os.path.basename(local_file)}_{gcs_path}"
        return file_key in self.uploaded_files
    
    def mark_file_uploaded(self, local_file, gcs_path, file_size):
        """Mark a file as uploaded"""
        file_key = f"{os.path.basename(local_file)}_{gcs_path}"
        self.uploaded_files[file_key] = {
            "uploaded_at": datetime.now().isoformat(),
            "size": file_size,
            "gcs_path": gcs_path
        }
    
    def load_and_format(self, filepath):
        """Load CSV and format for Parquet export"""
        df = pd.read_csv(filepath)
        
        # Standardize date column
        if "Date" in df.columns:
            df.rename(columns={"Date": "timestamp"}, inplace=True)
        elif "Datetime" in df.columns:
            df.rename(columns={"Datetime": "timestamp"}, inplace=True)
        
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        
        # Extract ticker and timeframe from filename
        base = os.path.basename(filepath).replace(".csv", "")
        parts = base.split("_")
        ticker = parts[0]
        timeframe = parts[-1]
        
        df["ticker"] = ticker
        df["timeframe"] = timeframe
        
        # Standardize column names
        column_mapping = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        }
        df = df.rename(columns=column_mapping)
        
        # Select and order columns
        required_cols = ["ticker", "timeframe", "timestamp", "open", "high", "low", "close", "volume"]
        df = df[[col for col in required_cols if col in df.columns]]
        
        return df
    
    def create_parquet_file(self, df, output_path):
        """Convert DataFrame to Parquet file"""
        table = pa.Table.from_pandas(df)
        pq.write_table(table, output_path, compression='snappy')
        return os.path.getsize(output_path)
    
    def upload_parquet_to_gcs(self, local_parquet_path, gcs_path):
        """Upload Parquet file to GCS"""
        blob = self.bucket.blob(gcs_path)
        blob.upload_from_filename(local_parquet_path)
        logger.info(f"Uploaded {local_parquet_path} to gs://{self.bucket_name}/{gcs_path}")
    
    def get_gcs_path(self, ticker, timeframe, date):
        """Generate GCS path based on date partitioning"""
        year = date.strftime("%Y")
        month = date.strftime("%m")
        day = date.strftime("%d")
        filename = f"{ticker}_{timeframe}.parquet"
        return f"{self.bucket_path}/{year}/{month}/{day}/{filename}"
    
    def upload_new_data(self):
        """Upload new data files to GCS as Parquet"""
        logger.info("Starting GCS Parquet upload...")
        
        # Find all CSV files
        csv_files = glob.glob(os.path.join(self.transf_folder, "*.csv"))
        
        if not csv_files:
            logger.warning("No CSV files found for upload")
            return
        
        # Create temporary directory for Parquet files
        temp_dir = Path("temp_parquet")
        temp_dir.mkdir(exist_ok=True)
        
        uploaded_count = 0
        skipped_count = 0
        
        for csv_file in csv_files:
            try:
                # Load and format data
                df = self.load_and_format(csv_file)
                
                if df.empty:
                    logger.warning(f"Skipping empty file: {csv_file}")
                    continue
                
                # Get ticker and timeframe
                ticker = df["ticker"].iloc[0]
                timeframe = df["timeframe"].iloc[0]
                
                # Get date range for partitioning
                min_date = df["timestamp"].min()
                max_date = df["timestamp"].max()
                
                # For simplicity, use the most recent date for path
                # In production, you might want to partition by date ranges
                gcs_path = self.get_gcs_path(ticker, timeframe, max_date)
                
                # Check if already uploaded
                if self.check_file_uploaded(csv_file, gcs_path):
                    logger.info(f"Skipping {csv_file} (already uploaded)")
                    skipped_count += 1
                    continue
                
                # Create Parquet file
                parquet_filename = f"{ticker}_{timeframe}_{datetime.now().strftime('%Y%m%d')}.parquet"
                parquet_path = temp_dir / parquet_filename
                
                file_size = self.create_parquet_file(df, str(parquet_path))
                
                # Upload to GCS
                self.upload_parquet_to_gcs(str(parquet_path), gcs_path)
                
                # Mark as uploaded
                self.mark_file_uploaded(csv_file, gcs_path, file_size)
                
                # Clean up local Parquet file
                parquet_path.unlink()
                
                uploaded_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}", exc_info=True)
        
        # Save metadata
        self.save_uploaded_metadata()
        
        # Clean up temp directory
        try:
            temp_dir.rmdir()
        except:
            pass
        
        logger.info(f"GCS upload completed: {uploaded_count} files uploaded, {skipped_count} skipped")

