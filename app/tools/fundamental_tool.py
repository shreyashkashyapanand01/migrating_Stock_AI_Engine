import logging
import yfinance as yf
from app.tools.market_data_tool import get_stock_name

logger = logging.getLogger(__name__)

def fetch_fundamental_data(symbol: str):
    logger.info(f"fundamental_tool: Fetching fundamental data for {symbol}...")

    try:
        symbol = get_stock_name(symbol) #edited
        if not symbol.endswith(".NS"):
            symbol = symbol + ".NS"

        ticker = yf.Ticker(symbol)

        info = ticker.info

        fundamentals = {
            "pe_ratio": info.get("trailingPE"),
            "revenue_growth": info.get("revenueGrowth"),
            "profit_margin": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity")
        }

        logger.info(f"fundamental_tool: Successfully fetched data for {symbol}")
        return fundamentals

    except Exception:
        logger.error(f"Error in fundamental_tool.py at fetch_fundamental_data: Could not retrieve info for {symbol}")
        return {
            "pe_ratio": None,
            "revenue_growth": None,
            "profit_margin": None,
            "debt_to_equity": None
        }