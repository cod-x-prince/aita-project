import os
import logging
import sys
import time
import json
from datetime import datetime, date
from dotenv import load_dotenv
import pandas as pd
import upstox_client
from upstox_client.api import history_api
from upstox_client.rest import ApiException
from utils.notifications import send_email, send_mobile_alert

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
# NOTE: Switched back to the profitable NSE key for HDFCBANK from our backtest
INSTRUMENT_KEY = "NSE_EQ|INE040A01034"
STOCK_SYMBOL = "HDFCBANK"
STATUS_FILE = "status.json"
RANGE_MINUTES = 30
VIRTUAL_CAPITAL = 100000.0 # Our starting paper trading capital

# --- Added stop loss and take profit parameters ---
STOP_LOSS_PERCENT = 0.02
TAKE_PROFIT_PERCENT = 0.04

# --- Agent State (The Agent's Memory) ---
today = date.today()
opening_range_high = 0
opening_range_low = float('inf')
trade_taken_today = False

# --- Added paper trading state variables ---
eod_report_sent = False
position_open = False
entry_price = 0
stop_loss_price = 0
take_profit_price = 0
trade_journal = []

logger.info("--- Live ORB Agent Initialized ---")
logger.info(f"Today's date: {today}. Waiting for market open...")

# --- Main Agent Loop ---
while True:
    try:
        # Check if it's a new day, and if so, reset the state
        if date.today() != today:
            today = date.today()
            opening_range_high = 0
            opening_range_low = float('inf')
            trade_taken_today = False
            
            # --- Reset paper trading state for new day ---
            eod_report_sent = False
            position_open = False
            entry_price = 0
            stop_loss_price = 0
            take_profit_price = 0
            trade_journal = []
            
            logger.info(f"--- New Day Detected: {today}. Agent state has been reset. ---")

        current_time = datetime.now().time()
        market_open_time = datetime.strptime("09:15", "%H:%M").time()
        range_end_time = datetime.strptime("09:45", "%H:%M").time() # 9:15 + 30 mins
        market_close_time = datetime.strptime("15:30", "%H:%M").time()
        
        # Only run during market hours
        if market_open_time <= current_time < market_close_time:
            # Fetch the latest 1-minute candle
            instrument_key = INSTRUMENT_KEY
            api_response = api_instance.get_intra_day_candle_data(instrument_key, "1minute", "v2")
            latest_candle = api_response.data.candles[-1]
            # Column order: timestamp, open, high, low, close, volume, oi
            latest_high = latest_candle[2]
            latest_low = latest_candle[3]
            latest_close = latest_candle[4]

            signal = "HOLD"

            # --- Live Trade Management Section ---
            if position_open:
                exit_reason = None
                exit_price = 0
                # Check for Stop-Loss
                if latest_low <= stop_loss_price:
                    exit_reason, exit_price = "STOP_LOSS", stop_loss_price
                # Check for Take-Profit
                elif latest_high >= take_profit_price:
                    exit_reason, exit_price = "TAKE_PROFIT", take_profit_price
    
                if exit_reason:
                    pnl = (exit_price - entry_price) * shares # <-- CORRECTED P&L CALCULATION
                    logger.info(f"!!! {exit_reason} TRIGGERED !!! Exiting trade. P&L: Rs.{pnl:,.2f}")
                    send_mobile_alert("trade_alert", STOCK_SYMBOL, pnl, exit_reason)
                    trade_journal.append(f"{exit_reason} Exit at {exit_price:.2f}. P&L: {pnl:,.2f}")
                    position_open = False

            # --- Agent Logic ---
            # 1. During the opening range window, just record the high and low
            if current_time < range_end_time:
                opening_range_high = max(opening_range_high, latest_high)
                opening_range_low = min(opening_range_low, latest_low)
                signal = "DEFINING_RANGE"
            
            # 2. After the opening range, check for breakouts
            # --- MODIFIED: Added condition to check if position is not already open ---
            elif not trade_taken_today and not position_open:
                if latest_high > opening_range_high:
                    signal = "BUY"
                    entry_price = opening_range_high
                    shares = VIRTUAL_CAPITAL / entry_price # <-- CORRECTED: Calculate position size
                    stop_loss_price = entry_price * (1 - STOP_LOSS_PERCENT)
                    take_profit_price = entry_price * (1 + TAKE_PROFIT_PERCENT)
                    position_open = True
                    trade_taken_today = True
                    trade_journal.append(f"BUY Entry at {entry_price:.2f} for {shares:.2f} shares.")
                    logger.info(trade_journal[-1])
                    
                elif latest_low < opening_range_low:
                    signal = "SELL"
                    trade_taken_today = True # Take only one trade per day
                    # Note: Currently only handling long trades (BUY then SELL)
                    logger.info("SELL Signal detected but logic is for long trades only. Holding.")
            
            # --- Broadcast Status for Dashboard ---
            status = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'close_price': latest_close,
                'current_signal': signal,
                'opening_range_high': opening_range_high,
                'opening_range_low': opening_range_low,
                'trade_taken_today': trade_taken_today,
                # --- Added paper trading status fields ---
                'position_open': position_open,
                'entry_price': entry_price,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'trade_journal': trade_journal
            }
            with open(STATUS_FILE, 'w') as f:
                json.dump(status, f)
            
            logger.info(f"Status Updated: Signal={signal}, OR High={opening_range_high:.2f}, OR Low={opening_range_low:.2f}")

        # --- End-of-day report logic ---
        elif current_time > market_close_time and not eod_report_sent:
            # Send end-of-day report
            subject = f"ORB Agent EOD Report - {today}"
            body = f"""
            ORB Agent End-of-Day Report for {today}
            
            Final Status:
            - Opening Range High: {opening_range_high:.2f}
            - Opening Range Low: {opening_range_low:.2f}
            - Trade Taken Today: {trade_taken_today}
            - Position Open: {position_open}
            
            Trade Journal:
            {chr(10).join(trade_journal) if trade_journal else 'No trades today'}
            """
            
            try:
                send_email(subject, body)
                eod_report_sent = True
                logger.info("EOD report sent successfully")
            except Exception as email_error:
                logger.error(f"Failed to send EOD report: {email_error}")

    except ApiException as e:
        logger.error(f"Upstox API Exception: {e.reason}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        time.sleep(60) # Wait for the next minute