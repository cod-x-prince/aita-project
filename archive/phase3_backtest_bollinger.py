# FILE: phase3_backtest_bollinger.py
import pandas as pd
import logging
import sys
from strategy_logic import run_bollinger_bands_strategy, calculate_performance_with_exits

# --- Set up Logger ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
HISTORICAL_DATA_FILE = "reliance_1m_data_2024_2025.csv"
STARTING_CASH = 100000.0
BROKERAGE_PER_TRADE = 10.0
SLIPPAGE_PERCENT = 0.0005
STOP_LOSS_PERCENT = 0.02 # A 2% stop-loss
TAKE_PROFIT_PERCENT = 0.04 # A 4% take-profit

# --- BACKTESTING ENGINE ---
if __name__ == "__main__":
    try:
        df_history = pd.read_csv(HISTORICAL_DATA_FILE)
        df_history['timestamp'] = pd.to_datetime(df_history['timestamp_text'])
        df_history = df_history.sort_values(by='timestamp').set_index('timestamp')
        logger.info(f"Loaded {len(df_history)} rows of historical data.")

        # --- Call the NEW Bollinger Bands strategy brain ---
        signals = run_bollinger_bands_strategy(df_history, bb_length=20, bb_std=2.0)
        df_history['signal'] = signals

        ending_cash, df_trades = calculate_performance_with_exits(
            df_history, STARTING_CASH, BROKERAGE_PER_TRADE, 
            SLIPPAGE_PERCENT, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
        )

        # --- Performance Analysis ---
        logger.info("--- Backtest Finished for Bollinger Bands Strategy ---")
        total_profit = df_trades['profit'].sum()
        num_trades = len(df_trades)
        num_wins = len(df_trades[df_trades['profit'] > 0])
        win_rate = (num_wins / num_trades) * 100 if num_trades > 0 else 0
        
        logger.info("\n--- FINAL PERFORMANCE REPORT (V3: Bollinger Bands + SL/TP) ---")
        logger.info(f"Starting Portfolio Value: Rs.{STARTING_CASH:,.2f}")
        logger.info(f"Ending Portfolio Value:   Rs.{ending_cash:,.2f}")
        logger.info(f"Total Net Profit/Loss:    Rs.{total_profit:,.2f}")
        logger.info("-" * 30)
        logger.info(f"Total Trades Executed:    {num_trades}")
        logger.info(f"Win Rate:                 {win_rate:.2f}%")
        logger.info("Exit Reasons:")
        print(df_trades['exit_reason'].value_counts())
        logger.info("--------------------------------\n")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)