import logging
import yfinance as yf
from dotenv import load_dotenv
import os
from groq import Groq

from app.config import llm_model

load_dotenv()

logger = logging.getLogger(__name__)
llm = client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_stock_name(stock):
    
    system_prompt = """
    You are a financial ticker mapping assistant. 
    Return ONLY the Yahoo Finance ticker symbol.
    - Indian NSE stocks: Append .NS (e.g., RELIANCE.NS)
    - US stocks: Primary ticker (e.g., AAPL)
    - Priority: Indian NSE listing.
    - Format: ONLY the ticker. No prose, no bolding.
    """
    try:
        response = client.chat.completions.create(
            # model="llama-3.1-8b-instant",
            model = llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": stock} 
            ],
            temperature=0 
        )
        ticker = response.choices[0].message.content.strip()
        return ticker
    except Exception:
        logger.error(f"Error in market_data_tool.py at get_stock_name: Failed to map ticker for {stock}")
        return stock


def fetch_price_history(symbol: str):

    logger.info(f"market_data_tool: Fetching price history for {symbol}")
    try:
        symbol = get_stock_name(symbol) # edited now
        
        if not symbol.endswith(".NS"):
            symbol = symbol + ".NS"
        ticker = yf.Ticker(symbol)

        df = ticker.history(period="6mo")
        
        if df.empty:
            logger.warning(f"market_data_tool: No history found for {symbol}")
            
        return df
    except Exception:
        logger.error(f"Error in market_data_tool.py at fetch_price_history: Failed to download data for {symbol}")
        import pandas as pd
        return pd.DataFrame()

def fetch_latest_price(symbol: str):

    try:
        symbol = get_stock_name(symbol) #edited now
        
        ticker = yf.Ticker(symbol)

        price_df = ticker.history(period="1d")
        if price_df.empty:
            raise ValueError("Empty price data")
            
        price = price_df["Close"].iloc[-1]

        return float(price)
    except Exception:
        logger.error(f"Error in market_data_tool.py at fetch_latest_price: Could not get latest price for {symbol}")
        return 0.0