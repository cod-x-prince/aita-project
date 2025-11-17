from upstox_instrument_query.query import InstrumentQuery
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')

try:
    home_dir = Path.home()
    db_path = os.path.join(home_dir, '.upstox_instruments.db')
    query = InstrumentQuery(db_path)
    
    search_symbol = 'HDFCBANK'
    instruments = query.search_by_name(search_symbol)
    
    if instruments:
        logging.info(f"--- Found Instruments for '{search_symbol}' ---")
        for instrument in instruments:
            # We removed the filter to see ALL results
            logging.info(f"Name: {instrument['trading_symbol']}")
            logging.info(f"Instrument Key: {instrument['instrument_key']}")
            logging.info(f"Exchange: {instrument['exchange']}")
            # Let's also print the type to see what it is
            logging.info(f"Instrument Type: {instrument['instrument_type']}")
            logging.info("-" * 20)
    else:
        logging.warning(f"Could not find any instruments for '{search_symbol}'")

except Exception as e:
    logging.error(f"An error occurred: {e}")