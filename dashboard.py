import streamlit as st
import json
import time
from datetime import datetime
import os

STATUS_FILE = "status.json"

st.set_page_config(layout="wide")

st.title("AITA-01: Live ORB Agent Status")

# --- Create the layout ---
col1, col2, col3 = st.columns(3)
price_placeholder = col1.empty()
signal_placeholder = col2.empty()
trade_status_placeholder = col3.empty()

st.divider()

col_or1, col_or2 = st.columns(2)
or_high_placeholder = col_or1.empty()
or_low_placeholder = col_or2.empty()

st.divider()
status_text_placeholder = st.empty()


# --- Main Dashboard Loop ---
while True:
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                status = json.load(f)

            # --- Update Top Row Metrics ---
            price_placeholder.metric("Latest Price", f"Rs. {status.get('close_price', 0):.2f}")
            
            signal = status.get('current_signal', 'WAITING')
            if signal == "BUY":
                signal_placeholder.success("Signal: BUY")
            elif signal == "SELL":
                signal_placeholder.error("Signal: SELL")
            elif signal == "DEFINING_RANGE":
                signal_placeholder.info("Signal: DEFINING RANGE")
            else:
                signal_placeholder.info("Signal: HOLD")
            
            trade_taken = status.get('trade_taken_today', False)
            trade_status_placeholder.metric("Trade Taken Today?", "Yes" if trade_taken else "No")

            # --- Update Opening Range Metrics ---
            or_high_placeholder.metric("Opening Range High", f"Rs. {status.get('opening_range_high', 0):.2f}")
            or_low_placeholder.metric("Opening Range Low", f"Rs. {status.get('opening_range_low', 0):.2f}")
            
            # --- Update Status Text ---
            status_text_placeholder.write(f"Last Agent Update: {status.get('timestamp', 'N/A')}")

        except (FileNotFoundError, json.JSONDecodeError):
            status_text_placeholder.warning("Waiting for agent to produce status file...")
    else:
        status_text_placeholder.warning("Waiting for agent to produce status file...")
    
    time.sleep(5) # Refresh the dashboard every 5 seconds