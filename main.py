
import yfinance as yf
import pandas as pd
from datetime import datetime
import numpy as np


short_ema_len = 10
long_ema_len = 20
rsi_period = 14
rsi_high_bound = 70
rsi_low_bound = 30
macd_fast_len = 12
macd_slow_len = 26
macd_sig_len = 9


def grab_stock_hist(tick, num_days=90):
    end_dt = datetime.now().strftime("%Y-%m-%d")
    start_dt = (datetime.now() - pd.Timedelta(days=num_days)).strftime("%Y-%m-%d")
    data_raw = yf.download(tick, start=start_dt, end=end_dt)
    if data_raw.empty:
        print(f"No data for {tick}.")
        return None
    return data_raw

def calc_all_stuff(data_in):
    data_in["S_EMA"] = data_in["Close"].ewm(span=short_ema_len, adjust=False).mean()
    data_in["L_EMA"] = data_in["Close"].ewm(span=long_ema_len, adjust=False).mean()

    chg = data_in["Close"].diff()
    up = chg.where(chg > 0, 0)
    down = -chg.where(chg < 0, 0)

    avg_up = up.ewm(alpha=1 / rsi_period, adjust=False).mean().fillna(0)
    avg_down = down.ewm(alpha=1 / rsi_period, adjust=False).mean().fillna(0)
    rs_val = avg_up / avg_down
    data_in["RSI_val"] = 100 - (100 / (1 + rs_val)).fillna(0)

    data_in["MACD_F"] = data_in["Close"].ewm(span=macd_fast_len, adjust=False).mean()
    data_in["MACD_S"] = data_in["Close"].ewm(span=macd_slow_len, adjust=False).mean()
    data_in["MACD_Line_val"] = data_in["MACD_F"] - data_in["MACD_S"]
    data_in["MACD_Signal_val"] = data_in["MACD_Line_val"].ewm(span=macd_sig_len, adjust=False).mean()

    return data_in

def get_live_price(ticker_sym):
    t = yf.Ticker(ticker_sym)
    hist_1d = t.history(period="1d")
    if hist_1d.empty:
        print(f"No current price for {ticker_sym}.")
        return None
    return hist_1d["Close"].iloc[-1]

def make_the_call(data_processed):
    if data_processed.empty:
        return "Not enough data."

    s_ema_curr = data_processed["S_EMA"].iloc[-1]
    l_ema_curr = data_processed["L_EMA"].iloc[-1]
    rsi_curr = data_processed["RSI_val"].iloc[-1]
    macd_line_curr = data_processed["MACD_Line_val"].iloc[-1]
    macd_sig_curr = data_processed["MACD_Signal_val"].iloc[-1]

    if (s_ema_curr > l_ema_curr and
        rsi_curr < rsi_high_bound and
        macd_line_curr > macd_sig_curr):
        return "BUY"
    elif (s_ema_curr < l_ema_curr and
          rsi_curr > rsi_low_bound and
          macd_line_curr < macd_sig_curr):
        return "SELL"
    else:
        return "HOLD"


if __name__ == "__main__":
    print("Starting stock analysis program.")

    user_syms = input("Enter stock symbols (e.g., MSFT, GOOG): ").strip().upper()
    sym_list = [s.strip() for s in user_syms.split(",") if s.strip()]

    if not sym_list:
        print("No symbols, quitting.")
        exit()

    for sym in sym_list:
        print(f"\n--- Analyzing {sym} ---")

        df = grab_stock_hist(sym)
        if df is None:
            continue

        df = calc_all_stuff(df)

        if df.isnull().values.any():
            df = df.dropna()
            if df.empty:
                print(f"Skipping {sym} due to too many NaNs.")
                continue

        curr_p = get_live_price(sym)
        if curr_p is None:
            continue

        trade_decision = make_the_call(df)


        print(f"\nSymbol: {sym}")
        print(f"Current Price: {curr_p:.2f}")

        if not df.empty:
            print("Indicators:")
            print(f"  Short EMA: {df['S_EMA'].iloc[-1]:.2f}")
            print(f"  Long EMA: {df['L_EMA'].iloc[-1]:.2f}")
            print(f"  RSI: {df['RSI_val'].iloc[-1]:.2f}")
            print(f"  MACD Line: {df['MACD_Line_val'].iloc[-1]:.2f}")
            print(f"  MACD Signal: {df['MACD_Signal_val'].iloc[-1]:.2f}")
        else:
            print("Indicator data missing for analysis.")

        print(f"\nDecision for {sym}: {trade_decision}\n")
        print("-" * 25)

    print("\nAll done.")
