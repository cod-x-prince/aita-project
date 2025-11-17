import pandas as pd
import pandas_ta as ta
import logging
import sys
import numpy as np

# --- Set up Logger ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
HISTORICAL_DATA_FILE = "reliance_1m_data_2024_2025.csv"
VOLUME_AVG_PERIOD = 20
VOLUME_FACTOR = 1.5
STARTING_CASH = 100000.0
BROKERAGE_PER_TRADE = 10.0
SLIPPAGE_PERCENT = 0.0005

# --- Main Backtesting Logic ---
logger.info("--- Starting Final Backtest with CORRECT P&L Calculation ---")

try:
    df_history = pd.read_csv(HISTORICAL_DATA_FILE)
    df_history['timestamp'] = pd.to_datetime(df_history['timestamp_text'])
    df_history = df_history.sort_values(by='timestamp').set_index('timestamp')
    df_history.ta.vwap(append=True)
    df_history.ta.sma(close='volume', length=VOLUME_AVG_PERIOD, append=True)
    
    cash = STARTING_CASH
    shares = 0
    trades = []
    position_open = False

    for i in range(VOLUME_AVG_PERIOD, len(df_history)):
        current_bar = df_history.iloc[i]
        previous_bar = df_history.iloc[i-1]
        
        is_bullish_crossover = previous_bar['close'] < previous_bar['VWAP_D'] and current_bar['close'] > current_bar['VWAP_D']
        is_bearish_crossover = previous_bar['close'] > previous_bar['VWAP_D'] and current_bar['close'] < current_bar['VWAP_D']
        average_volume = previous_bar[f'SMA_{VOLUME_AVG_PERIOD}']
        is_volume_strong = current_bar['volume'] > (average_volume * VOLUME_FACTOR)

        final_signal = "HOLD"
        if is_bullish_crossover and is_volume_strong: final_signal = "BUY"
        elif is_bearish_crossover and is_volume_strong: final_signal = "SELL"

        if final_signal == "BUY" and not position_open:
            entry_price = current_bar['close'] * (1 + SLIPPAGE_PERCENT)
            cash -= BROKERAGE_PER_TRADE
            shares = cash / entry_price # Use all available cash
            cash = 0 # All cash is now in the position
            position_open = True
            trades.append({'entry_date': current_bar.name, 'entry_price': entry_price, 'shares': shares})
        elif final_signal == "SELL" and position_open:
            exit_price = current_bar['close'] * (1 - SLIPPAGE_PERCENT)
            cash -= BROKERAGE_PER_TRADE
            cash += shares * exit_price # Get cash back from selling shares
            shares = 0
            position_open = False
            
            # Record the completed trade
            trade_profit = (exit_price - trades[-1]['entry_price']) * trades[-1]['shares']
            trades[-1].update({'exit_date': current_bar.name, 'exit_price': exit_price, 'profit': trade_profit})
            
    # If a position is still open at the end, close it at the last price
    if position_open:
        last_price = df_history.iloc[-1]['close']
        cash += shares * last_price
        trades[-1].update({'exit_date': df_history.iloc[-1].name, 'exit_price': last_price, 'profit': (last_price - trades[-1]['entry_price']) * trades[-1]['shares']})
        
    logger.info("--- Backtest Simulation Finished ---")
    
    df_trades = pd.DataFrame(trades).dropna()
    total_profit = df_trades['profit'].sum()
    num_trades = len(df_trades)
    num_wins = len(df_trades[df_trades['profit'] > 0])
    win_rate = (num_wins / num_trades) * 100 if num_trades > 0 else 0
    
    logger.info("\n--- FINAL PERFORMANCE REPORT ---")
    logger.info(f"Starting Portfolio Value: Rs.{STARTING_CASH:,.2f}")
    logger.info(f"Ending Portfolio Value:   Rs.{cash:,.2f}")
    logger.info(f"Total Net Profit/Loss:    Rs.{total_profit:,.2f}")
    logger.info("-" * 30)
    logger.info(f"Total Trades Executed:    {num_trades}")
    logger.info(f"Win Rate:                 {win_rate:.2f}%")
    logger.info("--------------------------------\n")

except Exception as e:
    logger.error(f"An error occurred: {e}", exc_info=True)