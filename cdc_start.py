import ccxt
import pandas as pd
from ta.trend import EMA
import subprocess
import time
from datetime import datetime, timedelta

# Set up exchange connection
exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET_KEY',
})

# Define trading parameters
base_currency = 'USDT'
quote_currency = 'BTC'
buy_amount = 50

# Get list of all symbols available on Binance
symbol_list = exchange.load_markets()
symbols = list(symbol_list.keys())

# Create an empty DataFrame to store the results
results_df = pd.DataFrame(columns=['symbol', 'fast_ema', 'slow_ema'])

while True:
    # Wait until 7:00 AM
    now = datetime.now()
    next_run_time = datetime(now.year, now.month, now.day, hour=7, minute=0, second=0)
    if now >= next_run_time:
        next_run_time += timedelta(days=1)
    wait_time = (next_run_time - now).total_seconds()
    time.sleep(wait_time)

    # Loop over all symbols and check EMA indicators
    for symbol in symbols:
        # Skip symbols that don't have the quote currency as the base currency
        if not symbol.endswith(base_currency):
            continue
            
        # Define crypto symbol and time period
        timeframe = '1d'
        limit = 100
        
        # Load historical crypto data
        crypto_data = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        crypto_df = pd.DataFrame(crypto_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        crypto_df['timestamp'] = pd.to_datetime(crypto_df['timestamp'], unit='ms')
        crypto_df.set_index('timestamp', inplace=True)

        # Calculate EMA indicators
        fast_ema = EMA(crypto_df['close'], window=12)
        slow_ema = EMA(crypto_df['close'], window=26)

        # Check if fast EMA is above slow EMA
        if fast_ema.iloc[-1] > slow_ema.iloc[-1]:
            # Add symbol and EMA values to DataFrame
            results_df = results_df.append({'symbol': symbol, 'fast_ema': fast_ema.iloc[-1], 'slow_ema': slow_ema.iloc[-1]}, ignore_index=True)

    # Filter DataFrame to show only symbols with fast EMA above slow EMA
    results_df = results_df[results_df['fast_ema'] > results_df['slow_ema']]
    print(results_df.to_string(index=False))

    # Export results to Excel file
    results_df.to_excel('ema_results.xlsx', index=False)

    # Send first column of results_df to a Telegram chat
    subprocess.run(['telegram-send', results_df.iloc[:, 0].to_string(index=False)])
    
    # Clear results DataFrame
    results_df = pd.DataFrame(columns=['symbol', 'fast_ema', 'slow_ema'])
