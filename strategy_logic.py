# FILE: strategy_logic.py
import pandas as pd
import pandas_ta as ta

def run_v2_strategy(historical_data, volume_period=20, volume_factor=1.5, trend_period=50):
    df = historical_data.copy()
    
    # Calculate all indicators
    df.ta.vwap(append=True)
    df.ta.sma(close='volume', length=volume_period, append=True)
    df.ta.sma(length=trend_period, append=True) # Trend indicator

    signals = []
    for i in range(trend_period, len(df)):
        previous_bar = df.iloc[i-1]
        current_bar = df.iloc[i]
        
        # Specialist Agent Opinions
        is_bullish_crossover = previous_bar['close'] < previous_bar['VWAP_D'] and current_bar['close'] > current_bar['VWAP_D']
        is_bearish_crossover = previous_bar['close'] > previous_bar['VWAP_D'] and current_bar['close'] < current_bar['VWAP_D']
        
        avg_vol = previous_bar[f'SMA_{volume_period}']
        is_strong_vol = current_bar['volume'] > (avg_vol * volume_factor)
        
        trend_sma = current_bar[f'SMA_{trend_period}']
        is_uptrend = current_bar['close'] > trend_sma
        
        # Master Agent Logic
        signal = "HOLD"
        if is_bullish_crossover and is_strong_vol and is_uptrend:
            signal = "BUY"
        elif is_bearish_crossover and is_strong_vol and not is_uptrend:
            signal = "SELL"
        signals.append(signal)
    
    return ["HOLD"] * trend_period + signals

def run_bollinger_bands_strategy(historical_data, bb_length=20, bb_std=2.0):
    """
    Runs a Mean Reversion strategy based on Bollinger Bands.
    """
    df = historical_data.copy()
    
    # Calculate Bollinger Bands using pandas-ta
    df.ta.bbands(length=bb_length, std=bb_std, append=True)
    
    # The column names will be BBL_20_2.0 (lower), BBM_20_2.0 (middle), BBU_20_2.0 (upper)
    lower_band_col = f'BBL_{bb_length}_{bb_std}'
    upper_band_col = f'BBU_{bb_length}_{bb_std}'

    signals = []
    for i in range(bb_length, len(df)):
        current_bar = df.iloc[i]
        
        # Agent Logic
        signal = "HOLD"
        if current_bar['close'] < current_bar[lower_band_col]:
            signal = "BUY" # Price is oversold, expect it to revert up
        elif current_bar['close'] > current_bar[upper_band_col]:
            signal = "SELL" # Price is overbought, expect it to revert down
        signals.append(signal)
            
    return ["HOLD"] * bb_length + signals

def run_orb_strategy(historical_data, range_minutes=30):
    """
    Runs an Opening Range Breakout strategy.
    """
    df = historical_data.copy()
    signals = []
    
    # Group data by each unique day to process one day at a time
    daily_groups = df.groupby(df.index.date)
    
    for day, daily_data in daily_groups:
        daily_signals = ["HOLD"] * len(daily_data)
        
        if len(daily_data) > range_minutes:
            # Define the opening range time
            market_open_time = pd.to_datetime(f"{day} 09:15:00").tz_localize('Asia/Kolkata')
            range_end_time = market_open_time + pd.Timedelta(minutes=range_minutes)

            # Get the data for the opening range
            opening_range_data = daily_data.loc[market_open_time:range_end_time]
            
            if not opening_range_data.empty:
                # Find the high and low of the range
                range_high = opening_range_data['high'].max()
                range_low = opening_range_data['low'].min()
                
                trade_taken_today = False
                
                # Check for breakouts for the rest of the day
                for i in range(len(daily_data)):
                    current_bar = daily_data.iloc[i]
                    
                    if current_bar.name > range_end_time and not trade_taken_today:
                        # Check for Bullish Breakout
                        if current_bar['high'] > range_high:
                            daily_signals[i] = "BUY"
                            trade_taken_today = True # Take only the first signal of the day
                        # Check for Bearish Breakout
                        elif current_bar['low'] < range_low:
                            daily_signals[i] = "SELL"
                            trade_taken_today = True # Take only the first signal of the day
        
        signals.extend(daily_signals)
            
    return signals

def calculate_performance_with_exits(df_with_signals, starting_cash, brokerage, slippage, stop_loss_pct, take_profit_pct):
    df = df_with_signals.copy()
    cash = starting_cash
    shares = 0
    trades = []
    position_open = False
    stop_loss_price = 0
    take_profit_price = 0

    for i in range(len(df)):
        current_bar = df.iloc[i]
        signal = current_bar['signal']

        # First, check for exit conditions if we are in a position
        if position_open:
            # Check for Stop-Loss trigger
            if current_bar['low'] <= stop_loss_price:
                exit_price = stop_loss_price
                cash -= brokerage
                cash += shares * exit_price
                position_open = False
                profit = (exit_price - trades[-1]['entry_price']) * trades[-1]['shares']
                trades[-1].update({'exit_date': current_bar.name, 'exit_price': exit_price, 'profit': profit, 'exit_reason': 'STOP_LOSS'})
                continue # Move to the next bar
            
            # Check for Take-Profit trigger
            elif current_bar['high'] >= take_profit_price:
                exit_price = take_profit_price
                cash -= brokerage
                cash += shares * exit_price
                position_open = False
                profit = (exit_price - trades[-1]['entry_price']) * trades[-1]['shares']
                trades[-1].update({'exit_date': current_bar.name, 'exit_price': exit_price, 'profit': profit, 'exit_reason': 'TAKE_PROFIT'})
                continue # Move to the next bar

            # Check for opposite signal exit
            elif signal == "SELL":
                exit_price = current_bar['close'] * (1 - slippage)
                cash -= brokerage
                cash += shares * exit_price
                position_open = False
                profit = (exit_price - trades[-1]['entry_price']) * trades[-1]['shares']
                trades[-1].update({'exit_date': current_bar.name, 'exit_price': exit_price, 'profit': profit, 'exit_reason': 'OPPOSITE_SIGNAL'})
                continue # Move to the next bar

        # If we are not in a position, check for an entry signal
        if signal == "BUY" and not position_open:
            entry_price = current_bar['close'] * (1 + slippage)
            cash -= brokerage
            shares = cash / entry_price
            cash = 0
            position_open = True
            
            # Set our exit levels
            stop_loss_price = entry_price * (1 - stop_loss_pct)
            take_profit_price = entry_price * (1 + take_profit_pct)
            
            trades.append({'entry_date': current_bar.name, 'entry_price': entry_price, 'shares': shares})

    # If a position is still open at the very end, close it
    if position_open:
        last_price = df.iloc[-1]['close']
        cash += shares * last_price
        trades[-1].update({'exit_date': df.iloc[-1].name, 'exit_price': last_price, 'profit': (last_price - trades[-1]['entry_price']) * trades[-1]['shares'], 'exit_reason': 'END_OF_DATA'})
    
    return cash, pd.DataFrame(trades).dropna()