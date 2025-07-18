import yfinance as yf
import pandas as pd
from datetime import datetime
import numpy as np # Still needed for some pandas operations, though less critical


# Strategy Parameters (Very Basic)
SHORT_EMA_WINDOW = 10
LONG_EMA_WINDOW = 20
RSI_WINDOW = 14 # Standard RSI window
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9


def get_historical_data(symbol, days=90):
    """Fetch historical data."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    data = yf.download(symbol, start=start_date, end=end_date)
    if data.empty:
        print(f"No data for {symbol}. Check the symbol or internet connection.", flush=True)
        return None
    return data


def calculate_indicators(data):
    """Calculate EMA, RSI, and MACD (simplified)."""
    # EMA
    data["Short_EMA"] = data["Close"].ewm(span=SHORT_EMA_WINDOW, adjust=False).mean()
    data["Long_EMA"] = data["Close"].ewm(span=LONG_EMA_WINDOW, adjust=False).mean()

    # RSI
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    # Using .fillna(0) to handle potential division by zero for initial periods
    avg_gain = gain.ewm(alpha=1 / RSI_WINDOW, adjust=False).mean().fillna(0)
    avg_loss = loss.ewm(alpha=1 / RSI_WINDOW, adjust=False).mean().fillna(0)
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs)).fillna(0) # Fillna 0 to avoid NaN from division by zero

    # MACD
    data["MACD_Fast"] = data["Close"].ewm(span=MACD_FAST, adjust=False).mean()
    data["MACD_Slow"] = data["Close"].ewm(span=MACD_SLOW, adjust=False).mean()
    data["MACD_Line"] = data["MACD_Fast"] - data["MACD_Slow"]
    data["MACD_Signal"] = data["MACD_Line"].ewm(span=MACD_SIGNAL, adjust=False).mean()

    # Drop intermediate columns if desired to save memory
    data = data.drop(columns=["MACD_Fast", "MACD_Slow"], errors='ignore')

    return data


def get_current_price(symbol):
    """Fetch the current price."""
    ticker = yf.Ticker(symbol)
    history = ticker.history(period="1d")
    if history.empty:
        print(f"No current price for {symbol}.", flush=True)
        return None
    return history["Close"].iloc[-1]


def make_decision(data):
    """Make a very basic trading decision based on EMA crossover and RSI/MACD."""
    # Ensure there's enough data for the latest calculations
    if data.empty or len(data) < max(SHORT_EMA_WINDOW, LONG_EMA_WINDOW, RSI_WINDOW, MACD_SLOW, MACD_SIGNAL):
        return "Not enough data to make a decision."

    latest_short_ema = data["Short_EMA"].iloc[-1]
    latest_long_ema = data["Long_EMA"].iloc[-1]
    latest_rsi = data["RSI"].iloc[-1]
    latest_macd_line = data["MACD_Line"].iloc[-1]
    latest_macd_signal = data["MACD_Signal"].iloc[-1]

    # Buy condition: Short EMA above Long EMA AND RSI not overbought AND MACD Line above Signal
    if (latest_short_ema > latest_long_ema and
        latest_rsi < RSI_OVERBOUGHT and
        latest_macd_line > latest_macd_signal):
        return "Buy"
    # Sell condition: Short EMA below Long EMA AND RSI not oversold AND MACD Line below Signal
    elif (latest_short_ema < latest_long_ema and
          latest_rsi > RSI_OVERSOLD and
          latest_macd_line < latest_macd_signal):
        return "Sell"
    else:
        return "Hold"


if __name__ == "__main__":
    try:
        print("Starting the basic trading decision bot...", flush=True)

        symbols_input = input("Enter stock symbols separated by commas (e.g., AAPL,MSFT): ").strip().upper()
        symbols = [s.strip() for s in symbols_input.split(",") if s.strip()]

        if not symbols:
            print("No symbols entered. Exiting.", flush=True)
            exit()

        for symbol in symbols:
            print(f"\nAnalyzing {symbol}...", flush=True)

            data = get_historical_data(symbol)
            if data is None or data.empty:
                print(f"Could not retrieve historical data for {symbol}. Skipping.", flush=True)
                continue

            data = calculate_indicators(data)

            # Check for NaN values after indicator calculation, especially at the start
            if data.isnull().values.any():
                # Filter out rows with NaN in the columns we care about for decision making
                data_for_decision = data.dropna(subset=["Short_EMA", "Long_EMA", "RSI", "MACD_Line", "MACD_Signal"])
                if data_for_decision.empty:
                    print(f"Insufficient valid data after indicator calculation for {symbol}. Skipping.", flush=True)
                    continue
                # If only some rows are NaN, use the latest valid ones
                data = data_for_decision


            current_price = get_current_price(symbol)
            if current_price is None:
                continue

            decision = make_decision(data) # Simplified decision function

            print("\n--- Analysis Summary ---")
            print(f"Symbol: {symbol}")
            print(f"Current Price: {current_price:.2f}")

            # Print latest indicator values if available
            if not data.empty and not data["Short_EMA"].iloc[-1] is np.nan:
                print(f"Short EMA ({SHORT_EMA_WINDOW} days): {data['Short_EMA'].iloc[-1]:.2f}")
                print(f"Long EMA ({LONG_EMA_WINDOW} days): {data['Long_EMA'].iloc[-1]:.2f}")
                print(f"RSI ({RSI_WINDOW} days): {data['RSI'].iloc[-1]:.2f}")
                print(f"MACD Line: {data['MACD_Line'].iloc[-1]:.2f}")
                print(f"MACD Signal: {data['MACD_Signal'].iloc[-1]:.2f}")
            else:
                print("Indicator values not available due to insufficient data.")

            print(f"\nTrading Decision for {symbol}: {decision}")
            print("-" * 30)

        print("\nThe basic trading decision script has completed successfully.", flush=True)

    except Exception as e:
        print(f"An error occurred: {e}", flush=True)
