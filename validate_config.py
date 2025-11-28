#!/usr/bin/env python3
"""
Configuration Validation Script
Validates environment variables and configuration before running the service
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

errors = []
warnings = []

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if filepath and not Path(filepath).exists():
        errors.append(f"{description} file not found: {filepath}")

def check_env_var(var_name, description, required=False):
    """Check if environment variable is set"""
    value = os.getenv(var_name)
    if required and not value:
        errors.append(f"Required environment variable not set: {var_name} ({description})")
    elif not required and not value:
        warnings.append(f"Optional environment variable not set: {var_name} ({description})")
    return value

def validate_config():
    """Validate all configuration"""
    print("=" * 60)
    print("Configuration Validation")
    print("=" * 60)
    
    # General configuration
    print("\n[1] General Configuration")
    check_env_var("TZ", "Timezone", required=False)
    check_env_var("LOG_LEVEL", "Logging level", required=False)
    check_env_var("BASE_FOLDER", "Base data folder", required=False)
    
    # Check ticker.json exists
    if not Path("ticker.json").exists():
        errors.append("ticker.json file not found (required)")
    
    # Local DB configuration
    print("\n[2] Local PostgreSQL Database")
    enable_local_db = os.getenv("ENABLE_LOCAL_DB", "false").lower() == "true"
    if enable_local_db:
        check_env_var("DB_NAME", "Database name", required=True)
        check_env_var("DB_USER", "Database user", required=True)
        check_env_var("DB_PASSWORD", "Database password", required=True)
        check_env_var("DB_HOST", "Database host", required=False)
        check_env_var("DB_PORT", "Database port", required=False)
    else:
        warnings.append("Local DB upload is disabled (ENABLE_LOCAL_DB=false)")
    
    # BigQuery configuration
    print("\n[3] Google Cloud BigQuery")
    enable_bigquery = os.getenv("ENABLE_BIGQUERY", "false").lower() == "true"
    storage_mode = os.getenv("STORAGE_MODE", "bigquery").lower()
    
    if enable_bigquery or storage_mode in ["bigquery", "both"]:
        check_env_var("daily_datset_bq", "Daily BigQuery table", required=False)
        check_env_var("intraday_dataset_bq", "Intraday BigQuery table", required=False)
        credentials_path = check_env_var("GOOGLE_APPLICATION_CREDENTIALS", "GCP service account JSON", required=False)
        if credentials_path:
            check_file_exists(credentials_path, "GCP service account")
    else:
        warnings.append("BigQuery upload is disabled (ENABLE_BIGQUERY=false)")
    
    # GCS configuration
    print("\n[4] Google Cloud Storage")
    enable_gcs = os.getenv("ENABLE_GCS", "false").lower() == "true"
    
    if enable_gcs or storage_mode in ["parquet", "both"]:
        check_env_var("GCS_BUCKET_NAME", "GCS bucket name", required=True)
        check_env_var("GCS_BUCKET_PATH", "GCS bucket path", required=False)
        credentials_path = check_env_var("GOOGLE_APPLICATION_CREDENTIALS", "GCP service account JSON", required=False)
        if credentials_path:
            check_file_exists(credentials_path, "GCP service account")
    else:
        warnings.append("GCS Parquet upload is disabled (ENABLE_GCS=false)")
    
    # Quality monitoring
    print("\n[5] Data Quality Monitoring")
    enable_quality = os.getenv("ENABLE_QUALITY_CHECKS", "true").lower() == "true"
    if enable_quality:
        check_env_var("QUALITY_REPORT_PATH", "Quality report path", required=False)
    else:
        warnings.append("Quality checks are disabled (ENABLE_QUALITY_CHECKS=false)")
    
    # Check if at least one storage option is enabled
    print("\n[6] Storage Options Check")
    if not enable_local_db and not enable_bigquery and not enable_gcs:
        if storage_mode not in ["bigquery", "parquet", "both"]:
            warnings.append("No storage options enabled - data will only be collected locally")
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✓ All checks passed!")
    
    if not errors:
        print("\n✓ Configuration is valid. Service can run.")
        return True
    else:
        print("\n✗ Configuration has errors. Please fix them before running the service.")
        return False

if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)

