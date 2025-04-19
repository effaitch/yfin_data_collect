# inputting missing data
# 2 options include backfill or forwardfill
    # backfill is where we use previous data to fill in the missing data
    # forwardfill is where we use future data to fill in the missing data
for method in ['backfill', 'ffill']:
    df_na = raw_data.copy()
    # assign missing na values
    # fill missing values
    df_na[f"method_{method}"]=(df_na[['missing']].fillna(method=method))