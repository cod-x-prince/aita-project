import os
import logging
import sys
from dotenv import load_dotenv
import webbrowser
import upstox_client
from upstox_client.api import login_api
from upstox_client.rest import ApiException

# --- Load Environment and Set up Logger ---
load_dotenv()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Main Authentication Logic ---
API_KEY = os.getenv("UPSTOX_API_KEY")
API_SECRET = os.getenv("UPSTOX_API_SECRET")
REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")

# --- NEW DEBUGGING STEP ---
# Let's print the values to make sure they are loaded correctly from the .env file.
logger.info("--- Verifying credentials loaded from .env file ---")
logger.info(f"API Key being used: {API_KEY}")
logger.info(f"Redirect URI being used: {REDIRECT_URI}")
logger.info("-------------------------------------------------")


if not all([API_KEY, API_SECRET, REDIRECT_URI]):
    logger.error("API credentials missing in .env file. Please check.")
else:
    try:
        api_config = upstox_client.Configuration()
        api_instance = login_api.LoginApi(upstox_client.ApiClient(api_config))

        api_response = api_instance.authorize(API_KEY, "v2", REDIRECT_URI)
        login_url = api_response.get('authorisation_url')

        logger.info(f"--- Step 1: Manual Login Required ---")
        # (The rest of the script is the same)

    # (Exception handling is the same)
    except ApiException as e:
        logger.error(f"Upstox API Exception: {e.status} {e.reason}")
        logger.error(e.body)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")