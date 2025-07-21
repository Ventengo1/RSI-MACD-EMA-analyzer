# /// script
# dependencies = [
#   "yfinance",
#   "pandas",
#   "numpy",
#   "scikit-learn",
#   "scipy",
# ]
# python = "3.9" # This version will match what you specified with 'uv init --script'
# ///
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from scipy.signal import argrelextrema

#Worked on troubleshooting errors with the dataframes and the columns. Spent a lot of the time torubleshooting but now finally getting it to work.


short_ema_len = 10
long_ema_len = 20
rsi_period = 14
rsi_high_bound = 70
rsi_low_bound = 30
macd_fast_len = 12
macd_slow_len = 26
macd_sig_len = 9


def get_data(symb, days=300):
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
        df = yf.download(symb, start=start, end=end)
        if df.empty:
            return None
        return df
    except Exception:
        return None


def indicators(df):
    df['ema_s'] = df['Close'].ewm(span=13, adjust=False).mean()
    df['ema_l'] = df['Close'].ewm(span=34, adjust=False).mean()

    delta = df['Close'].diff()
    up = delta.where(delta > 0, 0)
    down = -delta.where(delta < 0, 0)

    avg_up = up.ewm(span=5, adjust=False).mean().fillna(0)
    avg_down = down.ewm(span=5, adjust=False).mean().fillna(0)

    rs = np.divide(avg_up, avg_down, out=np.zeros_like(avg_up), where=avg_down!=0)
    rs = rs.fillna(0)

    df['rsi'] = 100 - (100 / (1 + rs))

    macd_f = df['Close'].ewm(span=12, adjust=False).mean()
    macd_s = df['Close'].ewm(span=26, adjust=False).mean()
    df['macd'] = macd_f - macd_s
    df['macd_sig'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_sig']

    # Calculate Bollinger Bands correctly
    df['vol'] = df['Close'].rolling(window=10).std()
    df['bb_mid'] = df['Close'].rolling(window=10).mean()
    df['bb_up'] = df['bb_mid'] + 1.5 * df['vol']
    df['bb_dn'] = df['bb_mid'] - 1.5 * df['vol']


    return df


def trend(df):
    out = []
    if len(df) < 15:
        return out

    for i in range(15, len(df)):
        y = df['Close'].iloc[i-15:i].values
        x = np.arange(15).reshape(-1, 1)
        try:
            m = LinearRegression().fit(x, y)
            out.append((df.index[i], m.coef_[0]))
        except (ValueError, Exception):
            out.append((df.index[i], 0))
    return out


def extremes(df):
    if len(df) < 11:
        return pd.DataFrame(), pd.DataFrame()

    hi = argrelextrema(df['Close'].values, np.greater, order=5)[0]
    lo = argrelextrema(df['Close'].values, np.less, order=5)[0]
    return df.iloc[hi], df.iloc[lo]


def latest_price(t):
    h = yf.Ticker(t).history(period="1d")
    if not h.empty:
        return h['Close'].iloc[-1]
    return None


if __name__ == '__main__':
    syms = input("Symbols: ").upper().split(',')
    for s in syms:
        s = s.strip()
        print(f"\nChecking {s}")
        df = get_data(s)
        if df is None:
            print("No data")
            continue

        df = indicators(df)
        df = df.dropna()
        if df.empty:
            print("Empty after indicators")
            continue

        trends_data = trend(df) # Renamed to avoid conflict with 'trends' variable in print
        pks, trs = extremes(df)
        px = latest_price(s)
        if px is None:
            print("No current price")
            continue

        if df.empty: # This check is redundant if the previous df.dropna() and empty check were thorough
            print(f"Not enough data for {s} after indicator calculation to get last row.")
            continue

        last = df.iloc[-1]
        slope = trends_data[-1][1] if trends_data else 0 # Use trends_data

        near_top = False
        near_bot = False

        if not pks.empty:
            for t_idx in pks.index[-3:]:
                if (df.index[-1].to_pydatetime() - t_idx.to_pydatetime()).days <= 5:
                    near_top = True
                    break

        if not trs.empty:
            for b_idx in trs.index[-3:]:
                if (df.index[-1].to_pydatetime() - b_idx.to_pydatetime()).days <= 5:
                    near_bot = True
                    break

        print(f"Price: {px:.2f}")
        # Use .item() to extract scalar value from Series to avoid FutureWarning
        print(f"Short EMA: {last['ema_s'].item():.2f}   Long EMA: {last['ema_l'].item():.2f}")
        print(f"RSI: {last['rsi'].item():.2f}")
        print(f"MACD: {last['macd'].item():.2f}   Signal: {last['macd_sig'].item():.2f}")


        action = "Hold"
        if px > last['ema_s'].item() and last['rsi'].item() < 80 and last['macd'].item() > last['macd_sig'].item():
            if not near_top:
                action = "Buy"
        elif px < last['ema_l'].item() and last['rsi'].item() > 20 and last['macd'].item() < last['macd_sig'].item():
            action = "Sell" if not near_bot else "Maybe sell"

        print(f"Decision: {action}")
