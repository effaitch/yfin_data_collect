import yfinance as yf
from google.cloud import bigquery

def main(request):
    """Cloud Function to be triggered by Cloud Scheduler."""

    # Define your list of tickers
    tickers = ["AAPL", "GOOGL", "MSFT"]

    # Define your BigQuery client, dataset, and table
    client = bigquery.Client()
    dataset_id = "yfinance_data"
    table_id = "daily_stock_data"
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)

    # Loop through each ticker and fetch the data
    for ticker in tickers:
        data = yf.download(ticker, period="1d")
        data["Ticker"] = ticker # Add the ticker symbol to the DataFrame

        # Convert the index to a column
        data.reset_index(inplace=True)

        # Rename columns to match the BigQuery schema
        data.rename(columns={"Adj Close": "Adj_Close"}, inplace=True)


        # Load the data into BigQuery
        job_config = bigquery.LoadJobConfig(
            schema=table.schema,
            write_disposition="WRITE_APPEND",
        )

        job = client.load_table_from_dataframe(
            data, table_ref, job_config=job_config
        )
        job.result()  # Wait for the job to complete

    return "Data loaded successfully to BigQuery."