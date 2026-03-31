import logging
from langchain_core.tools import tool
from app.tools.indicator_tool import (
    calculate_trend,
    calculate_momentum,
    calculate_rsi,
    classify_rsi,
    calculate_volatility
)
from app.tools.market_data_tool import fetch_price_history
from app.tools.news_tool import fetch_news
from app.tools.fundamental_tool import fetch_fundamental_data

logger = logging.getLogger(__name__)


@tool
def get_technical_indicators(symbol: str) -> dict:
    """Fetch price history and calculate technical indicators for a stock symbol.
    Returns trend, momentum, RSI state, and volatility."""

    logger.info(f"stock_tools: Fetching technical indicators for {symbol}")

    try:
        df = fetch_price_history(symbol)

        if df.empty:
            return {"error": "No market data found for this symbol"}

        trend      = calculate_trend(df)
        momentum   = calculate_momentum(df)
        rsi_value  = calculate_rsi(df)
        rsi_state  = classify_rsi(rsi_value)
        volatility = calculate_volatility(df)

        return {
            "trend":      trend,
            "momentum":   momentum,
            "rsi":        rsi_state,
            "volatility": volatility
        }
    except Exception as e:
        logger.error(f"stock_tools: Technical indicators failed for {symbol} - {e}")
        return {"error": "Technical calculation failure"}


@tool
def get_news_headlines(symbol: str) -> dict:
    """Search the web for the latest financial news about a stock symbol
    from trusted Indian and global financial sources.
    Returns a list of headline strings with brief snippets."""

    logger.info(f"stock_tools: Searching web news for {symbol}")

    try:
        headlines = fetch_news(symbol)
        return {"headlines": headlines}
    except Exception as e:
        logger.error(f"stock_tools: News search failed for {symbol} - {e}")
        return {"headlines": [], "error": "Failed to fetch news"}


@tool
def get_fundamental_data(symbol: str) -> dict:
    """Fetch fundamental financial data for a stock symbol.
    Returns PE ratio, revenue growth, profit margin, and debt to equity."""

    logger.info(f"stock_tools: Fetching fundamental data for {symbol}")

    try:
        return fetch_fundamental_data(symbol)
    except Exception as e:
        logger.error(f"stock_tools: Fundamental data failed for {symbol} - {e}")
        return {
            "pe_ratio":        None,
            "revenue_growth":  None,
            "profit_margin":   None,
            "debt_to_equity":  None
        }