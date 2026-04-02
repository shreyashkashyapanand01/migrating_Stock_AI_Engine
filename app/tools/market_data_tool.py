import logging
import yfinance as yf
from dotenv import load_dotenv
import os
from groq import Groq
from tavily import TavilyClient
from app.config import llm_model

load_dotenv()

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def get_stock_name(stock: str) -> str:
    logger.info(f"market_data_tool: Resolving ticker for '{stock}'")

    # Step 1: Web search for real ticker context
    try:
        search_result = tavily.search(
            query=f"{stock} NSE ticker symbol Yahoo Finance",
            search_depth="basic",
            max_results=3,
            include_domains=[
                "finance.yahoo.com",
                "moneycontrol.com",
                "nseindia.com",
                "screener.in",
                "tickertape.in"
            ]
        )
        snippets = " ".join(
            r.get("content", "") for r in search_result.get("results", [])
        )
    except Exception as e:
        logger.warning(f"market_data_tool: Tavily search failed for '{stock}' - {e}")
        snippets = ""

    # Step 2: Original Groq LLM extracts clean ticker from search context
    system_prompt = """
    You are a financial ticker mapping assistant. 
    Return ONLY the Yahoo Finance ticker symbol.
    - Indian NSE stocks: Append .NS (e.g., RELIANCE.NS, HDFCBANK.NS, VEDL.NS)
    - NEVER return US ADR tickers for Indian stocks (e.g., HDB, IBN, WIT are WRONG)
    - Priority: Indian NSE listing.
    - Format: ONLY the ticker. No prose, no bolding.
    """

    user_content = (
        f"Stock name: {stock}\n"
        f"Web search context: {snippets[:1000] if snippets else 'No context available'}\n\n"
        f"Return the Yahoo Finance ticker symbol for '{stock}'."
    )

    try:
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0
        )
        ticker = response.choices[0].message.content.strip()
        logger.info(f"market_data_tool: Resolved '{stock}' -> '{ticker}'")
        return ticker
    except Exception:
        logger.error(f"Error in market_data_tool.py at get_stock_name: Failed to map ticker for {stock}")
        return stock


def fetch_price_history(symbol: str):
    logger.info(f"market_data_tool: Fetching price history for {symbol}")
    try:
        symbol = get_stock_name(symbol)

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
        symbol = get_stock_name(symbol)

        ticker = yf.Ticker(symbol)
        price_df = ticker.history(period="1d")

        if price_df.empty:
            raise ValueError("Empty price data")

        price = price_df["Close"].iloc[-1]
        return float(price)
    except Exception:
        logger.error(f"Error in market_data_tool.py at fetch_latest_price: Could not get latest price for {symbol}")
        return 0.0


# import logging
# import yfinance as yf
# from dotenv import load_dotenv
# import os
# from groq import Groq
# from tavily import TavilyClient
# from app.config import llm_model

# load_dotenv()

# logger = logging.getLogger(__name__)
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# def get_stock_name(stock: str) -> str:
#     logger.info(f"market_data_tool: Resolving ticker for '{stock}'")

#     # Skip resolution if already a valid Yahoo Finance ticker
#     if stock.endswith(".NS") or stock.endswith(".BO") or "." in stock:
#         logger.info(f"market_data_tool: '{stock}' already resolved, skipping")
#         return stock

#     # Step 1: Web search for real ticker context
#     try:
#         search_result = tavily.search(
#             query=f"{stock} NSE ticker symbol Yahoo Finance",
#             search_depth="basic",
#             max_results=3,
#             include_domains=[
#                 "finance.yahoo.com",
#                 "moneycontrol.com",
#                 "nseindia.com",
#                 "screener.in",
#                 "tickertape.in"
#             ]
#         )
#         snippets = " ".join(
#             r.get("content", "") for r in search_result.get("results", [])
#         )
#     except Exception as e:
#         logger.warning(f"market_data_tool: Tavily search failed for '{stock}' - {e}")
#         snippets = ""

#     # Step 2: Groq LLM extracts clean ticker from search context
#     system_prompt = """
#     You are a financial ticker mapping assistant. 
#     Return ONLY the Yahoo Finance ticker symbol.
#     - Indian NSE stocks: Append .NS (e.g., RELIANCE.NS, HDFCBANK.NS, VEDL.NS)
#     - US stocks: Primary ticker (e.g., AAPL)
#     - Priority: Indian NSE listing.
#     - Format: ONLY the ticker. No prose, no bolding.
#     """

#     user_content = (
#         f"Stock name: {stock}\n"
#         f"Web search context: {snippets[:1000] if snippets else 'No context available'}\n\n"
#         f"Return the Yahoo Finance ticker symbol for '{stock}'."
#     )

#     try:
#         response = client.chat.completions.create(
#             model=llm_model,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user",   "content": user_content}
#             ],
#             temperature=0
#         )
#         ticker = response.choices[0].message.content.strip()
#         logger.info(f"market_data_tool: Resolved '{stock}' -> '{ticker}'")
#         return ticker
#     except Exception:
#         logger.error(f"market_data_tool: Failed to map ticker for '{stock}'")
#         return stock


# def fetch_price_history(symbol: str):
#     logger.info(f"market_data_tool: Fetching price history for {symbol}")
#     try:
#         # Only resolve if not already a Yahoo Finance ticker
#         if not symbol.endswith(".NS") and "." not in symbol:
#             symbol = get_stock_name(symbol)

#         if not symbol.endswith(".NS"):
#             symbol = symbol + ".NS"

#         ticker = yf.Ticker(symbol)
#         df = ticker.history(period="6mo")

#         if df.empty:
#             logger.warning(f"market_data_tool: No history found for {symbol}")

#         return df
#     except Exception:
#         logger.error(f"market_data_tool: Failed to fetch price history for {symbol}")
#         import pandas as pd
#         return pd.DataFrame()


# def fetch_latest_price(symbol: str) -> float:
#     try:
#         # Only resolve if not already a Yahoo Finance ticker
#         if not symbol.endswith(".NS") and "." not in symbol:
#             symbol = get_stock_name(symbol)

#         if not symbol.endswith(".NS"):
#             symbol = symbol + ".NS"

#         ticker   = yf.Ticker(symbol)
#         price_df = ticker.history(period="1d")

#         if price_df.empty:
#             raise ValueError("Empty price data")

#         price = price_df["Close"].iloc[-1]
#         return float(price)
#     except Exception:
#         logger.error(f"market_data_tool: Could not get latest price for {symbol}")
#         return 0.0