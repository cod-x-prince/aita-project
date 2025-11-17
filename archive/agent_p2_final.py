import os
import logging
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import json
import pandas as pd
import pandas_ta as ta
import upstox_client
from upstox_client.api import history_api
from upstox_client.rest import ApiException

# (Logger and API Configuration is the same as before)
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

# --- Agent Configuration ---
VOLUME_AVG_PERIOD = 20
VOLUME_FACTOR = 1.5
STATUS_FILE = "status.json"

# --- Main Agent Loop ---
while True:
    try:
        logger.info("--- Agent Loop: New cycle started ---")
        
        instrument_key = "NSE_EQ|INE002A01018"
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
        df = df.sort_values(by='timestamp')
        df.set_index('timestamp', inplace=True)
        
        df.ta.vwap(append=True)
        df.ta.sma(close=df['volume'], length=VOLUME_AVG_PERIOD, append=True)
        
        latest_data = df.iloc[-1]
        latest_time = latest_data.name.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Latest Data: Time: {latest_time}, Close: {latest_data['close']}, VWAP: {latest_data['VWAP_D']:.2f}")

        if len(df) > VOLUME_AVG_PERIOD:
            previous_bar = df.iloc[-2]
            current_bar = df.iloc[-1]
            
            # --- Specialist Agent Opinions ---
            # 1. Crossover Agent
            is_bullish_crossover = previous_bar['close'] < previous_bar['VWAP_D'] and current_bar['close'] > current_bar['VWAP_D']
            is_bearish_crossover = previous_bar['close'] > previous_bar['VWAP_D'] and current_bar['close'] < current_bar['VWAP_D']
            
            # 2. Volume Agent
            average_volume = previous_bar[f'SMA_{VOLUME_AVG_PERIOD}']
            is_volume_strong = current_bar['volume'] > (average_volume * VOLUME_FACTOR)

            # --- Master Agent Logic ---
            # The Master Agent makes the final decision based on a simple rulebook.
            final_signal = "HOLD" # Default decision is to do nothing.

            if is_bullish_crossover and is_volume_strong:
                final_signal = "BUY"
            elif is_bearish_crossover and is_volume_strong:
                final_signal = "SELL"
            
            logger.info(f"Crossover Opinion: {'BULLISH' if is_bullish_crossover else ('BEARISH' if is_bearish_crossover else 'HOLD')}, "
                        f"Volume Opinion: {'STRONG' if is_volume_strong else 'WEAK'}")
            logger.info(f"----> MASTER AGENT FINAL DECISION: {final_signal} <----")
            # --- NEW: Save Status to File ---
        # Create a dictionary with the latest status
        status = {
            'timestamp': latest_time,
            'close_price': current_bar['close'],
            'vwap': current_bar['VWAP_D'],
            'crossover_opinion': 'BULLISH' if is_bullish_crossover else ('BEARISH' if is_bearish_crossover else 'HOLD'),
            'volume_opinion': 'STRONG' if is_volume_strong else 'WEAK',
            'master_decision': final_signal
        }

        # Write the dictionary to our status file
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        logger.info("--- Cycle finished, sleeping for 60 seconds ---\n")
        time.sleep(60)