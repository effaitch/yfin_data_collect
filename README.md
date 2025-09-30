USing the yfin library to automate data collection to BigQuery in GCP

INSTRUCTIONS
Create json or file that can read all tickers you want to collect data from
- ticker.json

Define the folder you want to save the files in. 
   There are 4 folders that work in unison
   
      self.fetched_folder = os.path.join(base_folder, "fetched_data")
      this is to streo all the raw fetched data in raw form
      self.raw_folder = os.path.join(base_folder, "raw_intraday")
      this is where we store the processed fetched raw data
      self.processed_folder = os.path.join(base_folder, "process_data")
      - this is the processed data that is new 
      self.transf_folder = os.path.join(base_folder, "transf_data")
      - this is the final folder

Then use either the daily or intraday data collection
- can add more timeranges to intraday but will increase the time to run





UPDATES TO MAKE:
- Automate the trigger to be 1 week on saturday morning to run main.py file
- remove any checks when data is older than X time 
-make code leaner: how can we reduce the number of csv's and folder used/created, simpler fetch, process and store logic
- need a final step that combines all the ticker and timeframe data into 1 to acheive the desired output
- configure how to upload all raw data into BigQuery using the google-cloud-bigquery lib

BigQuery tables for daily and intraday have the following schema
   [
    {"name": "Date", "type": "TIMESTAMP"},
    {"name": "Ticker", "type": "STRING"},
    {"name": "Timeframe", "type": "STRING"},
    {"name": "Open", "type": "FLOAT"},
    {"name": "High", "type": "FLOAT"},
    {"name": "Low", "type": "FLOAT"},
    {"name": "Close", "type": "FLOAT"},
    {"name": "Volume", "type": "INTEGER"}
   ]



Log files are created whevner the functions are run through the main.py
- since daily is first to run, this one creates and stores all the logs for both functions.