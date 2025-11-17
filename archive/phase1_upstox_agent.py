import os
import logging
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import pandas_ta as ta
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

# --- Main Agent Loop ---
while True:
    try:
        logger.info("--- Agent Loop: New cycle started ---")
        
        instrument_key = "NSE_EQ|INE002A01018" # Reliance Instrument Key
        today_date = datetime.now().strftime('%Y-%m-%d')

        api_response = api_instance.get_historical_candle_data(
            instrument_key=instrument_key,
            interval="1minute",
            to_date=today_date,
            api_version="v2"
        )
        
        candles = api_response.data.candles
        df = pd.DataFrame(candles, columns=['timestamp_text', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp_text']).dt.tz_convert('Asia/Kolkata')
        
        # --- THIS IS THE FIX ---
        # 1. Sort the data by the timestamp to ensure it's in chronological order.
        df = df.sort_values(by='timestamp')
        # 2. Set the timestamp as the official index of the DataFrame.
        df.set_index('timestamp', inplace=True)
        
        # Now, calculate VWAP on the properly sorted data
        df.ta.vwap(append=True)
        
        latest_data = df.iloc[-1]
        # We use .name to get the timestamp from the index
        latest_time = latest_data.name.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Latest Data for {instrument_key}:")
        logger.info(f"Time: {latest_time}, Close: {latest_data['close']}, VWAP: {latest_data['VWAP_D']:.2f}")

    except ApiException as e:
        logger.error(f"Upstox API Exception: {e.status} {e.reason}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        logger.info("--- Cycle finished, sleeping for 60 seconds ---\n")
        time.sleep(60)