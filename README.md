USing the yfin library 

Create json or file that can read all tickers you want to collect data from

define the folder you want to save the files in. 
There are 4 folders that work in unison
 
   self.fetched_folder = os.path.join(base_folder, "fetched_data")
    this is to streo all the raw fetched data in raw form
   self.raw_folder = os.path.join(base_folder, "raw_intraday")
    this is where we store the processed fetched raw data
   self.processed_folder = os.path.join(base_folder, "process_data")
   - this is the processed data 
   self.transf_folder = os.path.join(base_folder, "transf_data")
   - this si the transfordmed data

Then use either the daily or intraday data collection
- can add more timeranges to intraday but will increase the time to run


Future work
- implement a handling fo all errors in a table
    - hight eh the date run, ticker, timeframe, error message, last date in file 

