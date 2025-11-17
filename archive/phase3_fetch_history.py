import os
import logging
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import upstox_client
from upstox_client.api import history_api
from upstox_client.rest import ApiException

# --- Load .env and Set up Logger ---
load_dotenv()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configure API ---
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
api_config = upstox_client.Configuration()
api_config.access_token = ACCESS_TOKEN
api_client = upstox_client.ApiClient(api_config)
api_instance = history_api.HistoryApi(api_client)

# --- Configuration ---
instrument_key = "NSE_EQ|INE002A01018"
output_filename = "reliance_1m_data_2024_2025.csv"
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# --- Main Logic ---
try:
    logger.info(f"Starting historical data download for {instrument_key}...")
    all_candles = []
    current_date = end_date

    # --- THIS IS THE CORRECTED LOOP ---
    # We loop backwards one day at a time from today to the start date.
    while current_date > start_date:
        date_str = current_date.strftime('%Y-%m-%d')
        logger.info(f"Fetching data for: {date_str}")
        
        try:
            # Make the API call for this single day
            api_response = api_instance.get_historical_candle_data(
                instrument_key=instrument_key,
                interval="1minute",
                to_date=date_str, # The only date parameter needed
                api_version="v2"
            )
            
            if api_response.data and api_response.data.candles:
                all_candles.extend(api_response.data.candles)
            
            # Pause briefly to respect API rate limits
            time.sleep(0.5) 

        except ApiException as e:
            # It's normal to get a 404 error for weekends or holidays
            if e.status == 404:
                logger.warning(f"No data found for {date_str} (likely a weekend or holiday).")
            else:
                logger.error(f"API Exception on {date_str}: {e.reason}")
        
        # Move to the previous day for the next loop
        current_date -= timedelta(days=1)

    logger.info("All data chunks downloaded. Converting and saving...")
    
    df = pd.DataFrame(all_candles, columns=['timestamp_text', 'open', 'high', 'low', 'close', 'volume', 'oi'])
    df['timestamp'] = pd.to_datetime(df['timestamp_text']).dt.tz_convert('Asia/Kolkata')
    df.drop_duplicates(subset=['timestamp'], inplace=True)
    df = df.sort_values(by='timestamp')
    
    df.to_csv(output_filename, index=False)
    logger.info(f"Successfully saved {len(df)} rows of data to {output_filename}")

except Exception as e:
    logger.error(f"An unexpected error occurred: {e}")