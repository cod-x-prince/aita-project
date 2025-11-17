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
TARGET_STOCKS = {
    "RELIANCE": "NSE_EQ|INE002A01018",
    "INFY": "NSE_EQ|INE009A01021",
    "HDFCBANK": "BSE_EQ|INE040A01034"
}
YEARS_OF_DATA_TO_FETCH = 2 # Upstox API limit for 1-min data is typically 2 years
DAYS_TO_FETCH = YEARS_OF_DATA_TO_FETCH * 365

# --- Main Logic ---
logger.info(f"--- Starting Portfolio Historical Data Download ---")

# Loop through each stock in our target list
for symbol, instrument_key in TARGET_STOCKS.items():
    try:
        logger.info(f"--- Downloading data for {symbol} ({instrument_key}) ---")
        output_filename = f"{symbol.lower()}_{YEARS_OF_DATA_TO_FETCH}yr_1m_data.csv"
        
        all_candles = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DAYS_TO_FETCH)
        current_date = end_date

        while current_date > start_date:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Fetching {symbol} data for: {date_str}")
            
            try:
                api_response = api_instance.get_historical_candle_data(
                    instrument_key=instrument_key,
                    interval="1minute",
                    to_date=date_str,
                    api_version="v2"
                )
                if api_response.data and api_response.data.candles:
                    all_candles.extend(api_response.data.candles)
                time.sleep(0.5) 
            except ApiException as e:
                if e.status == 404:
                    logger.warning(f"No data found for {symbol} on {date_str}.")
                else:
                    logger.error(f"API Exception for {symbol} on {date_str}: {e.reason}")
            
            current_date -= timedelta(days=1)

        logger.info(f"All data for {symbol} downloaded. Converting and saving...")
        
        df = pd.DataFrame(all_candles, columns=['timestamp_text', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp_text']).dt.tz_convert('Asia/Kolkata')
        df.drop_duplicates(subset=['timestamp'], inplace=True)
        df = df.sort_values(by='timestamp')
        
        df.to_csv(output_filename, index=False)
        logger.info(f"Successfully saved {len(df)} rows of data for {symbol} to {output_filename}")

    except Exception as e:
        logger.error(f"An unexpected error occurred for {symbol}: {e}")

logger.info("--- All Portfolio Data Downloaded Successfully ---")