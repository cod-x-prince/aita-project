# FILE: utils/util_search_instruments.py
import pandas as pd
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')
logger = logging.getLogger(__name__)

INSTRUMENT_FILE = "upstox_complete_instruments.csv"
SEARCH_SYMBOL = "GOLDM"
EXCHANGE = "MCX_FO"
INSTRUMENT_TYPE = "FUT"

try:
    df = pd.read_csv(INSTRUMENT_FILE)
    df.columns = df.columns.str.strip() # Clean column names
    
    filtered_df = df[
        (df['exchange'] == EXCHANGE) &
        (df['instrument_type'] == INSTRUMENT_TYPE) &
        (df['tradingsymbol'].str.contains(SEARCH_SYMBOL, na=False))
    ].copy()

    if not filtered_df.empty:
        filtered_df['expiry'] = pd.to_datetime(filtered_df['expiry'])
        future_contracts = filtered_df[filtered_df['expiry'] > datetime.now()]
        
        if not future_contracts.empty:
            nearest_future = future_contracts.sort_values(by='expiry').iloc[0]
            logger.info("\n--- Found Nearest Active Futures Contract ---")
            logger.info(f"Trading Symbol: {nearest_future['tradingsymbol']}")
            logger.info(f"Instrument Key: {nearest_future['instrument_key']}")
        else:
            logger.warning("Found contracts, but none are active.")
    else:
        logger.warning(f"No matching futures contract found for {SEARCH_SYMBOL}.")
except Exception as e:
    logger.error(f"An error occurred: {e}")