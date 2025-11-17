import requests
import gzip
import pandas as pd
import logging
import sys

# --- Set up Logger ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# This is the official public URL from Upstox for their complete instrument list
INSTRUMENT_LIST_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
OUTPUT_FILE = "upstox_complete_instruments.csv"

logger.info(f"Downloading master instrument list from Upstox...")
logger.info("This may take a moment...")

try:
    # Use requests to download the compressed file
    response = requests.get(INSTRUMENT_LIST_URL, stream=True)
    response.raise_for_status() # This will raise an error if the download fails

    # Decompress the file in memory and use pandas to read the JSON data
    with gzip.open(response.raw, 'rt') as f:
        # We read the file line by line to handle large JSON files efficiently
        df = pd.read_json(f, lines=True)
        
    # Save the full list as a CSV file for easy searching
    df.to_csv(OUTPUT_FILE, index=False)
    
    logger.info(f"--- SUCCESS! ---")
    logger.info(f"Successfully downloaded and saved {len(df)} instruments to {OUTPUT_FILE}")
    logger.info(f"You can now open the file '{OUTPUT_FILE}' in VS Code and search for any symbol.")

except Exception as e:
    logger.error(f"Failed to download or process the instrument list: {e}")