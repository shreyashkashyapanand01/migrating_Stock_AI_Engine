import pandas as pd
import logging

logger = logging.getLogger(__name__)

def calculate_trend(df):
    try:
        short_ma = df["Close"].rolling(window=20).mean()
        long_ma = df["Close"].rolling(window=50).mean()

        if short_ma.iloc[-1] > long_ma.iloc[-1]:
            return "bullish"
        else:
            return "bearish"
    except Exception:
        logger.error("Error in indicator_tool.py at calculate_trend: Failed to calculate Moving Averages")
        return "unknown"


def calculate_momentum(df):
    try:
        momentum = df["Close"].pct_change().rolling(10).mean().iloc[-1]

        if momentum > 0.01:
            return "strong"
        elif momentum > 0:
            return "moderate"
        else:
            return "weak"
    except Exception:
        logger.error("Error in indicator_tool.py at calculate_momentum: Failed to calculate pct_change")
        return "unknown"


def calculate_rsi(df, window=14):
    try:
        delta = df["Close"].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()

        # Avoid division by zero
        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]
    except Exception:
        logger.error("Error in indicator_tool.py at calculate_rsi: Failed to calculate RSI value")
        return 50.0 # Return neutral


def classify_rsi(rsi):
    if rsi > 70:
        return "overbought"
    elif rsi < 30:
        return "oversold"
    else:
        return "neutral"


def calculate_volatility(df):
    try:
        volatility = df["Close"].pct_change().std()

        if volatility < 0.01:
            return "low"
        elif volatility < 0.02:
            return "medium"
        else:
            return "high"
    except Exception:
        logger.error("Error in indicator_tool.py at calculate_volatility: Failed to calculate standard deviation")
        return "unknown"