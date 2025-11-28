# Data Pipeline Architecture

This document outlines the recommended data pipeline for collecting, storing, and analyzing financial data using this project, especially when dealing with large data volumes and limited local storage.

## Pipeline Diagram

The architecture is designed to use a small VPS for data collection while offloading storage and analysis to scalable cloud services.

```mermaid
graph TD;
    subgraph Data Source
        A[Yahoo Finance API]
    end

    subgraph VPS Collector
        B[service.py on VPS]
    end

    subgraph Cloud Storage & Warehouse
        C[Google Cloud Storage (GCS) <br/><i>Parquet Files / Data Lake</i>]
        D[Google BigQuery <br/><i>Data Warehouse</i>]
    end

    subgraph Analysis Layer
        E[Analysis & BI Tools <br/><i>SQL, Python, Looker, etc.</i>]
    end

    A -- Fetches data --> B;
    B -- Uploads to --> C;
    B -- Uploads to --> D;
    D -- Queried by --> E;
```

## Workflow Steps

1.  **Collect (on VPS):**
    *   The `service.py` script runs on a schedule (e.g., via cron) on your VPS.
    *   It fetches the latest market data from the Yahoo Finance API.
    *   It performs optional data quality checks to ensure integrity.
    *   Data is temporarily stored on the VPS's local disk before upload.

2.  **Store (in Cloud):**
    *   The script connects to your Google Cloud account and uploads the processed data to one or both of the following destinations:
        *   **Google Cloud Storage (GCS):** Data is saved as efficiently compressed and partitioned Parquet files. This acts as a scalable and cost-effective "data lake" for long-term archival.
        *   **Google BigQuery:** Data is loaded into structured tables. This serves as a high-performance "data warehouse," optimized for fast and complex analytical SQL queries.

3.  **Analyze (from anywhere):**
    *   With the data residing in BigQuery, you can connect powerful tools for analysis without impacting your VPS.
    *   Run complex SQL queries using the BigQuery web UI or any connected SQL client.
    *   Connect Business Intelligence (BI) tools like Looker, Tableau, or Google Data Studio to create dashboards.
    *   Analyze the data in Python or R notebooks by connecting to the BigQuery API.

## Key Benefits

*   **Scalability:** Overcomes the storage limitations (e.g., 200GB SSD) of a single VPS by using virtually limitless cloud storage.
*   **Performance:** Leverages Google BigQuery's powerful distributed engine to run queries over massive datasets far faster than a local PostgreSQL database could.
*   **Decoupling:** Your collection service on the VPS is decoupled from your analysis workload. You can scale them independently.
*   **Cost-Effectiveness:** You only pay for the cloud storage and queries you use, which is often more economical than upgrading VPS hardware.
*   **Resilience:** Cloud storage solutions are highly durable and resilient, protecting your valuable historical data.

## How to Enable This Pipeline

To activate this workflow, configure the relevant settings in your `.env` file:

1.  Enable the cloud uploaders:
    *   `ENABLE_GCS=true`
    *   `ENABLE_BIGQUERY=true`
2.  Set the storage mode:
    *   `STORAGE_MODE=both`
3.  Provide your Google Cloud project details:
    *   `GCS_BUCKET_NAME`
    *   `daily_datset_bq` and `intraday_dataset_bq`
    *   Ensure your `GOOGLE_APPLICATION_CREDENTIALS` are set up correctly.
