import yfinance as yf
import pandas as pd
import pandas_ta as ta

def fetch_data(symbol: str, interval: str, period: str = "5d") -> pd.DataFrame:
    """
    Fetches historical market data from yfinance and cleans the MultiIndex.
    """
    df = yf.download(symbol, interval=interval, period=period, progress=False)
    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel('Ticker')

    # Drop rows with NaN values if any
    df.dropna(inplace=True)
    return df

def apply_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies SMA 7, SMA 30, RSI, and Bollinger Bands using pandas_ta.
    """
    if df.empty or len(df) < 30:
        return df

    # SMA 7 and SMA 30
    df.ta.sma(length=7, append=True)
    df.ta.sma(length=30, append=True)

    # RSI (default length 14)
    df.ta.rsi(length=14, append=True)

    # Bollinger Bands
    df.ta.bbands(append=True)

    return df

def generate_signals(df: pd.DataFrame) -> str:
    """
    Determines the trading signal based on the latest candle.
    Signal conditions:
    - BUY: RSI < 35 AND SMA 7 > SMA 30 (Golden Cross)
    - SELL: RSI > 70 AND SMA 7 < SMA 30 (Death Cross)
    - Strong Buy: Price <= Lower BB AND Golden Cross imminent (SMA 7 crosses SMA 30 or is close)
    """
    if df.empty or len(df) < 2:
        return "NEUTRAL"

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Extract indicator column names dynamically
    sma7_col = [col for col in df.columns if 'SMA_7' in col][0]
    sma30_col = [col for col in df.columns if 'SMA_30' in col][0]
    rsi_col = [col for col in df.columns if 'RSI' in col][0]
    bbl_col = [col for col in df.columns if 'BBL' in col][0]  # Lower Bollinger Band

    rsi = latest[rsi_col]
    sma7 = latest[sma7_col]
    sma30 = latest[sma30_col]
    close = latest['Close']
    bbl = latest[bbl_col]

    prev_sma7 = prev[sma7_col]
    prev_sma30 = prev[sma30_col]

    golden_cross = sma7 > sma30 and prev_sma7 <= prev_sma30
    death_cross = sma7 < sma30 and prev_sma7 >= prev_sma30

    golden_cross_imminent = (sma30 - sma7) > 0 and (sma30 - sma7) < (prev_sma30 - prev_sma7) # narrowing gap

    if close <= bbl and (golden_cross or golden_cross_imminent):
        return "STRONG BUY"

    if rsi < 35 and sma7 > sma30:
        return "BUY"

    if rsi > 70 and sma7 < sma30:
        return "SELL"

    return "NEUTRAL"

def get_latest_price(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    return float(df.iloc[-1]['Close'])
