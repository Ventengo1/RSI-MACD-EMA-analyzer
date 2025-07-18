import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from scipy.signal import argrelextrema

# super basic fetcher

def get_data(symb, days=300):
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
        df = yf.download(symb, start=start, end=end)
        if df.empty:
            return None
        return df
    except:
        return None


def indicators(df):
    df['ema_s'] = df['Close'].ewm(span=13).mean()
    df['ema_l'] = df['Close'].ewm(span=34).mean()

    delta = df['Close'].diff()
    up = delta.where(delta > 0, 0)
    down = -delta.where(delta < 0, 0)
    rs = up.ewm(span=5).mean() / down.ewm(span=5).mean()
    df['rsi'] = 100 - (100 / (1 + rs))

    macd_f = df['Close'].ewm(span=12).mean()
    macd_s = df['Close'].ewm(span=26).mean()
    df['macd'] = macd_f - macd_s
    df['macd_sig'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_sig']

    # just use rolling std for vol approximation
    df['vol'] = df['Close'].rolling(10).std()
    df['bb_up'] = df['Close'].rolling(10).mean() + 1.5 * df['vol']
    df['bb_dn'] = df['Close'].rolling(10).mean() - 1.5 * df['vol']

    return df


def trend(df):
    out = []
    for i in range(15, len(df)):
        y = df['Close'].iloc[i-15:i].values
        x = np.arange(15).reshape(-1, 1)
        try:
            m = LinearRegression().fit(x, y)
            out.append((df.index[i], m.coef_[0]))
        except:
            out.append((df.index[i], 0))
    return out


def extremes(df):
    hi = argrelextrema(df['Close'].values, np.greater, order=5)[0]
    lo = argrelextrema(df['Close'].values, np.less, order=5)[0]
    return df.iloc[hi], df.iloc[lo]


def latest_price(t):
    h = yf.Ticker(t).history(period="1d")
    if not h.empty:
        return h['Close'].iloc[-1]
    return None


if __name__ == '__main__':
    syms = input("Symbols? ").upper().split(',')
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

        trends = trend(df)
        pks, trs = extremes(df)
        px = latest_price(s)
        if px is None:
            print("No current price")
            continue

        last = df.iloc[-1]
        slope = trends[-1][1] if trends else 0

        near_top = False
        near_bot = False
        for t in pks.index[-3:]:
            if (df.index[-1] - t).days <= 5:
                near_top = True
        for b in trs.index[-3:]:
            if (df.index[-1] - b).days <= 5:
                near_bot = True

        print(f"Price: {px:.2f}")
        print(f"Short EMA: {last['ema_s']:.2f}  Long EMA: {last['ema_l']:.2f}")
        print(f"RSI: {last['rsi']:.2f}")
        print(f"MACD: {last['macd']:.2f}  Signal: {last['macd_sig']:.2f}")
        print(f"Trend: {slope:.4f}")

        # slightly looser rules
        action = "Hold"
        if px > last['ema_s'] and last['rsi'] < 80 and last['macd'] > last['macd_sig']:
            if not near_top:
                action = "Buy"
        elif px < last['ema_l'] and last['rsi'] > 20 and last['macd'] < last['macd_sig']:
            action = "Sell" if not near_bot else "Maybe sell"

        print(f"Decision: {action}")
