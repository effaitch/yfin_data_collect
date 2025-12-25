#!/usr/bin/env python3
"""
Main service script for Yahoo Finance Data Collection
Orchestrates the complete workflow in the correct order:
1. Data collection (main.py)
2. Quality checks (data_quality_monitor.py)
3. BigQuery upload (combine_transf_csv_for_upload.py)
4. Local DB upload (backfill_combined_csv_local.py)

Designed to run via cron job on weekends
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

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
        self.project_root = Path(__file__).parent.absolute()
        self.python_exe = sys.executable
        
        # Configuration flags
        self.enable_local_db = os.getenv("ENABLE_LOCAL_DB", "false").lower() == "true"
        self.enable_bigquery = os.getenv("ENABLE_BIGQUERY", "false").lower() == "true"
        self.enable_quality_checks = os.getenv("ENABLE_QUALITY_CHECKS", "true").lower() == "true"
    
    def run_script(self, script_path, description):
        """Run a Python script and return success status"""
        logger.info(f"Running: {description}")
        logger.info(f"Script: {script_path}")
        
        try:
            result = subprocess.run(
                [self.python_exe, script_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            # Log output
            if result.stdout:
                logger.info(f"Output:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Errors:\n{result.stderr}")
            
            if result.returncode == 0:
                logger.info(f"✓ {description} completed successfully")
                return True
            else:
                logger.error(f"✗ {description} failed with return code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"✗ {description} timed out after 1 hour")
            return False
        except Exception as e:
            logger.error(f"✗ {description} failed: {e}", exc_info=True)
            return False
    
    def collect_data(self):
        """Step 1: Collect data from Yahoo Finance (main.py)"""
        logger.info("=" * 60)
        logger.info("Step 1: Data Collection")
        logger.info("=" * 60)
        
        main_script = self.project_root / "main.py"
        return self.run_script(main_script, "Data Collection")
    
    def run_quality_checks(self):
        """Step 2: Run data quality monitoring (data_quality_monitor.py)"""
        if not self.enable_quality_checks:
            logger.info("Skipping quality checks (disabled)")
            return True
        
        logger.info("=" * 60)
        logger.info("Step 2: Data Quality Monitoring")
        logger.info("=" * 60)
        
        # Import and run quality monitor
        try:
            sys.path.insert(0, str(self.project_root / "src"))
            from data_quality_monitor import DataQualityMonitor
            
            monitor = DataQualityMonitor()
            monitor.run_checks()
            logger.info("✓ Data Quality Monitoring completed successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Data Quality Monitoring failed: {e}", exc_info=True)
            # Don't fail the pipeline on quality check errors
            logger.warning("Continuing pipeline despite quality check issues")
            return True
    
    def upload_to_bigquery(self):
        """Step 3: Upload to BigQuery (combine_transf_csv_for_upload.py)"""
        if not self.enable_bigquery:
            logger.info("Skipping BigQuery upload (disabled)")
            return True
        
        logger.info("=" * 60)
        logger.info("Step 3: BigQuery Upload")
        logger.info("=" * 60)
        
        bq_script = self.project_root / "src" / "combine_transf_csv_for_upload.py"
        success = self.run_script(bq_script, "BigQuery Upload")
        
        # Don't fail the pipeline on BigQuery errors
        if not success:
            logger.warning("BigQuery upload had issues but continuing pipeline")
        return True
    
    def upload_to_local_db(self):
        """Step 4: Upload to local PostgreSQL database (backfill_combined_csv_local.py)"""
        if not self.enable_local_db:
            logger.info("Skipping local DB upload (disabled)")
            return True
        
        logger.info("=" * 60)
        logger.info("Step 4: Local Database Upload")
        logger.info("=" * 60)
        
        local_db_script = self.project_root / "src" / "backfill_combined_csv_local.py"
        success = self.run_script(local_db_script, "Local DB Upload")
        
        # Don't fail the pipeline on local DB errors
        if not success:
            logger.warning("Local DB upload had issues but continuing pipeline")
        return True
    
    def run(self):
        """Run the complete workflow in order"""
        logger.info("=" * 60)
        logger.info("Yahoo Finance Data Collection Service")
        logger.info(f"Started at: {datetime.now()}")
        logger.info("=" * 60)
        
        results = {
            "data_collection": False,
            "quality_checks": False,
            "bigquery_upload": False,
            "local_db_upload": False
        }
        
        # Step 1: Collect data (main.py)
        results["data_collection"] = self.collect_data()
        if not results["data_collection"]:
            logger.error("Data collection failed, aborting workflow")
            return False
        
        # Step 2: Quality checks (data_quality_monitor.py)
        results["quality_checks"] = self.run_quality_checks()
        
        # Step 3: Upload to BigQuery (combine_transf_csv_for_upload.py)
        results["bigquery_upload"] = self.upload_to_bigquery()
        
        # Step 4: Upload to local DB (backfill_combined_csv_local.py)
        results["local_db_upload"] = self.upload_to_local_db()
        
        # Summary
        logger.info("=" * 60)
        logger.info("Workflow Summary")
        logger.info("=" * 60)
        for step, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"{status} {step.replace('_', ' ').title()}")
        
        # Consider workflow successful if data collection succeeded
        # (uploads are non-critical)
        workflow_success = results["data_collection"]
        
        if workflow_success:
            logger.info("=" * 60)
            logger.info("Workflow completed!")
            logger.info(f"Completed at: {datetime.now()}")
            logger.info("=" * 60)
        else:
            logger.error("Workflow failed (see logs above)")
        
        return workflow_success


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
