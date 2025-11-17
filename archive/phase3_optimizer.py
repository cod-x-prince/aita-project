# FILE: phase3_optimizer.py
import pandas as pd
import logging
import sys
from strategy_logic import run_v2_strategy, calculate_performance_with_exits

# --- Set up Logger ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
HISTORICAL_DATA_FILE = "reliance_1m_data_2024_2025.csv"
STARTING_CASH = 100000.0
BROKERAGE_PER_TRADE = 10.0
SLIPPAGE_PERCENT = 0.0005
STOP_LOSS_PERCENT = 0.02
TAKE_PROFIT_PERCENT = 0.04

# --- Optimization Parameters ---
volume_periods_to_test = [20, 40]
volume_factors_to_test = [1.5, 2.5]
trend_periods_to_test = [50, 100] # Our new parameter to test

# --- Main Optimizer Logic ---
try:
    df_history = pd.read_csv(HISTORICAL_DATA_FILE)
    df_history['timestamp'] = pd.to_datetime(df_history['timestamp_text'])
    df_history = df_history.sort_values(by='timestamp').set_index('timestamp')
    logger.info(f"Loaded {len(df_history)} rows of historical data.")
    
    results = []

    # Nested loops to test every combination
    for trend_period in trend_periods_to_test:
        for vol_period in volume_periods_to_test:
            for vol_factor in volume_factors_to_test:
                
                signals = run_v2_strategy(df_history, 
                                          volume_period=vol_period, 
                                          volume_factor=vol_factor, 
                                          trend_period=trend_period)
                df_history['signal'] = signals
                
                ending_cash, df_trades = calculate_performance_with_exits(
                    df_history, STARTING_CASH, BROKERAGE_PER_TRADE, 
                    SLIPPAGE_PERCENT, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
                )
                
                pnl = ending_cash - STARTING_CASH
                results.append({
                    'trend_period': trend_period, 
                    'vol_period': vol_period, 
                    'vol_factor': vol_factor, 
                    'pnl': pnl,
                    'win_rate': (len(df_trades[df_trades['profit'] > 0]) / len(df_trades) * 100) if len(df_trades) > 0 else 0,
                    'num_trades': len(df_trades)
                })
                logger.info(f"Finished run for TP={trend_period}, VP={vol_period}, VF={vol_factor}. P&L: Rs.{pnl:,.2f}")

    logger.info("\n--- V2 OPTIMIZATION COMPLETE ---")
    results_df = pd.DataFrame(results)
    ranked_results = results_df.sort_values(by='pnl', ascending=False)
    
    print("Top Performing Parameter Sets for Agent V2.0:")
    print(ranked_results.head(10))

except Exception as e:
    logger.error(f"An error occurred: {e}", exc_info=True)