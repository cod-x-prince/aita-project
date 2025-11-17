import pandas as pd
import logging
import sys
from strategy_logic import run_orb_strategy, calculate_performance_with_exits

# --- Set up Logger ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# Make sure these filenames exactly match the files downloaded by the previous script
STOCKS_TO_TEST = [
    "reliance_2yr_1m_data.csv",
    "infy_2yr_1m_data.csv",
    "hdfcbank_2yr_1m_data.csv"
]
STARTING_CASH = 100000.0
BROKERAGE_PER_TRADE = 10.0
SLIPPAGE_PERCENT = 0.0005
STOP_LOSS_PERCENT = 0.02 
TAKE_PROFIT_PERCENT = 0.04

# --- Main Loop ---
for stock_file in STOCKS_TO_TEST:
    logger.info(f"============================================================")
    logger.info(f"--- Starting Backtest for {stock_file.upper()} ---")
    logger.info(f"============================================================")
    
    try:
        df_history = pd.read_csv(stock_file)
        df_history['timestamp'] = pd.to_datetime(df_history['timestamp_text'])
        df_history = df_history.sort_values(by='timestamp').set_index('timestamp')
        
        signals = run_orb_strategy(df_history, range_minutes=30)
        df_history['signal'] = signals

        ending_cash, df_trades = calculate_performance_with_exits(
            df_history, STARTING_CASH, BROKERAGE_PER_TRADE, 
            SLIPPAGE_PERCENT, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
        )

        total_profit = df_trades['profit'].sum()
        num_trades = len(df_trades)
        num_wins = len(df_trades[df_trades['profit'] > 0])
        win_rate = (num_wins / num_trades) * 100 if num_trades > 0 else 0
        
        logger.info(f"\n--- PERFORMANCE REPORT FOR {stock_file.upper()} ---")
        logger.info(f"Starting Portfolio Value: Rs.{STARTING_CASH:,.2f}")
        logger.info(f"Ending Portfolio Value:   Rs.{ending_cash:,.2f}")
        logger.info(f"Total Net Profit/Loss:    Rs.{total_profit:,.2f}")
        logger.info(f"Return Over Period:       {total_profit / STARTING_CASH * 100:.2f}%")
        logger.info("-" * 30)
        logger.info(f"Total Trades Executed:    {num_trades}")
        logger.info(f"Win Rate:                 {win_rate:.2f}%")
        logger.info("Exit Reasons:")
        print(df_trades['exit_reason'].value_counts())
        logger.info("--------------------------------\n\n")

    except FileNotFoundError:
        logger.error(f"Data file not found: {stock_file}. Please make sure it's in the project folder.")
    except Exception as e:
        logger.error(f"An error occurred during backtest for {stock_file}: {e}", exc_info=True)